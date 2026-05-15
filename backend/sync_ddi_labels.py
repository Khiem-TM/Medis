#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_ddi_labels.py — Đồng bộ 65 nhãn tương tác từ DDI-MVP vào bảng drug_event_types
======================================================================================

Đọc labels từ ddi_mvp/models/label_map.json và insert/update vào PostgreSQL.

Cách dùng:
    cd backend/
    python sync_ddi_labels.py

Yêu cầu:
    - PostgreSQL đang chạy (docker-compose up -d postgres)
    - File .env đã cấu hình DATABASE_URL
    - File ddi_mvp/models/label_map.json tồn tại
"""

import asyncio
import json
import sys
from pathlib import Path

# ── Ensure backend app is importable ──
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, AsyncSessionLocal
from app.models.drug_event_type import DrugEventType


# ── Path to DDI-MVP label map ──
LABEL_MAP_PATH = Path(__file__).resolve().parent.parent / "ddi_mvp" / "models" / "label_map.json"


async def sync_labels():
    """Sync 65 DDI labels into drug_event_types table."""

    if not LABEL_MAP_PATH.exists():
        print(f"❌ Không tìm thấy file: {LABEL_MAP_PATH}")
        print("   Hãy chắc chắn ddi_mvp/models/label_map.json tồn tại.")
        sys.exit(1)

    with open(LABEL_MAP_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    id2label = meta["id2label"]  # {"0": "label_string", "1": "...", ...}
    num_classes = meta["num_classes"]

    print(f"📖 Đọc được {num_classes} nhãn tương tác từ label_map.json")
    print()

    async with AsyncSessionLocal() as session:
        # Lấy các event_type đã có
        existing_result = await session.execute(select(DrugEventType))
        existing_map = {et.event_name: et for et in existing_result.scalars().all()}

        created = 0
        skipped = 0

        for idx_str, label in sorted(id2label.items(), key=lambda x: int(x[0])):
            source_event_id = int(idx_str)

            if label in existing_map:
                # Update source_event_id nếu cần
                et = existing_map[label]
                if et.source_event_id != source_event_id:
                    et.source_event_id = source_event_id
                    print(f"  🔄 Updated source_event_id: [{source_event_id}] {label}")
                else:
                    skipped += 1
                continue

            new_et = DrugEventType(
                event_name=label,
                description=f"DDI interaction type (DDI-MVP class {source_event_id})",
                source_event_id=source_event_id,
            )
            session.add(new_et)
            created += 1
            print(f"  ✅ Created: [{source_event_id}] {label}")

        await session.commit()

    print()
    print(f"📊 Kết quả: {created} mới tạo | {skipped} đã tồn tại")
    print("✅ Đồng bộ hoàn tất!")


if __name__ == "__main__":
    asyncio.run(sync_labels())
