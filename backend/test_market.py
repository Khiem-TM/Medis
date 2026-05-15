import asyncio
from app.database import AsyncSessionLocal
from app.redis_client import get_redis_pool
from redis.asyncio import Redis
from app.services.market_drug_service import MarketDrugService

async def main():
    async with AsyncSessionLocal() as db:
        pool = get_redis_pool()
        redis = Redis(connection_pool=pool)
        
        svc = MarketDrugService(db)
        
        res = await svc.check_market_product_interactions([2, 6], redis)
        print("Unmapped:", res.unmapped_products)
        if res.ddi_result:
            print("Interactions found:", len(res.ddi_result.get("interactions", [])))
            for ix in res.ddi_result.get("interactions", []):
                print(f"- {ix.get('drug_name')} + {ix.get('interacts_with_name')} -> {ix.get('interaction_label')}")
        else:
            print("No DDI result.")
            
        await redis.close()

if __name__ == "__main__":
    asyncio.run(main())
