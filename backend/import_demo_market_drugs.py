#!/usr/bin/env python3
from __future__ import annotations

import asyncio

from app.database import AsyncSessionLocal
from app.services.market_drug_service import MarketDrugService


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await MarketDrugService(db).import_demo_products(limit_per_term=2)
        await db.commit()
        print(f"Imported: {result.imported_count} | Updated: {result.updated_count} | Mapped ingredients: {result.mapped_ingredients}")
        for item in result.imported_products:
            print(f"- #{item.id} {item.product_name} [{item.registration_number}] -> {', '.join(item.resolved_drug_ids) or 'no-ddi-map'}")


if __name__ == "__main__":
    asyncio.run(main())
