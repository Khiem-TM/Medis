# -*- coding: utf-8 -*-
"""
api.py — DDI-MVP FastAPI Server
=================================
REST API cho web developer tích hợp.

Khởi động:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload

Hoặc với gunicorn (production):
    gunicorn api:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

Lưu ý: dùng 1 worker (w=1) vì model TF không thread-safe với fork.

Endpoints:
    POST /api/predict          — Dự đoán đơn thuốc (danh sách thuốc)
    POST /api/predict/pair     — Dự đoán một cặp thuốc cụ thể
    GET  /api/drugs            — Danh sách thuốc đã biết (có phân trang)
    GET  /api/drugs/search     — Tìm kiếm tên thuốc
    GET  /health               — Health check
    GET  /api/labels           — Danh sách 65 nhãn tương tác
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from inference import DDIPredictor


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

MODEL_DIR    = os.getenv("MODEL_DIR", "models/")
THRESHOLD    = float(os.getenv("DDI_THRESHOLD", "0.40"))
LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger("ddi_api")


# ─────────────────────────────────────────────────────────────────────────────
# LIFESPAN: load model once at startup
# ─────────────────────────────────────────────────────────────────────────────

predictor: Optional[DDIPredictor] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global predictor
    logger.info(f"Loading DDIPredictor from {MODEL_DIR}...")
    predictor = DDIPredictor(model_dir=MODEL_DIR, threshold=THRESHOLD)
    logger.info("Model loaded successfully.")
    yield
    logger.info("Shutting down.")


# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DDI-MVP API",
    description=(
        "Drug-Drug Interaction Prediction API\n\n"
        "Dự đoán tương tác thuốc từ đơn thuốc, phân loại vào 65 nhãn "
        "dựa trên model ModernDDIMDL (ChemBERTa + Residual + Attention)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dev: cho phép tất cả; production: giới hạn domain
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class PrescriptionRequest(BaseModel):
    """Body cho endpoint dự đoán đơn thuốc."""
    drugs: List[str] = Field(
        ...,
        min_items=2,
        max_items=50,
        description="Danh sách tên thuốc trong đơn (tối thiểu 2, tối đa 50)",
        example=["Aspirin", "Warfarin", "Ibuprofen"],
    )
    threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Ngưỡng confidence để đánh dấu có tương tác (mặc định: 0.40). "
            "Tăng lên để giảm false positive, giảm xuống để nhạy hơn."
        ),
    )

    @validator("drugs")
    def strip_drug_names(cls, v):
        return [d.strip() for d in v if d.strip()]


class DrugPairRequest(BaseModel):
    """Body cho endpoint dự đoán cặp thuốc."""
    drug_a: str = Field(..., description="Tên thuốc A", example="Warfarin")
    drug_b: str = Field(..., description="Tên thuốc B", example="Aspirin")


class InteractionResult(BaseModel):
    drug_a: str
    drug_b: str
    label: str
    confidence: float
    top3_predictions: List[dict]


class PrescriptionResponse(BaseModel):
    has_interaction: bool
    total_pairs_checked: int
    unknown_drugs: List[str]
    interactions: List[InteractionResult]
    message: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# MEDIS BACKEND INTEGRATION — Adapter endpoint
# ─────────────────────────────────────────────────────────────────────────────

class MedisDrugPayload(BaseModel):
    """Payload for a single drug from the Medis backend."""
    id: str = Field(..., description="DrugBank ID (e.g. DB00945)")
    generic_name: Optional[str] = Field(None, description="Generic name (e.g. Aspirin)")
    targets: Optional[str] = None
    enzymes: Optional[str] = None
    pathways: Optional[str] = None
    smiles: Optional[str] = None


class MedisPredictRequest(BaseModel):
    """Request format matching Medis backend ml_client.py."""
    drug_a: MedisDrugPayload
    drug_b: MedisDrugPayload


def _resolve_drug_name(payload: MedisDrugPayload) -> Optional[str]:
    """
    Resolve a drug payload from Medis backend to a drug2vec key.

    Strategy (in order):
    1. generic_name → exact match in drug2vec
    2. generic_name → case-insensitive match in drug2vec
    3. DrugBank ID → not supported (drug2vec uses names, not IDs)

    Returns None if no match found.
    """
    if predictor is None:
        return None

    known_drugs = predictor.list_known_drugs()

    # 1. Try generic_name exact match
    name = payload.generic_name
    if name and name in predictor._drug2vec:
        return name

    # 2. Try case-insensitive match
    if name:
        name_lower = name.lower()
        for d in known_drugs:
            if d.lower() == name_lower:
                return d

    return None


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post(
    "/predict",
    tags=["Medis Integration"],
    summary="Adapter endpoint cho Medis backend (ml_client.py)",
)
def predict_for_medis(body: MedisPredictRequest):
    """
    Endpoint tương thích với Medis backend ``ml_client.py``.

    Nhận format::

        {
          "drug_a": {"id": "DB00945", "generic_name": "Aspirin", ...},
          "drug_b": {"id": "DB00316", "generic_name": "Warfarin", ...}
        }

    Trả về::

        {"event_name": "the metabolism of ...", "confidence": 0.78}

    Nếu không tìm thấy thuốc trong drug2vec, trả 404.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model chưa sẵn sàng")

    name_a = _resolve_drug_name(body.drug_a)
    name_b = _resolve_drug_name(body.drug_b)

    missing = []
    if not name_a:
        missing.append(f"{body.drug_a.id} ({body.drug_a.generic_name})")
    if not name_b:
        missing.append(f"{body.drug_b.id} ({body.drug_b.generic_name})")

    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Thuốc không có trong DDI model: {', '.join(missing)}",
        )

    try:
        result = predictor.predict_pair(name_a, name_b)
    except Exception as e:
        logger.exception("Medis predict error")
        raise HTTPException(status_code=500, detail=str(e))

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return {
        "event_name": result["predicted_label"],
        "confidence": result["confidence"],
    }


@app.get("/health", tags=["System"])
def health():
    """Health check — xác nhận API đang chạy và model đã load."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model chưa sẵn sàng")
    return {
        "status": "ok",
        "num_known_drugs": len(predictor.list_known_drugs()),
        "num_classes": predictor._num_classes,
        "threshold": predictor.threshold,
    }


@app.post(
    "/api/predict",
    response_model=PrescriptionResponse,
    tags=["Prediction"],
    summary="Dự đoán tương tác trong đơn thuốc",
)
def predict_prescription(body: PrescriptionRequest):
    """
    Nhận danh sách thuốc trong một đơn, kiểm tra tất cả các cặp,
    trả về những cặp có tương tác kèm nhãn phân loại.

    **Lưu ý**: Tên thuốc phải khớp chính xác với tên trong training database.
    Dùng `/api/drugs/search` để tìm tên đúng.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model chưa sẵn sàng")

    try:
        result = predictor.predict_prescription(
            drug_list=body.drugs,
            threshold=body.threshold,
        )
    except Exception as e:
        logger.exception("Prediction error")
        raise HTTPException(status_code=500, detail=str(e))

    return result


@app.post(
    "/api/predict/pair",
    tags=["Prediction"],
    summary="Dự đoán tương tác cho một cặp thuốc",
)
def predict_pair(body: DrugPairRequest):
    """
    Dự đoán tương tác cho một cặp thuốc cụ thể.
    Trả về toàn bộ 65 nhãn được xếp hạng theo confidence.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model chưa sẵn sàng")

    try:
        result = predictor.predict_pair(body.drug_a, body.drug_b)
    except Exception as e:
        logger.exception("Pair prediction error")
        raise HTTPException(status_code=500, detail=str(e))

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@app.get(
    "/api/drugs",
    tags=["Reference"],
    summary="Danh sách thuốc đã biết",
)
def list_drugs(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(50, ge=1, le=500, description="Số item mỗi trang"),
):
    """
    Trả về danh sách thuốc có trong training database (phân trang).
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model chưa sẵn sàng")

    all_drugs = predictor.list_known_drugs()
    total = len(all_drugs)
    start = (page - 1) * page_size
    end   = start + page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "drugs": all_drugs[start:end],
    }


@app.get(
    "/api/drugs/search",
    tags=["Reference"],
    summary="Tìm kiếm tên thuốc",
)
def search_drugs(
    q: str = Query(..., min_length=2, description="Từ khóa tìm kiếm (tối thiểu 2 ký tự)"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Tìm kiếm thuốc theo tên (case-insensitive substring match).
    Hữu ích để frontend gợi ý autocomplete.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model chưa sẵn sàng")

    q_lower = q.lower()
    matches = [
        d for d in predictor.list_known_drugs()
        if q_lower in d.lower()
    ]

    return {
        "query": q,
        "total_matches": len(matches),
        "results": matches[:limit],
    }


@app.get(
    "/api/labels",
    tags=["Reference"],
    summary="Danh sách 65 nhãn tương tác",
)
def list_labels():
    """
    Trả về danh sách đầy đủ 65 nhãn tương tác thuốc, xếp theo tần suất trong training data.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model chưa sẵn sàng")

    labels = [
        {"id": i, "label": predictor._id2label[i]}
        for i in range(predictor._num_classes)
    ]

    return {
        "total": len(labels),
        "labels": labels,
    }
