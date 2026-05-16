import json
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models.health_baseline import UserHealthBaseline, KidneyFunction, LiverFunction
from app.models.user import User
from app.schemas.onboarding import (
    OnboardingStep1Request, OnboardingStep2Request, OnboardingStep3Request,
    HealthBaselineResponse, ParsedConditionsResponse, AllergyItem, MedicationItem
)
from app.services.openai_client import build_async_openai_client

logger = logging.getLogger(__name__)


class OnboardingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.client = None

    async def _get_or_create_baseline(self, user_id: int) -> UserHealthBaseline:
        result = await self.db.execute(
            select(UserHealthBaseline).where(UserHealthBaseline.user_id == user_id)
        )
        baseline = result.scalar_one_or_none()
        if not baseline:
            baseline = UserHealthBaseline(user_id=user_id)
            self.db.add(baseline)
            await self.db.flush()
        return baseline

    async def get_status(self, user_id: int) -> HealthBaselineResponse:
        baseline = await self._get_or_create_baseline(user_id)
        await self.db.commit()
        await self.db.refresh(baseline)
        return HealthBaselineResponse.model_validate(baseline)

    async def save_step1(self, user_id: int, data: OnboardingStep1Request) -> HealthBaselineResponse:
        baseline = await self._get_or_create_baseline(user_id)
        if data.height_cm is not None:
            baseline.height_cm = data.height_cm
        if data.weight_kg is not None:
            baseline.weight_kg = data.weight_kg
        if data.blood_type is not None:
            baseline.blood_type = data.blood_type
        baseline.is_pregnant = data.is_pregnant
        baseline.is_breastfeeding = data.is_breastfeeding
        try:
            baseline.kidney_function = KidneyFunction(data.kidney_function)
        except ValueError:
            baseline.kidney_function = KidneyFunction.normal
        try:
            baseline.liver_function = LiverFunction(data.liver_function)
        except ValueError:
            baseline.liver_function = LiverFunction.normal
        baseline.onboarding_step = max(baseline.onboarding_step, 1)
        await self.db.commit()
        await self.db.refresh(baseline)
        return HealthBaselineResponse.model_validate(baseline)

    async def parse_conditions_with_ai(self, text: str) -> ParsedConditionsResponse:
        """Use GPT-4o-mini to parse Vietnamese free text into structured data."""
        try:
            client = self.client or build_async_openai_client()
            self.client = client
            if client is None:
                logger.warning("OpenAI API key is not configured; skipping onboarding AI parsing")
                return ParsedConditionsResponse(raw_text=text)

            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Bạn là dược sĩ lâm sàng. Phân tích văn bản tiếng Việt về sức khỏe người dùng. "
                            "Trả về JSON với format sau:\n"
                            '{"conditions": ["tên bệnh 1", "tên bệnh 2"], '
                            '"allergies": [{"drug": "tên thuốc", "reaction": "phản ứng nếu có"}], '
                            '"medications": [{"name": "tên thuốc", "dosage": "liều lượng nếu có", "frequency": "tần suất nếu có"}]}\n'
                            "Chuẩn hóa tên bệnh sang tiếng Anh chuẩn y khoa (ví dụ: tiểu đường → Diabetes Mellitus Type 2). "
                            "Nếu không rõ, để mảng rỗng."
                        ),
                    },
                    {"role": "user", "content": f"Văn bản sức khỏe: {text}"},
                ],
                temperature=0.1,
                max_tokens=600,
            )
            raw = json.loads(response.choices[0].message.content)
            return ParsedConditionsResponse(
                conditions=raw.get("conditions", []),
                allergies=[AllergyItem(**a) if isinstance(a, dict) else AllergyItem(drug=a) for a in raw.get("allergies", [])],
                medications=[MedicationItem(**m) if isinstance(m, dict) else MedicationItem(name=m) for m in raw.get("medications", [])],
                raw_text=text,
            )
        except Exception as e:
            logger.warning(f"AI parsing failed, returning empty: {e}")
            return ParsedConditionsResponse(raw_text=text)

    async def save_step2(self, user_id: int, data: OnboardingStep2Request) -> HealthBaselineResponse:
        baseline = await self._get_or_create_baseline(user_id)

        conditions = data.conditions or []
        allergies = data.allergies or []

        # AI parse free text if provided
        if data.conditions_text or data.allergies_text:
            combined_text = " ".join(filter(None, [data.conditions_text, data.allergies_text]))
            parsed = await self.parse_conditions_with_ai(combined_text)
            if not conditions:
                conditions = parsed.conditions
            if not allergies:
                allergies = parsed.allergies

        baseline.chronic_conditions = json.dumps(conditions, ensure_ascii=False)
        baseline.allergies = json.dumps(
            [a.model_dump() for a in allergies], ensure_ascii=False
        )
        baseline.onboarding_step = max(baseline.onboarding_step, 2)
        await self.db.commit()
        await self.db.refresh(baseline)
        return HealthBaselineResponse.model_validate(baseline)

    async def save_step3(self, user_id: int, data: OnboardingStep3Request) -> HealthBaselineResponse:
        baseline = await self._get_or_create_baseline(user_id)

        medications = data.medications or []
        goals = data.health_goals or []

        if data.medications_text and not medications:
            parsed = await self.parse_conditions_with_ai(data.medications_text)
            medications = parsed.medications

        baseline.current_medications = json.dumps(
            [m.model_dump() for m in medications], ensure_ascii=False
        )
        baseline.health_goals = json.dumps(goals, ensure_ascii=False)
        baseline.onboarding_step = 3
        baseline.onboarding_completed = True
        await self.db.commit()
        await self.db.refresh(baseline)
        return HealthBaselineResponse.model_validate(baseline)
