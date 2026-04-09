ok guys

Workflow Alembic khi update Table

# 1. Thêm/sửa model trong app/models/

# 2. Tạo migration mới:

alembic revision --autogenerate -m "add_prescriptions_table"

# 3. Chạy:

alembic upgrade head

# 4. Rollback nếu cần:

alembic downgrade -1

Schemas tương đương DTO trong NestJS
