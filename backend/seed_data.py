"""
Seed script — populates 5 drugs, their products/warnings, and 3 interaction pairs.
Run from the backend/ directory:
    python seed_data.py
"""
import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.drug import Drug, DrugInteraction, DrugProduct, DrugWarning, InteractionSeverity


# ── Drug fixtures ──────────────────────────────────────────────────────────────

_NOW = datetime.now(timezone.utc)

DRUGS = [
    Drug(
        id="DB00945",
        name="Aspirin",
        atc_code="B01AC06",
        dosage_form="Tablet",
        description="Aspirin (acetylsalicylic acid) is a salicylate drug used to reduce pain, fever, and inflammation.",
        classification="Antiplatelet / NSAID",
        updated_at=_NOW,
    ),
    Drug(
        id="DB00682",
        name="Warfarin",
        atc_code="B01AA03",
        dosage_form="Tablet",
        description="Warfarin is an anticoagulant used to prevent thrombosis and embolism.",
        classification="Anticoagulant",
        updated_at=_NOW,
    ),
    Drug(
        id="DB01050",
        name="Ibuprofen",
        atc_code="M01AE01",
        dosage_form="Tablet",
        description="Ibuprofen is a non-steroidal anti-inflammatory drug (NSAID) used for pain and fever.",
        classification="NSAID",
        updated_at=_NOW,
    ),
    Drug(
        id="DB00316",
        name="Paracetamol",
        atc_code="N02BE01",
        dosage_form="Tablet",
        description="Paracetamol (acetaminophen) is an analgesic and antipyretic widely used for mild-to-moderate pain.",
        classification="Analgesic / Antipyretic",
        updated_at=_NOW,
    ),
    Drug(
        id="DB00415",
        name="Amoxicillin",
        atc_code="J01CA04",
        dosage_form="Capsule",
        description="Amoxicillin is a broad-spectrum beta-lactam antibiotic used to treat bacterial infections.",
        classification="Antibiotic / Beta-lactam",
        updated_at=_NOW,
    ),
]

PRODUCTS = [
    # Aspirin
    DrugProduct(drug_id="DB00945", trade_name="Aspirin 100mg", route="Oral", dosage="100 mg", formulation="Tablet", origin="Germany"),
    DrugProduct(drug_id="DB00945", trade_name="Aspirin 500mg", route="Oral", dosage="500 mg", formulation="Tablet", origin="Germany"),
    # Warfarin
    DrugProduct(drug_id="DB00682", trade_name="Coumadin 2mg", route="Oral", dosage="2 mg", formulation="Tablet", origin="USA"),
    DrugProduct(drug_id="DB00682", trade_name="Coumadin 5mg", route="Oral", dosage="5 mg", formulation="Tablet", origin="USA"),
    # Ibuprofen
    DrugProduct(drug_id="DB01050", trade_name="Advil 200mg", route="Oral", dosage="200 mg", formulation="Tablet", origin="USA"),
    DrugProduct(drug_id="DB01050", trade_name="Brufen 400mg", route="Oral", dosage="400 mg", formulation="Tablet", origin="UK"),
    # Paracetamol
    DrugProduct(drug_id="DB00316", trade_name="Panadol 500mg", route="Oral", dosage="500 mg", formulation="Tablet", origin="UK"),
    DrugProduct(drug_id="DB00316", trade_name="Tylenol 500mg", route="Oral", dosage="500 mg", formulation="Tablet", origin="USA"),
    # Amoxicillin
    DrugProduct(drug_id="DB00415", trade_name="Amoxil 250mg", route="Oral", dosage="250 mg", formulation="Capsule", origin="USA"),
    DrugProduct(drug_id="DB00415", trade_name="Amoxil 500mg", route="Oral", dosage="500 mg", formulation="Capsule", origin="USA"),
]

WARNINGS = [
    DrugWarning(drug_id="DB00945", warning_text="Không dùng cho trẻ em dưới 12 tuổi do nguy cơ hội chứng Reye."),
    DrugWarning(drug_id="DB00945", warning_text="Thận trọng khi dùng cùng thuốc chống đông máu."),
    DrugWarning(drug_id="DB00682", warning_text="Theo dõi INR thường xuyên khi dùng Warfarin."),
    DrugWarning(drug_id="DB00682", warning_text="Nhiều thuốc và thực phẩm ảnh hưởng đến tác dụng của Warfarin."),
    DrugWarning(drug_id="DB01050", warning_text="Không dùng trong 3 tháng cuối thai kỳ."),
    DrugWarning(drug_id="DB01050", warning_text="Có thể gây loét dạ dày nếu dùng dài ngày."),
    DrugWarning(drug_id="DB00316", warning_text="Không vượt quá 4g/ngày — nguy cơ tổn thương gan."),
    DrugWarning(drug_id="DB00316", warning_text="Thận trọng ở bệnh nhân suy gan hoặc nghiện rượu."),
    DrugWarning(drug_id="DB00415", warning_text="Thận trọng ở bệnh nhân dị ứng với penicillin."),
    DrugWarning(drug_id="DB00415", warning_text="Sử dụng kháng sinh đúng liều để tránh kháng thuốc."),
]

INTERACTIONS = [
    DrugInteraction(
        drug_id_1="DB00682",  # Warfarin
        drug_id_2="DB00945",  # Aspirin  (min < max lexicographically)
        interaction_type="Pharmacodynamic",
        severity=InteractionSeverity.major,
        description=(
            "Aspirin ức chế kết tập tiểu cầu và có thể làm giảm nồng độ albumin gắn Warfarin, "
            "làm tăng nguy cơ chảy máu nghiêm trọng."
        ),
        recommendation=(
            "Tránh phối hợp nếu không có chỉ định rõ ràng. "
            "Nếu bắt buộc, theo dõi INR chặt chẽ và điều chỉnh liều Warfarin."
        ),
    ),
    DrugInteraction(
        drug_id_1="DB00682",  # Warfarin
        drug_id_2="DB01050",  # Ibuprofen
        interaction_type="Pharmacodynamic",
        severity=InteractionSeverity.major,
        description=(
            "Ibuprofen ức chế tổng hợp prostaglandin bảo vệ niêm mạc dạ dày và kết tập tiểu cầu, "
            "làm tăng nguy cơ chảy máu tiêu hoá ở bệnh nhân dùng Warfarin."
        ),
        recommendation=(
            "Ưu tiên dùng Paracetamol thay thế. "
            "Nếu cần NSAIDs, theo dõi INR và triệu chứng chảy máu tiêu hoá."
        ),
    ),
    DrugInteraction(
        drug_id_1="DB00945",  # Aspirin
        drug_id_2="DB01050",  # Ibuprofen
        interaction_type="Pharmacodynamic",
        severity=InteractionSeverity.moderate,
        description=(
            "Ibuprofen có thể cạnh tranh với Aspirin tại vị trí gắn COX-1 trên tiểu cầu, "
            "làm giảm tác dụng chống kết tập tiểu cầu của liều thấp Aspirin."
        ),
        recommendation=(
            "Nếu dùng Aspirin liều thấp để bảo vệ tim mạch, uống Aspirin ít nhất 30 phút "
            "trước Ibuprofen hoặc lựa chọn thuốc giảm đau thay thế."
        ),
    ),
]


# ── Seed runner ────────────────────────────────────────────────────────────────

async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # Drugs
        for drug in DRUGS:
            existing = await db.scalar(select(Drug).where(Drug.id == drug.id))
            if not existing:
                db.add(drug)
                print(f"  + Drug {drug.id} — {drug.name}")
            else:
                print(f"  ~ Drug {drug.id} — {drug.name} (already exists, skipped)")

        await db.flush()

        # Products
        for product in PRODUCTS:
            db.add(product)
        print(f"  + {len(PRODUCTS)} DrugProducts added")

        # Warnings
        for warning in WARNINGS:
            db.add(warning)
        print(f"  + {len(WARNINGS)} DrugWarnings added")

        # Interactions (normalize key order)
        for interaction in INTERACTIONS:
            d1, d2 = sorted([interaction.drug_id_1, interaction.drug_id_2])
            from sqlalchemy import and_
            existing = await db.scalar(
                select(DrugInteraction).where(
                    and_(DrugInteraction.drug_id_1 == d1, DrugInteraction.drug_id_2 == d2)
                )
            )
            if not existing:
                interaction.drug_id_1 = d1
                interaction.drug_id_2 = d2
                db.add(interaction)
                print(f"  + Interaction {d1} ↔ {d2} ({interaction.severity.value})")
            else:
                print(f"  ~ Interaction {d1} ↔ {d2} (already exists, skipped)")

        await db.commit()
        print("\nSeed completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
