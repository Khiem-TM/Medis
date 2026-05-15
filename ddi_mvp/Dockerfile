# DDI-MVP Dockerfile
# Tối ưu cho inference (không cần GPU nếu chạy CPU)
FROM python:3.11-slim

WORKDIR /app

# Cài system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy runtime requirements trước để tận dụng Docker cache.
# Image inference không cần torch/transformers/scikit-learn/pandas dùng cho training.
COPY requirements-inference.txt .
RUN pip install --no-cache-dir -r requirements-inference.txt

# Copy source code
COPY api.py .
COPY inference.py .

# Models được mount qua volume, không copy vào image
# COPY models/ models/

EXPOSE 8000

# Uvicorn — 1 worker vì TensorFlow không fork-safe
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
