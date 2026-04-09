from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from math import ceil
from typing import List, Optional

from fastapi import Request
from openai import AsyncOpenAI
from sqlalchemy import delete as sql_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.chat_message import ChatMessage
from app.models.health_profile import HealthProfile
from app.models.prescription import Prescription, PrescriptionStatus
from app.models.user import User
from app.schemas.chatbot import ChatMessageResponse, QuickSuggestion
from app.schemas.user import PaginatedResponse, PaginationMeta

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """Bạn là trợ lý tư vấn y tế AI của MediSmart — nền tảng y tế Việt Nam.

{health_context}

NHIỆM VỤ CỦA BẠN:
- Tư vấn thông tin sức khỏe tổng quát dựa trên hồ sơ người dùng
- Giải thích cách dùng thuốc, tác dụng phụ, thời điểm uống
- Hỗ trợ nhận biết triệu chứng cơ bản và gợi ý sơ bộ
- Trả lời bằng tiếng Việt, thân thiện, dễ hiểu

NGUYÊN TẮC BẮT BUỘC:
- Luôn nhắc: "Thông tin chỉ mang tính tham khảo, không thay thế khám bác sĩ"
- KHÔNG kê đơn thuốc cụ thể với liều lượng chính xác
- KHÔNG chẩn đoán bệnh chính thức
- Với triệu chứng nguy hiểm (đau ngực, khó thở, mất ý thức...) → LUÔN khuyên gọi cấp cứu hoặc đến bệnh viện ngay
- Nếu câu hỏi ngoài lĩnh vực y tế → từ chối nhẹ nhàng"""

_QUICK_SUGGESTIONS = [
    QuickSuggestion(text="Thuốc này uống trước hay sau ăn?", category="drug_usage"),
    QuickSuggestion(text="Tôi bị đau đầu, nên làm gì?", category="symptom"),
    QuickSuggestion(text="Có thể dùng chung các thuốc này không?", category="interaction"),
    QuickSuggestion(text="Tác dụng phụ của thuốc này là gì?", category="drug_usage"),
    QuickSuggestion(text="Triệu chứng này có nguy hiểm không?", category="symptom"),
]


def _calc_age(dob: Optional[datetime]) -> Optional[int]:
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class ChatbotService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def _get_health_context(self, user_id: int) -> str:
        # User info
        user = await self.db.scalar(select(User).where(User.id == user_id))
        if not user:
            return "Chưa có thông tin sức khỏe."

        age = _calc_age(user.date_of_birth)
        lines = ["Thông tin bệnh nhân:"]
        lines.append(
            f"- Họ tên: {user.full_name or 'Chưa cập nhật'}, "
            f"Tuổi: {age or 'N/A'}, "
            f"Giới tính: {user.gender or 'N/A'}"
        )

        # Recent health profiles
        hp_rows = (
            await self.db.execute(
                select(HealthProfile)
                .where(HealthProfile.user_id == user_id)
                .order_by(HealthProfile.exam_date.desc())
                .limit(3)
            )
        ).scalars().all()

        if hp_rows:
            lines.append("\nLịch sử bệnh án gần đây:")
            for hp in hp_rows:
                lines.append(
                    f"- {hp.diagnosis_name} ({hp.exam_date}): {hp.symptoms or 'Không có triệu chứng mô tả'}"
                )

        # Active prescriptions
        pres_rows = (
            await self.db.execute(
                select(Prescription)
                .where(
                    Prescription.user_id == user_id,
                    Prescription.status == PrescriptionStatus.active,
                )
                .options(selectinload(Prescription.items))
            )
        ).scalars().all()

        if pres_rows:
            lines.append("\nThuốc đang sử dụng:")
            for pres in pres_rows:
                for item in pres.items:
                    lines.append(
                        f"- {item.drug_name} {item.dosage}"
                        + (f" — {item.frequency}" if item.frequency else "")
                    )

        return "\n".join(lines) if len(lines) > 1 else "Chưa có thông tin sức khỏe."

    async def send_message(
        self,
        user_id: int,
        content: str,
        request: Optional[Request] = None,
    ) -> ChatMessageResponse:
        # 1. Save user message
        user_msg = ChatMessage(user_id=user_id, role="user", content=content)
        self.db.add(user_msg)
        await self.db.flush()

        # 2. Fetch last 10 messages before this one
        history_rows = (
            await self.db.execute(
                select(ChatMessage)
                .where(
                    ChatMessage.user_id == user_id,
                    ChatMessage.id != user_msg.id,
                )
                .order_by(ChatMessage.created_at.desc())
                .limit(10)
            )
        ).scalars().all()
        history_rows = list(reversed(history_rows))

        # 3. Build health context
        health_context = await self._get_health_context(user_id)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(health_context=health_context)

        # 4. Build messages list
        messages = [{"role": "system", "content": system_prompt}]
        for h in history_rows:
            messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": content})

        # 5. Call OpenAI
        response = await self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
        )
        reply = response.choices[0].message.content

        # 6. Save assistant reply
        assistant_msg = ChatMessage(user_id=user_id, role="assistant", content=reply)
        self.db.add(assistant_msg)
        await self.db.flush()

        # 7. Log activity
        try:
            from app.services.log_service import ActivityLogService
            await ActivityLogService(self.db).log(
                "CHATBOT_MESSAGE", user_id=user_id, request=request
            )
        except Exception:
            pass

        return ChatMessageResponse.model_validate(assistant_msg)

    async def get_history(
        self,
        user_id: int,
        page: int,
        size: int,
    ) -> PaginatedResponse:
        stmt = select(ChatMessage).where(ChatMessage.user_id == user_id)
        total = await self.db.scalar(
            select(func.count()).select_from(stmt.subquery())
        )
        rows = (
            await self.db.execute(
                stmt.order_by(ChatMessage.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()

        return PaginatedResponse(
            items=[ChatMessageResponse.model_validate(r) for r in rows],
            meta=PaginationMeta(
                total=total,
                page=page,
                size=size,
                total_pages=max(1, ceil(total / size)),
            ),
        )

    async def delete_history(self, user_id: int) -> int:
        result = await self.db.execute(
            sql_delete(ChatMessage).where(ChatMessage.user_id == user_id)
        )
        return result.rowcount

    def get_quick_suggestions(self) -> List[QuickSuggestion]:
        return _QUICK_SUGGESTIONS
