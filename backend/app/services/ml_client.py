import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def predict_interaction(
    drug_a_id: str,
    drug_b_id: str,
    features_a: dict,
    features_b: dict,
) -> Optional[dict]:
    """
    Call DDI-MVP microservice to predict drug interaction event type.

    Request:  POST {ML_SERVICE_URL}/predict
              {
                "drug_a": {"id": "DB00945", "generic_name": "Aspirin", ...},
                "drug_b": {"id": "DB00316", "generic_name": "Warfarin", ...}
              }

    Response: {"event_name": str, "confidence": float}

    Returns None on any failure — caller degrades gracefully (treats pair as safe).
    """
    payload = {
        "drug_a": {"id": drug_a_id, **features_a},
        "drug_b": {"id": drug_b_id, **features_b},
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ML_SERVICE_TIMEOUT) as client:
            resp = await client.post(f"{settings.ML_SERVICE_URL}/predict", json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "DDI-MVP service HTTP %s for pair (%s, %s): %s",
            exc.response.status_code, drug_a_id, drug_b_id, exc,
        )
        return None
    except httpx.RequestError as exc:
        logger.warning("DDI-MVP service unreachable for pair (%s, %s): %s", drug_a_id, drug_b_id, exc)
        return None
