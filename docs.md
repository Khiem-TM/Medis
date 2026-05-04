# Di vào thư mục backend

cd /Users/UET/VDHD/Medis/backend

# Activate virtual environment

source venv/bin/activate

# Chạy server (development)

source venv/bin/activate
uvicorn app.main:app --reload
Lưu ý: Dùng --reload khi dev để server tự restart khi thay đổi code. Khi Postgres.app hiện dialog xin quyền kết nối → click Allow.

Các lệnh hữu ích khác:

# Chạy tests

python test/test_e2e_full.py

# Migration DB

alembic upgrade head

# Seed data

python seed_data.py
