import asyncio
import sqlite3
import sys
from pathlib import Path

# ── Ensure backend app is importable ──
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.database import engine, AsyncSessionLocal
from app.models.drug import Drug, DrugInteraction, InteractionSource
from app.models.market_drug import MarketDrugProductIngredient

# ── Paths ──
DDI_DB_PATH = Path(__file__).resolve().parent.parent / "ddi_mvp" / "event.db"

async def sync_drugs_and_interactions():
    if not DDI_DB_PATH.exists():
        print(f"❌ Không tìm thấy file: {DDI_DB_PATH}")
        sys.exit(1)

    print("📖 Đang đọc dữ liệu từ event.db (SQLite)...")
    
    # Kết nối SQLite
    conn = sqlite3.connect(DDI_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Đọc danh sách thuốc
    cursor.execute("SELECT id, name, smile FROM drug")
    drugs_rows = cursor.fetchall()

    # Đọc danh sách tương tác
    cursor.execute("SELECT id1, name1, id2, name2, interaction FROM event")
    event_rows = cursor.fetchall()
    conn.close()

    print(f"📦 Đã lấy {len(drugs_rows)} thuốc và {len(event_rows)} bản ghi tương tác.")

    async with AsyncSessionLocal() as session:
        # 1. Sync Drugs
        print("🔄 Đang đồng bộ bảng drugs...")
        created_drugs = 0
        
        for row in drugs_rows:
            drug_id = row["id"]
            generic_name = row["name"]
            smile = row["smile"]

            stmt = insert(Drug).values(
                id=drug_id,
                generic_name=generic_name
            ).on_conflict_do_nothing(index_elements=["id"])
            
            result = await session.execute(stmt)
            if result.rowcount > 0:
                created_drugs += 1
        
        await session.commit()
        print(f"✅ Đã thêm mới {created_drugs} loại thuốc.")

        # 2. Sync Drug Interactions
        print("🔄 Đang đồng bộ bảng drug_interactions...")
        
        interaction_values = []
        for row in event_rows:
            interaction_values.append({
                "drug_id": row["id1"],
                "interacts_with_id": row["id2"],
                "interacts_with_name": row["name2"],
                "interaction_label": row["interaction"],
                "source": InteractionSource.database,
                "confidence_score": 1.0
            })
            
        chunk_size = 5000
        created_interactions = 0
        for i in range(0, len(interaction_values), chunk_size):
            chunk = interaction_values[i:i+chunk_size]
            stmt = insert(DrugInteraction).values(chunk).on_conflict_do_nothing(
                index_elements=["drug_id", "interacts_with_id"]
            )
            result = await session.execute(stmt)
            created_interactions += result.rowcount
            await session.commit()

        print(f"✅ Đã thêm mới {created_interactions} tương tác.")

        # 3. Map MarketDrugProductIngredient to Drug
        print("🔄 Đang ánh xạ MarketDrugProductIngredient với Drug...")
        
        ingredients_result = await session.execute(
            select(MarketDrugProductIngredient).where(MarketDrugProductIngredient.ddi_drug_id == None)
        )
        ingredients = ingredients_result.scalars().all()
        
        drugs_result = await session.execute(select(Drug))
        all_drugs = drugs_result.scalars().all()
        drug_map = {d.generic_name.lower(): d.id for d in all_drugs}
        
        mapped_count = 0
        for ing in ingredients:
            if ing.ingredient_name_normalized:
                norm_name = ing.ingredient_name_normalized.lower()
                if norm_name in drug_map:
                    ing.ddi_drug_id = drug_map[norm_name]
                    ing.mapping_confidence = 100
                    mapped_count += 1
        
        await session.commit()
        print(f"✅ Đã ánh xạ {mapped_count}/{len(ingredients)} thành phần thuốc thương mại.")

if __name__ == "__main__":
    asyncio.run(sync_drugs_and_interactions())
