import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.main import app

spec = app.openapi()
with open("openapi.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)

paths = spec["paths"]
total_ops = sum(len(v) for v in paths.values())

tags: dict[str, int] = {}
for path, methods in paths.items():
    for method, op in methods.items():
        for tag in op.get("tags", ["untagged"]):
            tags[tag] = tags.get(tag, 0) + 1

print(f"✅ openapi.json đã được tạo")
print(f"📁 Tổng paths: {len(paths)}")
print(f"🔢 Tổng operations: {total_ops}")
print("\n📋 Operations theo module:")
for tag, count in sorted(tags.items()):
    print(f"  {tag}: {count} endpoints")
