# DDI-MVP — Drug Interaction Prediction API

Hệ thống dự đoán tương tác thuốc kết hợp:
- **Feature pipeline** từ `feature_processing.py`: ChemBERTa SMILES + Jaccard+PCA (target / enzyme / pathway) → vector 1024d/drug, pair embedding 4096d
- **Model** từ `DDIMLD_v2.ipynb`: **ModernDDIMDL** — Feature Projection → Residual Blocks → Multi-Head Attention → 65-class classifier

---

## Kiến trúc tổng quan

```
Đơn thuốc [Drug1, Drug2, ..., DrugN]
           │
           ▼
  Tạo tất cả cặp (C(N,2))
           │
           ▼
  Drug2Vec lookup
  ┌─────────────────────────────────┐
  │ SMILES  → ChemBERTa → 768d      │
  │ Target  → Jaccard+PCA → 128d    │  → concat → 1024d/drug
  │ Enzyme  → Jaccard+PCA →  64d    │
  │ Pathway → Jaccard+PCA →  64d    │
  └─────────────────────────────────┘
           │
           ▼
  Pair Embedding: [v1 ‖ v2 ‖ |v1-v2| ‖ v1·v2] = 4096d
           │
           ▼
  ModernDDIMDL
  ┌─────────────────────────────────┐
  │ Dense(1024) → BN → Dropout(0.4) │
  │ Dense(512) → BN                 │
  │ ResidualBlock(512) × 2          │
  │ MultiHeadAttention(4 heads)     │
  │ Dense(256) → BN → Dropout(0.3)  │
  │ Dense(65, softmax)              │
  └─────────────────────────────────┘
           │
           ▼
  65 nhãn tương tác + confidence score
```

---

## Cài đặt

```bash
# 1. Clone / copy project
cd ddi_mvp/

# 2. Tạo virtual environment
python -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# 3. Cài dependencies
pip install -r requirements.txt
```

---

## Bước 1: Training (đã train có folder models, không cần train lại)

```bash
python train.py --db path/to/event.db --output models/
```

**Tham số:**

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `--db` | `event.db` | Đường dẫn tới SQLite database |
| `--output` | `models/` | Thư mục lưu artifacts |
| `--epochs` | `100` | Số epoch tối đa (EarlyStopping tự dừng) |
| `--batch_size` | `128` | Batch size |

**Artifacts đầu ra** (`models/`):

| File | Mô tả |
|---|---|
| `ModernDDIMDL.keras` | Model weights |
| `drug2vec.pkl` | Dict `{drug_name: np.array(1024)}` |
| `pca_objects.pkl` | PCA objects (dùng khi thêm drug mới) |
| `label_map.json` | Mapping nhãn ↔ index |

---

## Bước 2: Chạy API

```bash
# Development
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Production (1 worker do TensorFlow không fork-safe)
gunicorn api:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Biến môi trường:**

| Biến | Mặc định | Mô tả |
|---|---|---|
| `MODEL_DIR` | `models/` | Thư mục chứa artifacts |
| `DDI_THRESHOLD` | `0.40` | Confidence threshold mặc định |
| `LOG_LEVEL` | `INFO` | Log level |

---

## API Reference

### `POST /api/predict` — Dự đoán đơn thuốc

**Request:**
```json
{
  "drugs": ["Aspirin", "Warfarin", "Ibuprofen"],
  "threshold": 0.40
}
```

> `threshold` optional (0.0–1.0). Tăng lên để giảm false positive, giảm để nhạy hơn.

**Response:**
```json
{
  "has_interaction": true,
  "total_pairs_checked": 3,
  "unknown_drugs": [],
  "interactions": [
    {
      "drug_a": "Warfarin",
      "drug_b": "Aspirin",
      "label": "the metabolism of Warfarin can be decreased",
      "confidence": 0.7823,
      "top3_predictions": [
        { "label": "the metabolism of Warfarin can be decreased", "confidence": 0.7823 },
        { "label": "the anticoagulant activities increase",         "confidence": 0.1204 },
        { "label": "the serum concentration of Warfarin increase",  "confidence": 0.0512 }
      ]
    },
    ...
  ]
}
```

**Trường quan trọng:**

| Trường | Kiểu | Mô tả |
|---|---|---|
| `has_interaction` | bool | `true` nếu có ≥1 cặp vượt ngưỡng |
| `total_pairs_checked` | int | Tổng số cặp được kiểm tra (C(N,2)) |
| `unknown_drugs` | list | Thuốc không có trong database |
| `interactions[].label` | string | Nhãn tương tác (1 trong 65 loại) |
| `interactions[].confidence` | float | Độ tin cậy (max softmax, 0–1) |
| `interactions[].top3_predictions` | list | Top 3 dự đoán kèm confidence |

---

### `POST /api/predict/pair` — Dự đoán cặp thuốc

**Request:**
```json
{ "drug_a": "Warfarin", "drug_b": "Aspirin" }
```

**Response:**
```json
{
  "drug_a": "Warfarin",
  "drug_b": "Aspirin",
  "predicted_label": "the metabolism of Warfarin can be decreased",
  "confidence": 0.7823,
  "has_significant_interaction": true,
  "all_predictions": [
    { "rank": 1, "label": "...", "confidence": 0.7823 },
    ...
  ]
}
```

---

### `GET /api/drugs/search?q=<keyword>` — Tìm kiếm thuốc

```
GET /api/drugs/search?q=warfarin&limit=10
```

Dùng cho **autocomplete** ở frontend. Case-insensitive substring match.

**Response:**
```json
{
  "query": "warfarin",
  "total_matches": 2,
  "results": ["Warfarin", "Warfarin sodium"]
}
```

---

### `GET /api/labels` — Danh sách 65 nhãn

```
GET /api/labels
```

**Response:**
```json
{
  "total": 65,
  "labels": [
    { "id": 0, "label": "the metabolism of ... can be decreased" },
    { "id": 1, "label": "the serum concentration of ... increase" },
    ...
  ]
}
```

---

### `GET /health` — Health check

```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "num_known_drugs": 572,
  "num_classes": 65,
  "threshold": 0.4
}
```

---

## Tích hợp Frontend (JavaScript)

```javascript
// Kiểm tra đơn thuốc
const checkPrescription = async (drugs) => {
  const res = await fetch('http://localhost:8000/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ drugs, threshold: 0.40 }),
  });
  return res.json();
};

// Autocomplete tìm thuốc
const searchDrugs = async (query) => {
  const res = await fetch(
    `http://localhost:8000/api/drugs/search?q=${encodeURIComponent(query)}`
  );
  return res.json();
};

// Ví dụ sử dụng
const result = await checkPrescription(["Aspirin", "Warfarin", "Ibuprofen"]);

if (result.has_interaction) {
  result.interactions.forEach(({ drug_a, drug_b, label, confidence }) => {
    console.log(`⚠️  ${drug_a} + ${drug_b}: ${label} (${(confidence*100).toFixed(1)}%)`);
  });
} else {
  console.log("✅ Không phát hiện tương tác đáng chú ý.");
}

// Cảnh báo thuốc không tìm thấy
if (result.unknown_drugs.length > 0) {
  console.warn("Không tìm thấy trong database:", result.unknown_drugs);
}
```

---

## Lưu ý cho Dev

### Confidence Threshold

Model được train để phân loại **loại** tương tác (không phải có/không). Ngưỡng 0.40 được chọn để cân bằng precision/recall. Điều chỉnh theo nhu cầu:

- **0.60+**: Chỉ hiển thị tương tác rất chắc chắn (ít false positive)
- **0.40** (mặc định): Cân bằng
- **0.20**: Cảnh báo rộng hơn (nhiều gợi ý hơn)

### Unknown Drugs

Nếu người dùng nhập tên thuốc không có trong database:
- Trường `unknown_drugs` sẽ liệt kê chúng
- Những thuốc đó bị bỏ qua khi tính cặp
- Nên hiển thị cảnh báo ở UI và gợi ý dùng `/api/drugs/search`

### Tên thuốc

Tên thuốc **case-sensitive** và phải khớp chính xác với tên trong training data (thường là tên thương mại hoặc INN). Luôn dùng `/api/drugs/search` để validate trước.

---

## Cấu trúc project

```
ddi_mvp/
├── train.py          # Training pipeline
├── inference.py      # DDIPredictor class
├── api.py            # FastAPI server
├── requirements.txt  # Dependencies
├── README.md         # Tài liệu này
└── models/           # (tự tạo sau khi train)
    ├── ModernDDIMDL.keras
    ├── drug2vec.pkl
    ├── pca_objects.pkl
    └── label_map.json
```
