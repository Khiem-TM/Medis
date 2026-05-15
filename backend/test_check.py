import asyncio
from app.database import AsyncSessionLocal
from app.redis_client import get_redis
from app.services.drug_service import InteractionService

async def main():
    async with AsyncSessionLocal() as db:
        redis = await get_redis()
        svc = InteractionService(db, redis)
        
        # Test 1 known pair and 1 unknown pair (if any)
        # Acetylsalicylicacid (DB00945) and Acenocoumarol (DB01418) - should be from DB
        # Wait, Acenocoumarol is DB01418.
        res = await svc.check_interactions(["DB00945", "DB01418"])
        print("Interactions found:", len(res.interactions))
        for ix in res.interactions:
            print(f"- {ix.drug_name} + {ix.interacts_with_name} -> {ix.interaction_label} (Source: {ix.source})")
            
        print("Prediction count:", res.prediction_count)

if __name__ == "__main__":
    asyncio.run(main())
