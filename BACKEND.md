# Medis Backend - Tài liệu Tổng hợp

## 1. Tech Stack

| Thanh phan | Cong nghe |
|-----------|-----------|
| Framework | FastAPI 0.135.3 (async) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL (asyncpg driver) |
| Cache | Redis 7.4.0 |
| Auth | JWT (python-jose) + bcrypt + Google OAuth 2.0 |
| AI | OpenAI GPT-4o-mini |
| Email | FastAPI-Mail (SMTP Gmail) |
| Migrations | Alembic |
| Export | OpenPyXL (Excel .xlsx) |
| Validation | Pydantic v2 |

---

## 2. Cau truc thu muc

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── auth.py            # Auth routes
│   │   ├── users.py           # User, Prescription, HealthProfile routes
│   │   ├── drugs.py           # Drug search & interaction routes
│   │   ├── chatbot.py         # AI chatbot routes
│   │   ├── recommendations.py # AI recommendation routes
│   │   ├── activity.py        # Activity log routes
│   │   ├── admin.py           # Admin routes
│   │   └── __init__.py        # Router registration
│   ├── api/deps.py            # Auth dependencies
│   ├── models/                # SQLAlchemy ORM models
│   ├── schemas/               # Pydantic schemas (tuong duong DTO)
│   ├── services/              # Business logic
│   ├── core/
│   │   ├── security.py        # JWT, password hashing
│   │   └── middleware.py      # Activity logging middleware
│   ├── main.py                # App entry point
│   ├── config.py              # Settings from .env
│   ├── database.py            # SQLAlchemy async setup
│   └── redis_client.py        # Redis connection pool
├── migrations/                # Alembic migration files
├── test/                      # Test suite
├── seed_data.py               # DB seeding script
└── requirements.txt
```

---

## 3. Database Models

### User (`users`)
- `id` UUID PK, `username` (unique), `email` (unique), `password_hash` (nullable - Google users)
- `full_name`, `phone`, `date_of_birth`, `gender`, `address`, `occupation`, `avatar_url`
- `auth_provider` (local/google), `google_id`, `role` (user/admin), `is_active`
- Relations: prescriptions, health_profiles, activity_logs, chat_messages

### Prescription (`prescriptions`)
- `id` UUID, `user_id` FK, `name`, `status` (active/completed), `notes`
- Has many: `PrescriptionItem`

### PrescriptionItem (`prescription_items`)
- `prescription_id` FK, `drug_id` FK nullable (OCR-friendly), `drug_name` (luon luu ten)
- `dosage`, `frequency`, `duration`

### HealthProfile (`health_profiles`)
- `user_id` FK, `diagnosis_name`, `exam_date`, `facility`, `doctor`
- `symptoms`, `conclusion`, `notes`
- `prescription_id` FK nullable (lien ket don thuoc)

### Drug (`drugs`)
- `id` String PK (khong phai UUID), `name`, `atc_code`, `description`, `dosage_form`, `classification`
- Has many: `DrugProduct`, `DrugWarning`, `DrugInteraction`

### DrugProduct (`drug_products`)
- `drug_id` FK, `trade_name`, `route`, `dosage`, `formulation`, `origin`

### DrugWarning (`drug_warnings`)
- `drug_id` FK, `warning_text`

### DrugInteraction (`drug_interactions`)
- `drug_id_1`, `drug_id_2` FK (QUAN TRONG: drug_id_1 < drug_id_2 lexicographic de tranh duplicate)
- `interaction_type`, `severity` (minor/moderate/major), `description`, `recommendation`

### ChatMessage (`chat_messages`)
- `user_id` FK, `role` (user/assistant), `content` Text, `created_at`

### ActivityLog (`activity_logs`)
- `user_id` FK nullable, `action`, `entity_type`, `entity_id`, `detail` JSON, `ip_address`, `user_agent`
- Actions: LOGIN, LOGOUT, REGISTER, DRUG_SEARCH, INTERACTION_CHECK, PRESCRIPTION_CREATE/UPDATE/DELETE/VIEW, HEALTH_PROFILE_CREATE/UPDATE/DELETE/VIEW, CHATBOT_MESSAGE, PROFILE_UPDATE, PASSWORD_CHANGE

### SystemLog (`system_logs`)
- `level` (DEBUG/INFO/WARNING/ERROR/CRITICAL), `source`, `message`, `detail` JSON

---

## 4. Authentication Flow

```
Register:
  POST /auth/register → tao user (is_active=False) → gui email → luu token Redis 24h
  GET  /auth/verify-email?token=xxx → kich hoat tai khoan

Login:
  POST /auth/login → {access_token (30m), refresh_token (7d), token_type: "bearer"}

Refresh:
  POST /auth/refresh → access_token moi

Logout:
  POST /auth/logout → blacklist jti trong Redis

Password Reset:
  POST /auth/forgot-password → email reset (token Redis 1h)
  POST /auth/reset-password  → dat mat khau moi

Google OAuth:
  GET /auth/google/login    → redirect Google (CSRF state luu Redis 10m)
  GET /auth/google/callback → exchange code → tim/tao user → tra token pair
```

**JWT Claims:** `sub` (user_id), `role`, `jti` (unique ID), `iat`, `exp`

**Password rules:** 6+ ky tu, >= 1 chu hoa, >= 1 chu thuong, >= 1 so, >= 1 ky tu dac biet (`@$!%*?&`)

---

## 5. API Endpoints

> Base path: `/api/v1` | Auth: Yes = Bearer token required, Admin = role=admin required

### `/auth`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| POST | `/register` | No | Dang ky |
| GET | `/verify-email` | No | Xac nhan email |
| POST | `/resend-verification` | No | Gui lai email xac nhan |
| POST | `/login` | No | Dang nhap |
| POST | `/logout` | Yes | Dang xuat |
| POST | `/refresh` | No | Lam moi access token |
| POST | `/forgot-password` | No | Yeu cau reset mat khau |
| POST | `/reset-password` | No | Dat mat khau moi |
| GET | `/google/login` | No | Redirect Google |
| GET | `/google/callback` | No | Callback Google OAuth |
| GET | `/me` | Yes | Thong tin user hien tai |

### `/users`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| GET | `/me` | Yes | Xem profile |
| PUT | `/me` | Yes | Cap nhat profile |
| PUT | `/me/password` | Yes | Doi mat khau |
| POST | `/me/avatar` | Yes | Upload anh dai dien (JPEG/PNG/WebP, max 2MB) |

### `/users/me/prescriptions`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| GET | `/` | Yes | Danh sach don thuoc (phan trang, tim kiem, loc status) |
| POST | `/` | Yes | Tao don thuoc + items |
| GET | `/{id}` | Yes | Chi tiet don thuoc |
| PUT | `/{id}` | Yes | Cap nhat don thuoc |
| DELETE | `/{id}` | Yes | Xoa (chi khi status = completed) |
| DELETE | `/` | Yes | Xoa nhieu don thuoc |
| GET | `/{id}/interactions` | Yes | Kiem tra tuong tac trong don |

### `/users/me/health-profiles`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| GET | `/` | Yes | Danh sach ho so (phan trang, tim kiem, loc ngay) |
| POST | `/` | Yes | Tao ho so kham benh |
| GET | `/{id}` | Yes | Chi tiet ho so |
| PUT | `/{id}` | Yes | Cap nhat ho so |
| DELETE | `/{id}` | Yes | Xoa ho so |
| DELETE | `/` | Yes | Xoa nhieu ho so |

### `/drugs`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| GET | `/` | Optional | Tim kiem thuoc (cache Redis 5 phut) |
| GET | `/{id}` | Optional | Chi tiet thuoc + san pham + canh bao (cache 10 phut) |
| GET | `/{id}/interactions` | Optional | Tuong tac cua mot thuoc (phan trang) |

### `/interactions`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| POST | `/check` | Yes | Kiem tra tuong tac 2-20 thuoc |
| POST | `/check/export` | Yes | Xuat ket qua ra Excel |

### `/chatbot`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| GET | `/suggestions` | No | Goi y cau hoi nhanh |
| POST | `/message` | Yes | Gui tin nhan - AI tra loi (co context suc khoe) |
| GET | `/history` | Yes | Lich su chat (phan trang) |
| DELETE | `/history` | Yes | Xoa toan bo lich su chat |

### `/recommendations`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| POST | `/` | Yes | Goi y thuoc theo trieu chung (AI) |
| POST | `/export` | Yes | Xuat goi y ra Excel |

### `/activity`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| GET | `/` | Yes | Lich su hoat dong (phan trang, loc theo action/ngay) |
| GET | `/export` | Yes | Xuat log ra Excel |
| DELETE | `/{id}` | Yes | Xoa 1 log |
| DELETE | `/` | Yes | Xoa nhieu log (max 100) hoac tat ca |

### `/admin/users`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| GET | `/` | Admin | Danh sach tat ca user |
| GET | `/{id}` | Admin | Chi tiet user + thong ke |
| PUT | `/{id}` | Admin | Cap nhat user |
| PATCH | `/{id}/toggle-active` | Admin | Bat/tat tai khoan |

### `/admin/drugs`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| POST | `/` | Admin | Tao thuoc moi |
| PUT | `/{id}` | Admin | Cap nhat thuoc |
| DELETE | `/{id}` | Admin | Xoa thuoc |
| POST | `/{id}/products` | Admin | Them san pham |
| PUT | `/{id}/products/{pid}` | Admin | Cap nhat san pham |
| DELETE | `/{id}/products/{pid}` | Admin | Xoa san pham |
| POST | `/{id}/warnings` | Admin | Them canh bao |
| DELETE | `/{id}/warnings/{wid}` | Admin | Xoa canh bao |

### `/admin/interactions`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| GET | `/` | Admin | Danh sach tuong tac (phan trang, loc) |
| POST | `/` | Admin | Tao tuong tac |
| PUT | `/{id}` | Admin | Cap nhat |
| DELETE | `/{id}` | Admin | Xoa |

### `/admin/logs` & `/admin/stats`
| Method | Path | Auth | Chuc nang |
|--------|------|------|-----------|
| GET | `/logs/system` | Admin | System logs |
| GET | `/logs/system/export` | Admin | Export system logs Excel |
| GET | `/logs/activity` | Admin | Activity logs toan bo user |
| GET | `/logs/activity/export` | Admin | Export activity logs Excel |
| GET | `/stats` | Admin | Dashboard statistics |

---

## 6. Services

| Service | File | Chuc nang chinh |
|---------|------|----------------|
| AuthService | auth_service.py | Dang ky, login, logout, OAuth, reset mat khau |
| UserService | user_service.py | Profile, avatar, doi mat khau, CRUD prescription/healthprofile |
| DrugService | drug_service.py | Tim kiem thuoc, chi tiet, tuong tac (co Redis cache) |
| InteractionService | drug_service.py | Kiem tra cap tuong tac, export Excel |
| ChatbotService | chatbot_service.py | AI chat voi context suc khoe nguoi dung |
| RecommendationService | recommendation_service.py | AI goi y thuoc theo trieu chung |
| OAuthService | oauth_service.py | Google OAuth flow |
| AdminUserService | admin_service.py | Quan ly user |
| AdminDrugService | admin_service.py | Quan ly thuoc (+ xoa cache Redis) |
| AdminInteractionService | admin_service.py | Quan ly tuong tac |
| ActivityLogService | log_service.py | Log hoat dong nguoi dung |
| SystemLogService | log_service.py | Log he thong |
| EmailService | email_service.py | Gui mail nen (background task) |

---

## 7. Caching Strategy (Redis)

| Key | TTL | Muc dich |
|----|-----|---------|
| `blacklist:{jti}` | = JWT expiry | JWT blacklist khi logout |
| `verify:email:{token}` | 24h | Email verification |
| `reset:password:{token}` | 1h | Password reset |
| `oauth:state:{state}` | 10m | OAuth CSRF (one-time use) |
| `refresh:{user_id}` | - | Invalidate refresh token (doi mat khau) |
| `cache:drugs:list:{page}:{size}:{search}:{form}` | 5m | Drug list cache |
| `cache:drug:{id}` | 10m | Drug detail cache |
| `cache:drug_interactions:{id1}:{id2}` | 30m | Interaction pair cache |

---

## 8. Pagination Format

Tat ca list endpoints tra ve:
```json
{
  "items": [...],
  "meta": { "total": 100, "page": 1, "size": 10, "total_pages": 10 }
}
```
Query params: `page` (default 1), `size` (default 10, max 100)

---

## 9. Middleware

### ActivityLogMiddleware (`core/middleware.py`)
- Tu dong log moi HTTP request thanh cong (status < 400) vao `activity_logs`
- Extract user_id tu Bearer token, action tu method + path, entity tu URL
- Fire-and-forget (async task, khong block response)

### CORS
- Origins: `FRONTEND_URL` + `http://localhost:5173`
- Credentials: enabled

---

## 10. Validation Rules

| Field | Rule |
|-------|------|
| Username | 3-30 ky tu, alphanumeric + underscore |
| Password | 6+ ky tu, chu hoa + thuong + so + @$!%*?& |
| Interaction check | 2-20 thuoc |
| Symptoms | 10-1000 ky tu |
| Avatar | JPEG/PNG/WebP, max 2MB |
| Activity log delete | max 100 per request |

---

## 11. Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379
SECRET_KEY=...
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=...
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_FROM=...
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
FRONTEND_URL=http://localhost:5173
APP_ENV=development
```

---

## 12. AI Features

### Chatbot (`/api/v1/chatbot/message`)
- Model: GPT-4o-mini
- Context: thong tin ca nhan (tuoi, gioi tinh), chan doan gan nhat, don thuoc dang dung
- System prompt: khong chan doan benh, huong dan gap bac si neu khan cap
- Luu lich su trong `chat_messages`

### Recommendations (`/api/v1/recommendations`)
- Model: GPT-4o-mini
- Input: mo ta trieu chung (10-1000 ky tu), lich su suc khoe
- AI tra ve JSON danh sach thuoc goi y voi diem phu hop
- Query DB tim thuoc tuong ung, kiem tra tuong tac voi thuoc hien tai
- Export Excel duoc

---

## 13. Export Excel

Cac endpoint xuat Excel (.xlsx):
- `/interactions/check/export` - Ket qua kiem tra tuong tac
- `/activity/export` - Log hoat dong nguoi dung
- `/recommendations/export` - Goi y thuoc
- `/admin/logs/system/export` - System logs
- `/admin/logs/activity/export` - Activity logs toan bo

Format: header mau xanh, du lieu co cau truc.
