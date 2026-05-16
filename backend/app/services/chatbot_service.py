from __future__ import annotations

import logging
import json
from datetime import date, datetime, timezone
from math import ceil
from typing import Any, List, Optional

from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy import delete as sql_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.chat_message import ChatMessage, ChatSession
from app.models.health_baseline import UserHealthBaseline
from app.models.health_profile import HealthProfile
from app.models.prescription import Prescription, PrescriptionStatus
from app.models.reminder import MedicationReminder
from app.models.user import User
from app.schemas.chatbot import ChatMessageResponse, ChatSendResponse, ChatSessionResponse, QuickSuggestion
from app.schemas.user import PaginatedResponse, PaginationMeta
from app.services.github_models_client import build_github_models_client

logger = logging.getLogger(__name__)

_CONTEXT_CACHE_TTL_SECONDS = 10 * 60

_QUICK_SUGGESTIONS = [
    QuickSuggestion(text="Thuốc này uống trước hay sau ăn?", category="drug_usage"),
    QuickSuggestion(text="Tôi bị đau đầu, nên làm gì?", category="symptom"),
    QuickSuggestion(text="Có thể dùng chung các thuốc này không?", category="interaction"),
    QuickSuggestion(text="Tác dụng phụ của thuốc này là gì?", category="drug_usage"),
    QuickSuggestion(text="Triệu chứng này có nguy hiểm không?", category="symptom"),
]

_UNAVAILABLE_REPLY = (
    "Hiện tại Medis AI chưa thể kết nối tới dịch vụ AI. "
    "Bạn vẫn có thể tiếp tục lưu câu hỏi trong lịch sử trò chuyện. "
    "Với vấn đề sức khỏe khẩn cấp như đau ngực, khó thở, ngất, co giật hoặc dị ứng nặng, "
    "hãy gọi cấp cứu hoặc đến cơ sở y tế gần nhất ngay. "
    "Thông tin này chỉ mang tính tham khảo, không thay thế khám bác sĩ."
)

_QUOTA_LIMIT_REPLY = (
    "Hiện tại Medis AI chưa thể phản hồi vì dịch vụ AI đang bị giới hạn quota. "
    "Câu hỏi của bạn vẫn được lưu trong lịch sử trò chuyện. "
    "Với vấn đề sức khỏe khẩn cấp như đau ngực, khó thở, ngất, co giật hoặc dị ứng nặng, "
    "hãy gọi cấp cứu hoặc đến cơ sở y tế gần nhất ngay. "
    "Thông tin này chỉ mang tính tham khảo, không thay thế khám bác sĩ."
)


def _fallback_reply_for_openai_error(exc: Exception) -> str:
    status_code = getattr(exc, "status_code", None)
    body = getattr(exc, "body", None)
    error_code = None
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            error_code = error.get("code")

    if status_code == 429 or error_code == "insufficient_quota":
        logger.warning("OpenAI quota unavailable: status=%s code=%s", status_code, error_code)
        return _QUOTA_LIMIT_REPLY

    logger.warning("OpenAI chatbot request unavailable: %s", exc)
    return _UNAVAILABLE_REPLY


def _loads_json_list(raw: Optional[str]) -> list[Any]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def build_system_prompt(context_data: dict) -> str:
    """Build the model system prompt from cached user context."""
    profile = context_data.get("profile", {})
    baseline = context_data.get("health_baseline", {})
    recent_visits = context_data.get("recent_visits", [])
    active_prescriptions = context_data.get("active_prescriptions", [])
    active_reminders = context_data.get("active_reminders", [])
    today_metrics = context_data.get("today_metrics", {})

    chronic_conditions = ", ".join(baseline.get("chronic_conditions") or []) or "Chưa cập nhật"
    allergies = baseline.get("allergies") or []
    allergy_text = "; ".join(
        f"{item.get('drug', 'Không rõ')}"
        + (f" ({item.get('reaction')})" if item.get("reaction") else "")
        for item in allergies
        if isinstance(item, dict)
    ) or "Chưa ghi nhận"
    current_medications = baseline.get("current_medications") or []
    current_medication_text = "; ".join(
        " ".join(filter(None, [
            item.get("name"),
            item.get("dosage"),
            item.get("frequency"),
        ]))
        for item in current_medications
        if isinstance(item, dict)
    ) or "Chưa cập nhật"
    visit_text = "\n".join(
        f"- {item.get('diagnosis_name')} ({item.get('exam_date')}): "
        f"{item.get('symptoms') or 'Không có triệu chứng mô tả'}"
        for item in recent_visits
    ) or "- Chưa có lịch sử khám gần đây"
    prescription_text = "\n".join(
        f"- {item.get('name')}: " + "; ".join(item.get("items") or [])
        for item in active_prescriptions
    ) or "- Không có đơn thuốc đang dùng"
    reminder_text = "; ".join(
        f"{item.get('drug_name')} lúc {item.get('reminder_time')}"
        for item in active_reminders
    ) or "Không có nhắc thuốc đang bật"

    return f"""Bạn là trợ lý sức khỏe cá nhân của Medis.

NGỮ CẢNH CÁ NHÂN CỦA USER:
- Họ tên: {profile.get('full_name') or profile.get('username') or 'Chưa cập nhật'}
- Tuổi: {profile.get('age') or 'N/A'}
- Giới tính: {profile.get('gender') or 'N/A'}
- Chiều cao: {baseline.get('height_cm') or 'N/A'} cm
- Cân nặng: {baseline.get('weight_kg') or 'N/A'} kg
- Nhóm máu: {baseline.get('blood_type') or 'N/A'}
- Bệnh nền: {chronic_conditions}
- Dị ứng: {allergy_text}
- Thuốc tự khai báo đang dùng: {current_medication_text}
- Calo đã nạp hôm nay: {today_metrics.get('calories_today', 'Chưa có dữ liệu trong hệ thống')}
- Bài tập gần đây: {today_metrics.get('recent_exercises', 'Chưa có dữ liệu trong hệ thống')}
- Nhắc thuốc đang bật: {reminder_text}

LỊCH SỬ KHÁM GẦN ĐÂY:
{visit_text}

ĐƠN THUỐC ĐANG DÙNG:
{prescription_text}

HƯỚNG DẪN TRẢ LỜI:
- Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu và có tính cá nhân hóa theo ngữ cảnh trên.
- Không bịa dữ liệu nếu ngữ cảnh chưa có; hãy nói rõ là hệ thống chưa có thông tin đó.
- Không chẩn đoán chính thức và không kê đơn bắt buộc. Nếu nói về thuốc, chỉ giải thích thông tin tham khảo.
- Luôn nhắc người dùng hỏi bác sĩ/dược sĩ khi có bệnh nền, dị ứng, thai kỳ, triệu chứng nặng hoặc dùng nhiều thuốc.
- Với dấu hiệu nguy hiểm như đau ngực, khó thở, ngất, co giật, yếu liệt, dị ứng nặng: khuyên đi cấp cứu ngay.
- Kết thúc bằng nhắc nhở: "Thông tin chỉ mang tính tham khảo, không thay thế tư vấn y tế chuyên môn" khi câu hỏi liên quan sức khỏe."""


def _calc_age(dob: Optional[datetime]) -> Optional[int]:
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _make_session_title(content: str) -> str:
    title = " ".join(content.strip().split())
    if not title:
        return "Cuộc trò chuyện mới"
    return title[:60]


class ChatbotService:
    def __init__(self, db: AsyncSession, redis: Optional[Redis] = None) -> None:
        self.db = db
        self.redis = redis
        self.client = build_github_models_client()

    async def _get_session(self, user_id: int, session_id: int) -> ChatSession:
        session = await self.db.scalar(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        if not session:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy phiên trò chuyện",
            )
        return session

    def _to_session_response(
        self,
        session: ChatSession,
        message_count: int = 0,
        last_message_preview: Optional[str] = None,
    ) -> ChatSessionResponse:
        return ChatSessionResponse(
            id=session.id,
            title=session.title,
            message_count=message_count,
            last_message_preview=last_message_preview,
            last_message=session.last_message,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_message_at=session.last_message_at,
        )

    async def create_session(
        self,
        user_id: int,
        title: Optional[str] = None,
    ) -> ChatSessionResponse:
        session = ChatSession(
            user_id=user_id,
            title=(title or "Cuộc trò chuyện mới").strip()[:200] or "Cuộc trò chuyện mới",
        )
        self.db.add(session)
        await self.db.flush()
        return self._to_session_response(session)

    async def list_sessions(self, user_id: int) -> list[ChatSessionResponse]:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(
                ChatSession.last_message_at.desc().nullslast(),
                ChatSession.updated_at.desc(),
                ChatSession.id.desc(),
            )
        )
        sessions = result.scalars().all()
        responses = []
        for session in sessions:
            count = await self.db.scalar(
                select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
            )
            preview = session.last_message
            responses.append(self._to_session_response(session, count or 0, preview))
        return responses

    async def _load_user_context_from_db(self, user_id: int) -> dict:
        """Load personalized user context from PostgreSQL on cache miss."""
        user = await self.db.scalar(select(User).where(User.id == user_id))
        age = _calc_age(user.date_of_birth) if user else None
        baseline = await self.db.scalar(
            select(UserHealthBaseline).where(UserHealthBaseline.user_id == user_id)
        )
        hp_rows = (
            await self.db.execute(
                select(HealthProfile)
                .where(HealthProfile.user_id == user_id)
                .order_by(HealthProfile.exam_date.desc())
                .limit(3)
            )
        ).scalars().all()
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
        reminder_rows = (
            await self.db.execute(
                select(MedicationReminder)
                .where(
                    MedicationReminder.user_id == user_id,
                    MedicationReminder.is_active == True,  # noqa: E712
                )
                .order_by(MedicationReminder.reminder_time.asc())
                .limit(10)
            )
        ).scalars().all()

        return {
            "profile": {
                "user_id": user.id if user else user_id,
                "username": user.username if user else None,
                "full_name": user.full_name if user else None,
                "age": age,
                "gender": user.gender if user else None,
                "occupation": user.occupation if user else None,
            },
            "health_baseline": {
                "height_cm": baseline.height_cm if baseline else None,
                "weight_kg": baseline.weight_kg if baseline else None,
                "blood_type": baseline.blood_type if baseline else None,
                "chronic_conditions": _loads_json_list(baseline.chronic_conditions if baseline else None),
                "allergies": _loads_json_list(baseline.allergies if baseline else None),
                "current_medications": _loads_json_list(baseline.current_medications if baseline else None),
                "is_pregnant": baseline.is_pregnant if baseline else False,
                "is_breastfeeding": baseline.is_breastfeeding if baseline else False,
                "kidney_function": getattr(baseline.kidney_function, "value", None) if baseline else None,
                "liver_function": getattr(baseline.liver_function, "value", None) if baseline else None,
                "health_goals": _loads_json_list(baseline.health_goals if baseline else None),
            },
            "recent_visits": [
                {
                    "diagnosis_name": hp.diagnosis_name,
                    "exam_date": hp.exam_date.isoformat(),
                    "symptoms": hp.symptoms,
                    "conclusion": hp.conclusion,
                    "facility": hp.facility,
                }
                for hp in hp_rows
            ],
            "active_prescriptions": [
                {
                    "id": prescription.id,
                    "name": prescription.name,
                    "items": [
                        " ".join(filter(None, [
                            item.drug_name,
                            item.dosage,
                            item.frequency,
                            item.duration,
                        ]))
                        for item in prescription.items
                    ],
                }
                for prescription in pres_rows
            ],
            "active_reminders": [
                {
                    "drug_name": reminder.drug_name,
                    "reminder_time": reminder.reminder_time.strftime("%H:%M"),
                    "frequency": reminder.frequency,
                }
                for reminder in reminder_rows
            ],
            "today_metrics": {
                "calories_today": None,
                "recent_exercises": None,
            },
        }

    async def load_user_context(self, user_id: int) -> dict:
        """Load user context with Redis cache.

        Cache key is scoped by user and current date to prevent repeated DB
        queries during active chat usage while still refreshing daily context.
        """
        today_key = date.today().isoformat()
        cache_key = f"chatbot:ctx:{user_id}:{today_key}"

        if self.redis is not None:
            # Reuse the daily context snapshot for 10 minutes so one active
            # chat session does not repeatedly query profile/prescription data.
            cached = await self.redis.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    await self.redis.delete(cache_key)

        context_data = await self._load_user_context_from_db(user_id)
        if self.redis is not None:
            # Store JSON only after a DB cache miss; default=str keeps dates
            # serializable without losing the simple dict shape for prompts.
            await self.redis.setex(
                cache_key,
                _CONTEXT_CACHE_TTL_SECONDS,
                json.dumps(context_data, ensure_ascii=False, default=str),
            )
        return context_data

    async def send_chat_message(
        self,
        user_id: int,
        session_id: Optional[int],
        message: str,
        db: Optional[AsyncSession] = None,
        redis: Optional[Redis] = None,
        request: Optional[Request] = None,
    ) -> ChatSendResponse:
        """Send a context-aware chat message through GitHub Models.

        The optional db/redis parameters keep this method easy to call from
        controllers or tests that follow a functional service style.
        """
        if db is not None:
            self.db = db
        if redis is not None:
            self.redis = redis

        content = message.strip()
        if session_id:
            session = await self._get_session(user_id, session_id)
        else:
            session = ChatSession(user_id=user_id, title=_make_session_title(content))
            self.db.add(session)
            await self.db.flush()

        previous_count = await self.db.scalar(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
        )
        if not previous_count:
            session.title = _make_session_title(content)

        context_data = await self.load_user_context(user_id)
        system_prompt = build_system_prompt(context_data)

        history_rows = (
            await self.db.execute(
                select(ChatMessage)
                .where(
                    ChatMessage.user_id == user_id,
                    ChatMessage.session_id == session.id,
                )
                .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
                .limit(20)
            )
        ).scalars().all()
        history_rows = list(reversed(history_rows))

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        # Convert persisted history into the OpenAI-compatible chat format.
        # The comprehension keeps only role/content so DB-only fields never
        # leak into the provider payload.
        messages.extend(
            [
                {
                    "role": row.role.value if hasattr(row.role, "value") else str(row.role),
                    "content": row.content,
                }
                for row in history_rows
            ]
        )
        messages.append({"role": "user", "content": content})

        if self.client is None:
            logger.warning("GitHub Models client is not configured; returning chatbot fallback")
            reply = _UNAVAILABLE_REPLY
        else:
            try:
                response = await self.client.chat.completions.create(
                    model=settings.GITHUB_MODELS_MODEL,
                    messages=messages,
                    max_tokens=800,
                    temperature=0.7,
                )
                reply = response.choices[0].message.content or _UNAVAILABLE_REPLY
            except Exception as exc:
                reply = _fallback_reply_for_openai_error(exc)

        now = datetime.now(timezone.utc)
        user_msg = ChatMessage(
            user_id=user_id,
            session_id=session.id,
            role="user",
            content=content,
            created_at=now,
        )
        assistant_msg = ChatMessage(
            user_id=user_id,
            session_id=session.id,
            role="assistant",
            content=reply,
            created_at=now,
        )
        self.db.add_all([user_msg, assistant_msg])
        session.last_message = reply
        session.last_message_at = now
        session.updated_at = now
        await self.db.flush()

        try:
            from app.services.log_service import ActivityLogService
            await ActivityLogService(self.db).log(
                "CHATBOT_MESSAGE", user_id=user_id, request=request
            )
        except Exception:
            logger.debug("Failed to write chatbot activity log", exc_info=True)

        message_count = (previous_count or 0) + 2
        return ChatSendResponse(
            session=self._to_session_response(session, message_count, reply),
            user_message=ChatMessageResponse.model_validate(user_msg),
            assistant_message=ChatMessageResponse.model_validate(assistant_msg),
        )

    async def send_message(
        self,
        user_id: int,
        content: str,
        session_id: Optional[int] = None,
        request: Optional[Request] = None,
    ) -> ChatSendResponse:
        return await self.send_chat_message(user_id, session_id, content, request=request)

    async def get_history(
        self,
        user_id: int,
        page: int,
        size: int,
        session_id: Optional[int] = None,
    ) -> PaginatedResponse:
        stmt = select(ChatMessage).where(ChatMessage.user_id == user_id)
        if session_id is not None:
            await self._get_session(user_id, session_id)
            stmt = stmt.where(ChatMessage.session_id == session_id)
        total = await self.db.scalar(
            select(func.count()).select_from(stmt.subquery())
        )
        rows = (
            await self.db.execute(
                stmt.order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
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

    async def delete_session(self, user_id: int, session_id: int) -> bool:
        session = await self._get_session(user_id, session_id)
        await self.db.delete(session)
        return True

    def get_quick_suggestions(self) -> List[QuickSuggestion]:
        return _QUICK_SUGGESTIONS


async def send_chat_message(
    user_id: int,
    session_id: Optional[int],
    message: str,
    db: AsyncSession,
    redis: Redis,
) -> ChatSendResponse:
    """Functional entry point for controllers/tests."""
    return await ChatbotService(db, redis).send_chat_message(user_id, session_id, message)
