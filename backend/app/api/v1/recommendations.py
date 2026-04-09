from __future__ import annotations

import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["✨ Gợi ý thuốc"])


def _svc(db: AsyncSession) -> RecommendationService:
    return RecommendationService(db)


@router.post(
    "",
    summary="Gợi ý thuốc theo triệu chứng cá nhân hóa",
    description=(
        "AI phân tích triệu chứng, lịch sử bệnh và thuốc đang dùng "
        "để gợi ý thuốc phù hợp và kiểm tra tương tác."
    ),
)
async def recommend(
    data: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await _svc(db).recommend(current_user.id, data)
    return {
        "success": True,
        "message": "Đã tạo gợi ý thuốc thành công",
        "data": result.model_dump(),
    }


@router.post(
    "/export",
    summary="Xuất danh sách thuốc gợi ý ra Excel",
)
async def export_recommendation(
    data: RecommendationResponse,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await _svc(db).export_xlsx(data, current_user.id)
    filename = f"goi-y-thuoc-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
