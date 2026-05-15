#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_test_drugs.py — Seed test drugs matching DDI-MVP drug2vec names
=====================================================================
Tạo vài thuốc test trong DB với generic_name khớp với drug2vec
để test full flow: Backend → DDI-MVP → prediction → cache.

Chạy:
    cd backend/
    python seed_test_drugs.py
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Drug, DrugBrandName, DrugWarning, DrugFeature


_NOW = datetime.now(timezone.utc)

# Thuốc với generic_name khớp drug2vec keys
TEST_DRUGS = [
    {
        "id": "DB00945",
        "generic_name": "Acetylsalicylicacid",  # drug2vec key
        "description": "Aspirin (acetylsalicylic acid) là thuốc salicylate dùng giảm đau, hạ sốt và chống viêm.",
        "brand_names": [
            {"name": "Aspirin 100mg", "route": "Oral", "strength": "100 mg", "dosage_form": "Tablet", "country": "Germany"},
            {"name": "Aspirin 500mg", "route": "Oral", "strength": "500 mg", "dosage_form": "Tablet", "country": "Germany"},
        ],
        "warnings": [
            "Không dùng cho trẻ em dưới 12 tuổi do nguy cơ hội chứng Reye.",
            "Thận trọng khi dùng cùng thuốc chống đông máu.",
        ],
        "features": {
            "targets": "Prostaglandin G/H synthase 1, Prostaglandin G/H synthase 2",
            "enzymes": "Cytochrome P450 2C9",
            "pathways": "Aspirin Action Pathway",
            "smiles": "CC(=O)OC1=CC=CC=C1C(O)=O"
        }
    },
    {
        "id": "DB01050",
        "generic_name": "Ibuprofen",
        "description": "Ibuprofen là thuốc chống viêm không steroid (NSAID) dùng giảm đau và hạ sốt.",
        "brand_names": [
            {"name": "Advil 200mg", "route": "Oral", "strength": "200 mg", "dosage_form": "Tablet", "country": "USA"},
            {"name": "Brufen 400mg", "route": "Oral", "strength": "400 mg", "dosage_form": "Tablet", "country": "UK"},
        ],
        "warnings": [
            "Không dùng trong 3 tháng cuối thai kỳ.",
            "Có thể gây loét dạ dày nếu dùng dài ngày.",
        ],
        "features": {
            "targets": "Prostaglandin G/H synthase 1, Prostaglandin G/H synthase 2",
            "enzymes": "Cytochrome P450 2C9, Cytochrome P450 2C19",
            "pathways": "Ibuprofen Action Pathway",
            "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(O)=O"
        }
    },
    {
        "id": "DB00316",
        "generic_name": "Acetaminophen",  # drug2vec key (Paracetamol)
        "description": "Acetaminophen (Paracetamol) là thuốc giảm đau, hạ sốt phổ biến.",
        "brand_names": [
            {"name": "Panadol 500mg", "route": "Oral", "strength": "500 mg", "dosage_form": "Tablet", "country": "UK"},
            {"name": "Tylenol 500mg", "route": "Oral", "strength": "500 mg", "dosage_form": "Tablet", "country": "USA"},
        ],
        "warnings": [
            "Không vượt quá 4g/ngày — nguy cơ tổn thương gan.",
            "Thận trọng ở bệnh nhân suy gan hoặc nghiện rượu.",
        ],
        "features": {
            "targets": "Prostaglandin G/H synthase 1, Prostaglandin G/H synthase 2",
            "enzymes": "Cytochrome P450 2E1, Cytochrome P450 1A2",
            "pathways": "Acetaminophen Action Pathway",
            "smiles": "CC(=O)NC1=CC=C(O)C=C1"
        }
    },
    {
        "id": "DB00264",
        "generic_name": "Metoprolol",
        "description": "Metoprolol là thuốc chẹn beta chọn lọc dùng điều trị tăng huyết áp và suy tim.",
        "brand_names": [
            {"name": "Betaloc 50mg", "route": "Oral", "strength": "50 mg", "dosage_form": "Tablet", "country": "Sweden"},
        ],
        "warnings": [
            "Không ngưng đột ngột — nguy cơ hội chứng phản hồi.",
        ],
        "features": {
            "targets": "Beta-1 adrenergic receptor",
            "enzymes": "Cytochrome P450 2D6",
            "pathways": "Metoprolol Action Pathway",
            "smiles": "CC(C)NCC(O)COC1=CC=C(CCOC)C=C1"
        }
    },
    {
        "id": "DB00672",
        "generic_name": "Chloroquine",
        "description": "Chloroquine là thuốc dùng điều trị và phòng ngừa sốt rét.",
        "brand_names": [
            {"name": "Aralen 250mg", "route": "Oral", "strength": "250 mg", "dosage_form": "Tablet", "country": "USA"},
        ],
        "warnings": [
            "Theo dõi thị lực khi dùng dài ngày.",
        ],
        "features": {
            "targets": "Tumor necrosis factor",
            "enzymes": "Cytochrome P450 2D6, Cytochrome P450 3A4",
            "pathways": "Chloroquine Action Pathway",
            "smiles": "CCN(CC)CCCC(C)NC1=C2C=CC(Cl)=CC2=NC=C1"
        }
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        for drug_data in TEST_DRUGS:
            existing = await db.scalar(
                select(Drug).where(Drug.id == drug_data["id"])
            )
            
            if not existing:
                drug = Drug(
                    id=drug_data["id"],
                    generic_name=drug_data["generic_name"],
                    description=drug_data["description"],
                )
                db.add(drug)
                await db.flush()

                for bn in drug_data.get("brand_names", []):
                    db.add(DrugBrandName(drug_id=drug_data["id"], **bn))

                for wt in drug_data.get("warnings", []):
                    db.add(DrugWarning(drug_id=drug_data["id"], warning_text=wt))
                
                print(f"  ✅ Drug {drug_data['id']} — {drug_data['generic_name']}")
            else:
                print(f"  ~ Drug {drug_data['id']} (already exists)")

            # Seed features regardless of whether drug was just created
            feat_existing = await db.scalar(
                select(DrugFeature).where(DrugFeature.drug_id == drug_data["id"])
            )
            if not feat_existing and "features" in drug_data:
                db.add(DrugFeature(drug_id=drug_data["id"], **drug_data["features"]))
                print(f"  ✅ Features for {drug_data['id']}")

        await db.commit()
        print("\n✅ Seed hoàn tất!")


if __name__ == "__main__":
    asyncio.run(seed())
