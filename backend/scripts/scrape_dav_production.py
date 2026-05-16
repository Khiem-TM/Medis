#!/usr/bin/env python3
"""
Production DAV drug scraper — Medis platform.

Pipeline (4 phases):
  1. SCRAPE   — Paginate DAV API, target all 572 DDI drugs + fill to TARGET_TOTAL
  2. IMAGE    — Acquire product images: pharmacy lookup → category fallback → Cloudinary upload
  3. MAP      — Fuzzy-match product ingredients → DDI drug IDs
  4. UPSERT   — Write to PostgreSQL (market_drug_products + market_drug_product_ingredients)

Usage:
  cd backend
  CLOUDINARY_CLOUD_NAME=your_cloud python scripts/scrape_dav_production.py

  # Resume after interruption (reads checkpoint.json):
  CLOUDINARY_CLOUD_NAME=your_cloud python scripts/scrape_dav_production.py --resume

  # Dry run (no DB writes, no Cloudinary uploads):
  python scripts/scrape_dav_production.py --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import defaultdict

import httpx

# ── Path setup ──────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models.drug import Drug
from app.models.market_drug import MarketDrugProduct, MarketDrugProductIngredient

# ── Configuration ────────────────────────────────────────────────────────────
DAV_API_URL = "https://dichvucong.dav.gov.vn/api/services/app/soDangKy/GetAllPublicServerPaging"
DDI_DB_PATH = BACKEND_DIR.parent / "ddi_mvp" / "event.db"
CHECKPOINT_PATH = BACKEND_DIR / "scripts" / "scrape_checkpoint.json"

# Cloudinary — get cloud name from: https://cloudinary.com/console
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "dfzokytpi")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "925338521972236")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "iAdvKoiDm56XVujZeDiPix0R_IA")

# Scraping targets
TARGET_TOTAL = 2000          # desired market_drug_products count
DAV_PAGE_SIZE = 100          # records per DAV request
DAV_MAX_PER_DDI_TERM = 10   # max DAV results per DDI drug name search
DAV_RATE_LIMIT_SEC = 0.6     # seconds between requests

# Pharmacy image search
PHARMACY_SEARCH_URL = "https://api.nhathuoclongchau.com.vn/lcdss/api/v1/products/search"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scraper")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 0 — helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Strip diacritics, lowercase, remove noise tokens for matching."""
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.lower()
    text = re.sub(r"\(.*?\)", " ", text)
    text = re.sub(r"\b\d+[.,]?\d*\s*(mg|mcg|g|ml|%|ui|iu)\b", " ", text, flags=re.I)
    text = re.sub(r"[/;+,]", " ", text)
    text = re.sub(
        r"\b(hydrochloride|hydrochlorid|hcl|natri|sodium|clathrate|bisulphat"
        r"|acetate|citrate|phosphate|sulfate|malate|maleate|tartrate"
        r"|dang|duoi dang|tuong duong)\b",
        " ", text,
    )
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _token_set_ratio(a: str, b: str) -> int:
    """Simplified token-set similarity, 0-100."""
    sa = set(a.split())
    sb = set(b.split())
    if not sa or not sb:
        return 0
    intersection = sa & sb
    union = sa | sb
    return int(len(intersection) / len(union) * 100)


def _lcs_ratio(a: str, b: str) -> int:
    """Longest common subsequence ratio, 0-100."""
    if not a or not b:
        return 0
    from difflib import SequenceMatcher
    return int(SequenceMatcher(None, a, b).ratio() * 100)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:19], fmt[:len(fmt)])
        except ValueError:
            continue
    return None


def _extract_ingredients(raw: str) -> list[tuple[str, str, Optional[str]]]:
    """Split raw ingredient text → list of (raw_name, normalized_name, strength)."""
    if not raw:
        return []
    parts = re.split(r"[;,]", raw)
    results: list[tuple[str, str, Optional[str]]] = []
    for part in parts:
        cleaned = part.strip()
        if not cleaned:
            continue
        m = re.search(r"(\d+[.,]?\d*\s*(?:mg|mcg|g|ml|%|UI|IU))", cleaned, re.I)
        strength = m.group(1) if m else None
        name = cleaned[: m.start()].strip() if m else cleaned
        normalized = _normalize(name)
        if normalized and len(normalized) > 1:
            results.append((cleaned, normalized, strength))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 0 — Load DDI drug catalogue + synonym expansion
# ─────────────────────────────────────────────────────────────────────────────

# Vietnamese / French INN names → English INN names used in DDI DB.
# Keys are _normalize()-d forms. Values match _normalize(ddi_drug.name).
# Common Vietnamese drug names that differ from DrugBank INN:
SYNONYMS: dict[str, str] = {
    # Analgesics / antipyretics
    "paracetamol": "acetaminophen",
    "acetaminophen": "acetaminophen",
    "acid acetylsalicylic": "acetylsalicylicacid",
    "aspirin": "acetylsalicylicacid",
    "acetylsalicylic acid": "acetylsalicylicacid",
    # NSAIDs
    "diclofenac": "diclofenac",
    "naproxen": "naproxen",
    "ketoprofen": "ketoprofen",
    "meloxicam": "meloxicam",
    "celecoxib": "celecoxib",
    "piroxicam": "piroxicam",
    "indomethacin": "indomethacin",
    # Anticoagulants
    "warfarin": "warfarin",
    "heparin": "heparin",
    "enoxaparin": "enoxaparin",
    "dabigatran": "dabigatran",
    "rivaroxaban": "rivaroxaban",
    # Antibiotics
    "amoxicillin": "amoxicillin",
    "ampicillin": "ampicillin",
    "ciprofloxacin": "ciprofloxacin",
    "levofloxacin": "levofloxacin",
    "erythromycin": "erythromycin",
    "azithromycin": "azithromycin",
    "clarithromycin": "clarithromycin",
    "doxycycline": "doxycycline",
    "tetracycline": "tetracycline",
    "metronidazole": "metronidazole",
    "tinidazole": "tinidazole",
    "cefuroxim": "cefuroxime",
    "cefuroxime": "cefuroxime",
    "ceftriaxone": "ceftriaxone",
    "cephalexin": "cephalexin",
    "cefalexin": "cephalexin",
    # Antifungals
    "fluconazol": "fluconazole",
    "fluconazole": "fluconazole",
    "itraconazol": "itraconazole",
    "itraconazole": "itraconazole",
    "ketoconazol": "ketoconazole",
    "ketoconazole": "ketoconazole",
    # Antihypertensives / cardiovascular
    "amlodipine": "amlodipine",
    "amlodipin": "amlodipine",
    "atenolol": "atenolol",
    "bisoprolol": "bisoprolol",
    "carvedilol": "carvedilol",
    "metoprolol": "metoprolol",
    "propranolol": "propranolol",
    "enalapril": "enalapril",
    "lisinopril": "lisinopril",
    "ramipril": "ramipril",
    "captopril": "captopril",
    "losartan": "losartan",
    "valsartan": "valsartan",
    "irbesartan": "irbesartan",
    "candesartan": "candesartan",
    "nifedipin": "nifedipine",
    "nifedipine": "nifedipine",
    "diltiazem": "diltiazem",
    "verapamil": "verapamil",
    "hydrochlorothiazid": "hydrochlorothiazide",
    "hydrochlorothiazide": "hydrochlorothiazide",
    "furosemid": "furosemide",
    "furosemide": "furosemide",
    "spironolacton": "spironolactone",
    "spironolactone": "spironolactone",
    "digoxin": "digoxin",
    "amiodarone": "amiodarone",
    # Diabetes
    "metformin": "metformin",
    "glibenclamid": "glibenclamide",
    "glibenclamide": "glibenclamide",
    "glimepirid": "glimepiride",
    "glimepiride": "glimepiride",
    "gliclazid": "gliclazide",
    "gliclazide": "gliclazide",
    "sitagliptin": "sitagliptin",
    "insulin": "insulin",
    # Lipid-lowering
    "atorvastatin": "atorvastatin",
    "simvastatin": "simvastatin",
    "rosuvastatin": "rosuvastatin",
    "pravastatin": "pravastatin",
    "lovastatin": "lovastatin",
    "fenofibrat": "fenofibrate",
    "fenofibrate": "fenofibrate",
    # GI
    "omeprazol": "omeprazole",
    "omeprazole": "omeprazole",
    "esomeprazol": "esomeprazole",
    "esomeprazole": "esomeprazole",
    "lansoprazol": "lansoprazole",
    "lansoprazole": "lansoprazole",
    "pantoprazol": "pantoprazole",
    "pantoprazole": "pantoprazole",
    "ranitidine": "ranitidine",
    "famotidin": "famotidine",
    "famotidine": "famotidine",
    "domperidon": "domperidone",
    "domperidone": "domperidone",
    "metoclopramid": "metoclopramide",
    "metoclopramide": "metoclopramide",
    # CNS
    "tramadol": "tramadol",
    "morphin": "morphine",
    "morphine": "morphine",
    "codein": "codeine",
    "codeine": "codeine",
    "diazepam": "diazepam",
    "lorazepam": "lorazepam",
    "alprazolam": "alprazolam",
    "phenobarbital": "phenobarbital",
    "phenytoin": "phenytoin",
    "carbamazepin": "carbamazepine",
    "carbamazepine": "carbamazepine",
    "valproat": "valproicacid",
    "valproic acid": "valproicacid",
    "acid valproic": "valproicacid",
    "lamotrigin": "lamotrigine",
    "lamotrigine": "lamotrigine",
    "levetiracetam": "levetiracetam",
    "fluoxetine": "fluoxetine",
    "sertraline": "sertraline",
    "paroxetine": "paroxetine",
    "escitalopram": "escitalopram",
    "citalopram": "citalopram",
    "amitriptyline": "amitriptyline",
    "haloperidol": "haloperidol",
    "olanzapine": "olanzapine",
    "risperidone": "risperidone",
    "clozapine": "clozapine",
    # Vitamins / minerals (common in combination products)
    "vitamin c": "ascorbicacid",
    "acid ascorbic": "ascorbicacid",
    "ascorbic acid": "ascorbicacid",
    "vitamin b1": "thiamine",
    "thiamin": "thiamine",
    "vitamin b6": "pyridoxine",
    "pyridoxin": "pyridoxine",
    "vitamin b12": "cyanocobalamin",
    "cyanocobalamin": "cyanocobalamin",
    "vitamin d": "cholecalciferol",
    "cholecalciferol": "cholecalciferol",
    "vitamin d3": "cholecalciferol",
    "vitamin e": "tocopherol",
    "folic acid": "folicacid",
    "acid folic": "folicacid",
    "calcium": "calcium",
    "canxi": "calcium",
    "magnesium": "magnesium",
    "zinc": "zinc",
    "kem": "zinc",
    # Respiratory
    "salbutamol": "salbutamol",
    "albuterol": "salbutamol",
    "terbutalin": "terbutaline",
    "terbutaline": "terbutaline",
    "budesonid": "budesonide",
    "budesonide": "budesonide",
    "fluticason": "fluticasonepropionate",
    "salmeterol": "salmeterol",
    "theophyllin": "theophylline",
    "theophylline": "theophylline",
    "aminophyllin": "aminophylline",
    "aminophylline": "aminophylline",
    "montelukast": "montelukast",
    # Antiviral / antiretroviral
    "acyclovir": "acyclovir",
    "aciclovir": "acyclovir",
    "oseltamivir": "oseltamivir",
    "zidovudin": "zidovudine",
    "zidovudine": "zidovudine",
    "lamivudin": "lamivudine",
    "lamivudine": "lamivudine",
    # Antituberculosis
    "rifampicin": "rifampicin",
    "rifampin": "rifampicin",
    "isoniazid": "isoniazid",
    "pyrazinamid": "pyrazinamide",
    "pyrazinamide": "pyrazinamide",
    "ethambutol": "ethambutol",
    # Hormones
    "prednisolon": "prednisolone",
    "prednisolone": "prednisolone",
    "dexametason": "dexamethasone",
    "dexamethasone": "dexamethasone",
    "methylprednisolon": "methylprednisolone",
    "methylprednisolone": "methylprednisolone",
    "hydrocortison": "hydrocortisone",
    "hydrocortisone": "hydrocortisone",
    "levothyroxin": "levothyroxine",
    "levothyroxine": "levothyroxine",
    # Immunosuppressants
    "cyclosporin": "cyclosporine",
    "cyclosporine": "cyclosporine",
    "tacrolimus": "tacrolimus",
    "methotrexat": "methotrexate",
    "methotrexate": "methotrexate",
    # Antihistamines
    "loratadin": "loratadine",
    "loratadine": "loratadine",
    "cetirizin": "cetirizine",
    "cetirizine": "cetirizine",
    "fexofenadin": "fexofenadine",
    "fexofenadine": "fexofenadine",
    "chlorpheniramin": "chlorpheniramine",
    "chlorpheniramine": "chlorpheniramine",
    "diphenhydramin": "diphenhydramine",
    "diphenhydramine": "diphenhydramine",
    # Antiparasitic
    "albendazol": "albendazole",
    "albendazole": "albendazole",
    "mebendazol": "mebendazole",
    "mebendazole": "mebendazole",
    "ivermectin": "ivermectin",
    "chloroquin": "chloroquine",
    "chloroquine": "chloroquine",
    # Ophthalmology
    "timolol": "timolol",
    "latanoprost": "latanoprost",
    "dexamethason": "dexamethasone",
    # Urology
    "tamsulosin": "tamsulosin",
    "finasterid": "finasteride",
    "finasteride": "finasteride",
    "sildenafil": "sildenafil",
    # Misc
    "caffein": "caffeine",
    "caffeine": "caffeine",
    "glucosamin": "glucosamine",
    "glucosamine": "glucosamine",
    "colchicin": "colchicine",
    "colchicine": "colchicine",
    "allopurinol": "allopurinol",
    "bisphosphonate": "alendronicacid",
    "alendronat": "alendronicacid",
    "alendronate": "alendronicacid",
    "memantine": "memantine",
    "donepezil": "donepezil",
}


def load_ddi_drugs() -> dict[str, str]:
    """
    Returns {normalized_name: drug_id} for all 572 DDI drugs.
    Includes synonym expansions so Vietnamese INN names resolve correctly.
    """
    if not DDI_DB_PATH.exists():
        log.error("DDI DB not found: %s", DDI_DB_PATH)
        return {}
    conn = sqlite3.connect(DDI_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM drug")
    rows = cursor.fetchall()
    conn.close()

    # Primary map: normalized DDI name → drug_id
    primary: dict[str, str] = {_normalize(name): drug_id for drug_id, name in rows}

    # Reverse synonym map: synonym_normalized → drug_id (via DDI name)
    expanded: dict[str, str] = dict(primary)
    for syn_norm, ddi_norm in SYNONYMS.items():
        if ddi_norm in primary and syn_norm not in expanded:
            expanded[syn_norm] = primary[ddi_norm]

    log.info("DDI map: %d primary + %d synonym entries", len(primary), len(expanded) - len(primary))
    return expanded


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — DAV scraping
# ─────────────────────────────────────────────────────────────────────────────

class DAVClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._req_count = 0

    async def _post(self, payload: dict) -> dict:
        await asyncio.sleep(DAV_RATE_LIMIT_SEC)
        try:
            r = await self._client.post(DAV_API_URL, json=payload, timeout=30)
            r.raise_for_status()
            self._req_count += 1
            return r.json().get("result", {})
        except Exception as exc:
            log.warning("DAV request failed: %s", exc)
            return {}

    async def search(self, filter_text: str = "", skip: int = 0, size: int = DAV_PAGE_SIZE) -> tuple[int, list[dict]]:
        payload = {
            "skipCount": skip,
            "maxResultCount": size,
            "sorting": None,
            "filterText": filter_text,
            "SoDangKyThuoc": {},
            "KichHoat": True,
        }
        result = await self._post(payload)
        return result.get("totalCount", 0), result.get("items", [])

    async def scrape_for_ddi_terms(self, ddi_names: list[str]) -> dict[str, dict]:
        """Query DAV for each DDI generic name, return id→record map."""
        collected: dict[str, dict] = {}
        for i, name in enumerate(ddi_names, 1):
            log.info("[DDI %d/%d] Searching DAV: %s", i, len(ddi_names), name)
            _, items = await self.search(filter_text=name, size=DAV_MAX_PER_DDI_TERM)
            for item in items:
                pid = str(item.get("id") or item.get("soDangKy") or "")
                if pid and pid not in collected:
                    collected[pid] = item
        log.info("After DDI-targeted scrape: %d unique products", len(collected))
        return collected

    async def scrape_broad(self, collected: dict[str, dict], target: int) -> dict[str, dict]:
        """Broad pagination (no filter) until we reach target count."""
        skip = 0
        total_dav = None
        while len(collected) < target:
            total_count, items = await self.search(filter_text="", skip=skip, size=DAV_PAGE_SIZE)
            if total_dav is None:
                total_dav = total_count
                log.info("DAV total available: %d products", total_dav)
            if not items:
                break
            for item in items:
                pid = str(item.get("id") or item.get("soDangKy") or "")
                if pid and pid not in collected:
                    collected[pid] = item
            skip += DAV_PAGE_SIZE
            log.info("Broad scan skip=%d → collected=%d / target=%d", skip, len(collected), target)
            if skip >= total_dav:
                break
        return collected


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — Image acquisition + Cloudinary
# ─────────────────────────────────────────────────────────────────────────────

# Category images — upload these once to Cloudinary.
# Maps dosage form keywords → Cloudinary public_id (created during upload)
DOSAGE_FORM_CATEGORIES = {
    "vien nen": "medis/drugs/vien-nen",
    "vien nang cung": "medis/drugs/vien-nang-cung",
    "vien nang mem": "medis/drugs/vien-nang-mem",
    "dung dich tiem": "medis/drugs/dung-dich-tiem",
    "bot pha tiem": "medis/drugs/bot-pha-tiem",
    "dung dich uong": "medis/drugs/dung-dich-uong",
    "siro": "medis/drugs/siro",
    "hon dich": "medis/drugs/hon-dich",
    "kem boi": "medis/drugs/kem-boi",
    "nho mat": "medis/drugs/nho-mat",
    "thuoc mo": "medis/drugs/thuoc-mo",
    "khi dung": "medis/drugs/khi-dung",
    "cao dan": "medis/drugs/cao-dan",
    "thuoc dat": "medis/drugs/thuoc-dat",
    "default": "medis/drugs/default",
}

# Free stock pharmaceutical images (Unsplash/Pexels no-attribution required)
# These are generic but categorized — real photos not placeholders
CATEGORY_STOCK_IMAGES: dict[str, str] = {
    "medis/drugs/vien-nen": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
    "medis/drugs/vien-nang-cung": "https://images.unsplash.com/photo-1550572017-edd951b55104?w=400&q=80",
    "medis/drugs/vien-nang-mem": "https://images.unsplash.com/photo-1563213126-a4273aed2016?w=400&q=80",
    "medis/drugs/dung-dich-tiem": "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
    "medis/drugs/bot-pha-tiem": "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?w=400&q=80",
    "medis/drugs/dung-dich-uong": "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=400&q=80",
    "medis/drugs/siro": "https://images.unsplash.com/photo-1516574187841-cb9cc2ca948b?w=400&q=80",
    "medis/drugs/hon-dich": "https://images.unsplash.com/photo-1586015555751-63bb77f4322a?w=400&q=80",
    "medis/drugs/kem-boi": "https://images.unsplash.com/photo-1556228841-a3c527ebefe5?w=400&q=80",
    "medis/drugs/nho-mat": "https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=400&q=80",
    "medis/drugs/thuoc-mo": "https://images.unsplash.com/photo-1550572017-edd951b55104?w=400&q=80",
    "medis/drugs/khi-dung": "https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=400&q=80",
    "medis/drugs/cao-dan": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80",
    "medis/drugs/thuoc-dat": "https://images.unsplash.com/photo-1550572017-edd951b55104?w=400&q=80",
    "medis/drugs/default": "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=400&q=80",
}


def _pick_category(dosage_form: Optional[str]) -> str:
    if not dosage_form:
        return "medis/drugs/default"
    normalized = _normalize(dosage_form)
    for keyword, public_id in DOSAGE_FORM_CATEGORIES.items():
        if keyword != "default" and keyword in normalized:
            return public_id
    return "medis/drugs/default"


class CloudinaryClient:
    """Minimal Cloudinary REST client (no SDK required)."""

    def __init__(self, cloud_name: str, api_key: str, api_secret: str, client: httpx.AsyncClient):
        self._cloud = cloud_name
        self._key = api_key
        self._secret = api_secret
        self._http = client
        self._cache: dict[str, str] = {}  # public_id → secure_url

    def _sign(self, params: dict) -> str:
        import hashlib
        import hmac
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if k != "file")
        to_sign = sorted_params + self._secret
        return hashlib.sha1(to_sign.encode()).hexdigest()

    async def upload_from_url(self, source_url: str, public_id: str) -> Optional[str]:
        """Upload image from URL to Cloudinary. Returns secure_url or None."""
        if public_id in self._cache:
            return self._cache[public_id]

        if not self._cloud:
            log.warning("CLOUDINARY_CLOUD_NAME not set — skipping upload")
            return None

        ts = str(int(datetime.now().timestamp()))
        params = {
            "public_id": public_id,
            "timestamp": ts,
            "overwrite": "false",
        }
        signature = self._sign(params)

        try:
            r = await self._http.post(
                f"https://api.cloudinary.com/v1_1/{self._cloud}/image/upload",
                data={
                    **params,
                    "file": source_url,
                    "api_key": self._key,
                    "signature": signature,
                },
                timeout=60,
            )
            data = r.json()
            if "secure_url" in data:
                url = data["secure_url"]
                self._cache[public_id] = url
                log.info("Cloudinary upload OK: %s → %s", public_id, url)
                return url
            # Already exists — fetch it
            if data.get("error", {}).get("http_code") == 400 and "already exists" in str(data):
                url = f"https://res.cloudinary.com/{self._cloud}/image/upload/{public_id}"
                self._cache[public_id] = url
                return url
            log.warning("Cloudinary error: %s", data.get("error"))
        except Exception as exc:
            log.warning("Cloudinary upload failed for %s: %s", public_id, exc)
        return None

    async def ensure_category_images(self) -> dict[str, str]:
        """Upload all category stock images once. Returns {public_id: secure_url}."""
        result: dict[str, str] = {}
        for public_id, stock_url in CATEGORY_STOCK_IMAGES.items():
            url = await self.upload_from_url(stock_url, public_id)
            result[public_id] = url or stock_url  # fallback to stock URL
        return result


async def _try_pharmacy_image(client: httpx.AsyncClient, product_name: str) -> Optional[str]:
    """
    Try Long Chau pharmacy API for real product image.
    Returns a direct image URL if found, else None.
    """
    try:
        r = await client.get(
            PHARMACY_SEARCH_URL,
            params={"keyword": product_name, "page": 1, "size": 1},
            timeout=10,
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        if r.status_code == 200:
            data = r.json()
            products = data.get("data", {}).get("products", []) or data.get("products", [])
            if products:
                img = products[0].get("thumbnail") or products[0].get("image") or products[0].get("imageUrl")
                if img and img.startswith("http"):
                    return img
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — DDI mapping engine
# ─────────────────────────────────────────────────────────────────────────────

class DDIMappingEngine:
    """
    Multi-tier fuzzy matching: ingredient text → DDI drug_id.

    Tiers (in order):
      1. Exact normalized match         → confidence 100
      2. Substring (drug name in ing.)  → confidence 90
      3. Token-set ratio ≥ 80           → confidence = ratio
      4. LCS sequence ratio ≥ 75        → confidence = ratio
    """

    def __init__(self, ddi_map: dict[str, str]):
        # {normalized_name: drug_id}
        self._map = ddi_map
        # Pre-split tokens for each DDI drug
        self._tokens: dict[str, list[str]] = {
            name: name.split() for name in ddi_map
        }

    def match(self, ingredient_normalized: str) -> tuple[Optional[str], int]:
        """Returns (drug_id, confidence) or (None, 0)."""
        norm = ingredient_normalized.strip()
        if not norm:
            return None, 0

        # Tier 1 — exact
        if norm in self._map:
            return self._map[norm], 100

        # Tier 2 — drug name is substring of ingredient
        for ddi_name, drug_id in self._map.items():
            if len(ddi_name) >= 4 and ddi_name in norm:
                return drug_id, 90

        # Tier 3 — token-set ratio
        best_id, best_score = None, 0
        for ddi_name, drug_id in self._map.items():
            score = _token_set_ratio(norm, ddi_name)
            if score >= 80 and score > best_score:
                best_id, best_score = drug_id, score

        if best_id:
            return best_id, best_score

        # Tier 4 — LCS ratio
        for ddi_name, drug_id in self._map.items():
            score = _lcs_ratio(norm, ddi_name)
            if score >= 75 and score > best_score:
                best_id, best_score = drug_id, score

        return best_id, best_score


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4 — PostgreSQL upsert
# ─────────────────────────────────────────────────────────────────────────────

async def upsert_product(
    session: AsyncSession,
    record: dict,
    image_url: Optional[str],
    mapper: DDIMappingEngine,
) -> tuple[bool, int]:
    """
    Upsert one DAV record into market_drug_products + ingredients.
    Returns (created: bool, mapped_ingredient_count: int).
    """
    reg_num = (record.get("soDangKy") or "").strip()
    if not reg_num:
        return False, 0

    basic = record.get("thongTinThuocCoBan") or {}
    reg = record.get("thongTinDangKyThuoc") or {}
    source_id = record.get("id")

    # ── payload hash for change detection ──────────────────────────────────
    payload_hash = hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    existing = await session.scalar(
        select(MarketDrugProduct).where(MarketDrugProduct.registration_number == reg_num)
    )
    created = existing is None
    product = existing or MarketDrugProduct(registration_number=reg_num)
    if not created and product.source_payload_hash == payload_hash:
        return False, 0  # unchanged — skip

    if created:
        session.add(product)

    product.source_product_id = source_id
    product.old_registration_number = record.get("soDangKyCu") or None
    product.product_name = record.get("tenThuoc") or reg_num
    product.normalized_product_name = _normalize(product.product_name)
    product.dosage_form = basic.get("dangBaoChe") or record.get("dangBaoChe")
    product.packaging = basic.get("dongGoi") or record.get("dongGoi")
    product.route_name = basic.get("tenDuongDung")
    product.quality_standard = basic.get("tieuChuan") or record.get("tieuChuan")
    product.shelf_life = basic.get("tuoiTho") or record.get("tuoiTho")
    product.decision_number = reg.get("soQuyetDinh") or record.get("soQuyetDinh")
    product.issue_batch = reg.get("dotCap") or record.get("dotCap")
    product.registration_date = _parse_dt(reg.get("ngayCapSoDangKy") or record.get("ngayCapSoDangKy"))
    product.expiry_date = _parse_dt(reg.get("ngayHetHanSoDangKy"))
    product.is_expired = bool(record.get("isHetHan"))
    product.is_withdrawn = bool(record.get("isDaRutSoDangKy"))
    product.is_active = bool(record.get("isActive", True))
    product.raw_ingredients_text = basic.get("hoatChatChinh") or record.get("hoatChatChinh")
    product.image_url = image_url
    product.source_payload = record
    product.source_payload_hash = payload_hash
    product.last_synced_at = datetime.now()

    await session.flush()

    # ── replace ingredients ─────────────────────────────────────────────────
    old_ings = (await session.execute(
        select(MarketDrugProductIngredient).where(MarketDrugProductIngredient.market_product_id == product.id)
    )).scalars().all()
    for row in old_ings:
        await session.delete(row)
    await session.flush()

    mapped_count = 0
    seen_keys: set[tuple] = set()
    for idx, (raw_name, norm_name, strength) in enumerate(_extract_ingredients(product.raw_ingredients_text or "")):
        key = (norm_name, strength or "")
        if key in seen_keys:
            continue
        seen_keys.add(key)

        ddi_id, confidence = mapper.match(norm_name)
        if ddi_id:
            mapped_count += 1

        session.add(MarketDrugProductIngredient(
            market_product_id=product.id,
            ingredient_name_raw=raw_name,
            ingredient_name_normalized=norm_name,
            strength_raw=strength,
            ddi_drug_id=ddi_id,
            mapping_confidence=confidence if ddi_id else None,
            sort_order=idx,
        ))

    await session.flush()
    return created, mapped_count


# ─────────────────────────────────────────────────────────────────────────────
# Checkpoint helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_checkpoint() -> dict:
    if CHECKPOINT_PATH.exists():
        try:
            return json.loads(CHECKPOINT_PATH.read_text())
        except Exception:
            pass
    return {"scraped_ids": [], "upserted_reg_nums": [], "category_urls": {}}


def save_checkpoint(data: dict) -> None:
    CHECKPOINT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# Main orchestrator
# ─────────────────────────────────────────────────────────────────────────────

async def run(resume: bool = False, dry_run: bool = False) -> None:
    checkpoint = load_checkpoint() if resume else {"scraped_ids": [], "upserted_reg_nums": [], "category_urls": {}}

    if not CLOUDINARY_CLOUD_NAME and not dry_run:
        log.warning(
            "CLOUDINARY_CLOUD_NAME not set — images will use stock URL directly (no Cloudinary upload). "
            "Set the env var for production use."
        )

    # ── Load DDI catalogue ──────────────────────────────────────────────────
    ddi_map = load_ddi_drugs()
    log.info("Loaded %d DDI drugs for mapping", len(ddi_map))
    mapper = DDIMappingEngine(ddi_map)
    ddi_names = list({name.split()[0] for name in ddi_map})  # first token = primary name

    async with httpx.AsyncClient(
        headers={"Content-Type": "application/json", "User-Agent": "Medis-Scraper/1.0"},
    ) as http:
        dav = DAVClient(http)
        cloudinary = CloudinaryClient(
            CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, http
        )

        # ── Phase 2a: ensure category images on Cloudinary ─────────────────
        if not dry_run and checkpoint.get("category_urls"):
            category_urls = checkpoint["category_urls"]
            log.info("Using cached category URLs from checkpoint")
        else:
            log.info("Uploading category stock images to Cloudinary...")
            category_urls = {} if dry_run else await cloudinary.ensure_category_images()
            if not dry_run:
                checkpoint["category_urls"] = category_urls
                save_checkpoint(checkpoint)

        # ── Phase 1a: DDI-targeted scrape ──────────────────────────────────
        already_scraped = set(checkpoint["scraped_ids"])
        collected: dict[str, dict] = {}

        log.info("Phase 1a: DDI-targeted scrape for %d terms...", len(ddi_names))
        ddi_collected = await dav.scrape_for_ddi_terms(ddi_names)
        for pid, record in ddi_collected.items():
            if pid not in already_scraped:
                collected[pid] = record

        # ── Phase 1b: broad fill to TARGET_TOTAL ───────────────────────────
        log.info("Phase 1b: broad fill to %d products...", TARGET_TOTAL)
        collected = await dav.scrape_broad(collected, TARGET_TOTAL)

        all_records = list(collected.values())
        log.info("Total scraped: %d products (%d DAV requests)", len(all_records), dav._req_count)

        # Save scraped IDs for resumability
        checkpoint["scraped_ids"] = list(collected.keys())
        save_checkpoint(checkpoint)

        # ── Phase 3 & 4: image + upsert ────────────────────────────────────
        already_upserted = set(checkpoint["upserted_reg_nums"])
        stats = {"created": 0, "updated": 0, "skipped": 0, "mapped_ingredients": 0, "errors": 0}

        async with AsyncSessionLocal() as session:
            for i, record in enumerate(all_records, 1):
                reg_num = (record.get("soDangKy") or "").strip()
                if not reg_num or reg_num in already_upserted:
                    stats["skipped"] += 1
                    continue

                # Image: try pharmacy → fallback to category
                product_name = record.get("tenThuoc") or ""
                dosage_form = (record.get("thongTinThuocCoBan") or {}).get("dangBaoChe")
                category_public_id = _pick_category(dosage_form)

                image_url: Optional[str] = None
                if not dry_run:
                    # Try pharmacy first (rate-limited — don't hammer)
                    if i % 5 == 0:  # only 1 in 5 products for pharmacy lookup
                        image_url = await _try_pharmacy_image(http, product_name)
                        if image_url:
                            # Upload pharmacy image to Cloudinary under product namespace
                            slug = re.sub(r"[^a-z0-9]", "-", _normalize(product_name))[:60]
                            public_id = f"medis/products/{slug}"
                            uploaded = await cloudinary.upload_from_url(image_url, public_id)
                            image_url = uploaded or image_url

                    if not image_url:
                        image_url = category_urls.get(category_public_id)

                try:
                    if not dry_run:
                        created, mapped = await upsert_product(session, record, image_url, mapper)
                        if created:
                            stats["created"] += 1
                        else:
                            stats["updated"] += 1
                        stats["mapped_ingredients"] += mapped

                        if i % 50 == 0:
                            await session.commit()
                            checkpoint["upserted_reg_nums"].append(reg_num)
                            save_checkpoint(checkpoint)
                            log.info(
                                "[%d/%d] created=%d updated=%d mapped_ing=%d",
                                i, len(all_records),
                                stats["created"], stats["updated"], stats["mapped_ingredients"],
                            )
                    else:
                        ingredients = _extract_ingredients(
                            (record.get("thongTinThuocCoBan") or {}).get("hoatChatChinh") or ""
                        )
                        mapped = sum(1 for _, n, _ in ingredients if mapper.match(n)[0])
                        stats["created"] += 1
                        stats["mapped_ingredients"] += mapped
                        if i <= 5:
                            log.info("DRY-RUN  %s  →  ing_mapped=%d  img_category=%s",
                                     record.get("tenThuoc"), mapped, category_public_id)

                except Exception as exc:
                    log.error("Upsert failed for %s: %s", reg_num, exc)
                    stats["errors"] += 1
                    await session.rollback()

            if not dry_run:
                await session.commit()

        log.info("=" * 60)
        log.info("DONE  created=%d  updated=%d  skipped=%d  errors=%d  mapped_ingredients=%d",
                 stats["created"], stats["updated"], stats["skipped"], stats["errors"], stats["mapped_ingredients"])
        log.info("Checkpoint saved to: %s", CHECKPOINT_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape DAV drug data for Medis production")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="No DB writes, no Cloudinary uploads")
    args = parser.parse_args()

    if args.dry_run:
        log.info("DRY RUN — no DB writes, no Cloudinary uploads")

    asyncio.run(run(resume=args.resume, dry_run=args.dry_run))
