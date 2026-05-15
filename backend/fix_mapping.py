import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.drug import Drug
from app.models.market_drug import MarketDrugProductIngredient

async def main():
    async with AsyncSessionLocal() as db:
        drugs_result = await db.execute(select(Drug))
        drug_map = {d.generic_name.lower(): d.id for d in drugs_result.scalars().all()}
        
        ingredients_result = await db.execute(select(MarketDrugProductIngredient).where(MarketDrugProductIngredient.ddi_drug_id == None))
        ingredients = ingredients_result.scalars().all()
        
        mapped = 0
        for ing in ingredients:
            if ing.ingredient_name_normalized:
                norm = ing.ingredient_name_normalized.lower()
                for drug_name, d_id in drug_map.items():
                    if len(drug_name) > 3 and drug_name in norm:
                        ing.ddi_drug_id = d_id
                        ing.mapping_confidence = 80
                        mapped += 1
                        break
        
        await db.commit()
        print(f"Mapped {mapped}/{len(ingredients)} previously unmapped ingredients.")

if __name__ == "__main__":
    asyncio.run(main())
