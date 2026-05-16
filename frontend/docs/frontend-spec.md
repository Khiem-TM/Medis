# Medis — Frontend Design & Architecture Specification

**Phiên bản:** 1.0  
**Ngày cập nhật:** 2026-05-16  
**Nguồn:** Phân tích toàn bộ backend FastAPI + frontend Vue 3 hiện có

---

## Mục lục

1. [Product Overview](#1-product-overview)
2. [User Roles & Permissions](#2-user-roles--permissions)
3. [Sitemap](#3-sitemap)
4. [Route Structure](#4-route-structure)
5. [Danh sách Screen/Page](#5-danh-sách-screenpage)
6. [Workflow Chi Tiết](#6-workflow-chi-tiết)
7. [Form Specification](#7-form-specification)
8. [Data Field Mapping](#8-data-field-mapping)
9. [UI/UX Style Guide](#9-uiux-style-guide)
10. [Component Breakdown](#10-component-breakdown)
11. [State Management](#11-state-management)
12. [API Integration Plan](#12-api-integration-plan)
13. [Validation Rules](#13-validation-rules)
14. [Loading / Error / Empty States](#14-loading--error--empty-states)
15. [Permission Matrix](#15-permission-matrix)
16. [Responsive Behavior](#16-responsive-behavior)
17. [Wireframe / Layout Description](#17-wireframe--layout-description)

---

## 1. Product Overview

### Medis là gì?

Medis là ứng dụng web quản lý thuốc và sức khỏe cá nhân, kết hợp AI (GPT-4o-mini) để:

- Giúp người dùng tra cứu, theo dõi và quản lý đơn thuốc
- Kiểm tra tương tác thuốc (Drug-Drug Interaction — DDI) theo thời gian thực
- Gợi ý thuốc phù hợp dựa trên triệu chứng thông qua AI
- Lưu trữ hồ sơ khám bệnh cá nhân
- Nhắc uống thuốc theo lịch
- Tư vấn sức khỏe qua chatbot AI với ngữ cảnh hồ sơ bệnh nhân

### Người dùng chính

| Nhóm | Mô tả |
|------|-------|
| Người dùng thông thường | Bệnh nhân, người chăm sóc sức khỏe cá nhân |
| Quản trị viên | Quản lý hệ thống, dữ liệu thuốc, người dùng |

### Module chính

1. **Auth & Profile** — Đăng ký, đăng nhập, Google OAuth, quản lý tài khoản
2. **Prescriptions** — Quản lý đơn thuốc cá nhân + kiểm tra tương tác tự động
3. **Drug Catalog** — Tra cứu thuốc generic (hoạt chất) và thuốc thương mại (DAV)
4. **Interaction Checker** — Kiểm tra tương tác thuốc độc lập (generic + thương mại)
5. **AI Chatbot** — Hỏi đáp sức khỏe có ngữ cảnh
6. **AI Recommendations** — Gợi ý thuốc từ triệu chứng
7. **Health Profiles** — Hồ sơ khám bệnh
8. **Reminders** — Lịch nhắc uống thuốc + WebSocket real-time
9. **Notifications** — Thông báo real-time qua WebSocket
10. **Admin Panel** — CRUD người dùng, thuốc, tương tác, xem logs

### Mục tiêu UX

- **Zero friction cho tra cứu thuốc**: Không yêu cầu đăng nhập để xem thông tin thuốc
- **AI first**: Tích hợp AI tự nhiên vào quy trình tạo đơn thuốc
- **Mobile friendly**: Responsive đầy đủ, hỗ trợ dùng trên điện thoại
- **Tiếng Việt toàn bộ**: UI, thông báo, lỗi đều bằng tiếng Việt

---

## 2. User Roles & Permissions

### Role Definitions

| Role | Mô tả | Điều kiện |
|------|-------|-----------|
| `guest` | Chưa đăng nhập | — |
| `user` | Người dùng đã đăng nhập, đã xác thực email | `is_active=true`, `is_email_verified=true` |
| `admin` | Quản trị viên hệ thống | `role='admin'` trong DB |

### Permission Matrix Tóm Tắt

| Tính năng | Guest | User | Admin |
|-----------|-------|------|-------|
| Xem trang landing | ✅ | ✅ | ✅ |
| Tra cứu thuốc generic | ✅ | ✅ | ✅ |
| Xem chi tiết thuốc | ✅ | ✅ | ✅ |
| Xem thuốc thương mại | ✅ | ✅ | ✅ |
| Đăng nhập / Đăng ký | ✅ | ❌ (redirect /dashboard) | ❌ |
| Dashboard | ❌ | ✅ | ✅ |
| Quản lý đơn thuốc | ❌ | ✅ | ❌ |
| Kiểm tra tương tác thuốc | ❌ | ✅ | ✅ |
| Chatbot AI | ❌ | ✅ | ✅ |
| Gợi ý thuốc AI | ❌ | ✅ | ✅ |
| Hồ sơ khám bệnh | ❌ | ✅ | ❌ |
| Nhắc uống thuốc | ❌ | ✅ | ❌ |
| Thông báo real-time | ❌ | ✅ | ✅ |
| Admin: Quản lý người dùng | ❌ | ❌ | ✅ |
| Admin: Quản lý thuốc | ❌ | ❌ | ✅ |
| Admin: Quản lý tương tác | ❌ | ❌ | ✅ |
| Admin: Xem logs | ❌ | ❌ | ✅ |
| Admin: Thống kê hệ thống | ❌ | ❌ | ✅ |

### Auth Provider Differences

| Tính năng | Local Auth | Google OAuth |
|-----------|-----------|--------------|
| Đổi mật khẩu | ✅ Hiển thị | ❌ Ẩn |
| Xem Google account info | ❌ | ✅ |
| Quên mật khẩu | ✅ | ❌ |

---

## 3. Sitemap

```
medis.app/
│
├── / (Landing Page)
│
├── /login
├── /register
├── /forgot-password
│   └── /verify-otp
│       └── /reset-password
├── /verify-email
├── /auth/callback (OAuth silent redirect)
│
├── /dashboard (Authenticated)
│
├── /profile
│   ├── /profile/prescriptions
│   │   └── /profile/prescriptions/:id
│   └── /profile/health
│       └── /profile/health/:id
│
├── /drugs (Public)
│   └── /drugs/:id
│
├── /market-drugs
│   └── /market-drugs/:id
│
├── /interactions (Authenticated)
│
├── /chatbot (Authenticated)
│
├── /recommendations (Authenticated)
│
├── /schedule (Authenticated)
│
├── /admin (Admin Only)
│   ├── /admin/users
│   │   └── /admin/users/:id
│   ├── /admin/drugs
│   ├── /admin/interactions
│   └── /admin/logs
│
├── /forbidden
└── /* (404 Not Found)
```

---

## 4. Route Structure

### Route Configuration (Vue Router)

```typescript
// Layouts
// - "app": Main layout (AppNavbar + AppSidebar + content)
// - "auth": Centered auth card, no sidebar
// - "admin": Admin layout (AdminSidebar + content)
// - "none": Full-page, no chrome (Landing)
```

### Route Guard Logic

```
Navigation →
  if (requiresAuth && !isAuthenticated)
    → redirect /login?redirect=<original_path>
  if (requiresAdmin && !isAdmin)
    → redirect /forbidden
  if (requiresGuest && isAuthenticated)
    → redirect /dashboard
  else
    → render
```

### Full Route Table

| Path | Layout | Auth | Admin | Guest Only | Meta Title |
|------|--------|------|-------|------------|------------|
| `/` | none | — | — | — | Medis |
| `/login` | auth | — | — | ✅ | Đăng nhập |
| `/register` | auth | — | — | ✅ | Đăng ký |
| `/forgot-password` | auth | — | — | ✅ | Quên mật khẩu |
| `/verify-otp` | auth | — | — | ✅ | Xác nhận OTP |
| `/reset-password` | auth | — | — | ✅ | Đặt lại mật khẩu |
| `/verify-email` | auth | — | — | — | Xác nhận email |
| `/auth/callback` | none | — | — | — | Đang đăng nhập... |
| `/dashboard` | app | ✅ | — | — | Tổng quan |
| `/profile` | app | ✅ | — | — | Hồ sơ cá nhân |
| `/profile/prescriptions` | app | ✅ | — | — | Đơn thuốc |
| `/profile/prescriptions/:id` | app | ✅ | — | — | Chi tiết đơn thuốc |
| `/profile/health` | app | ✅ | — | — | Hồ sơ khám bệnh |
| `/profile/health/:id` | app | ✅ | — | — | Chi tiết hồ sơ |
| `/drugs` | app | — | — | — | Tra cứu thuốc |
| `/drugs/:id` | app | — | — | — | Chi tiết thuốc |
| `/market-drugs/:id` | app | — | — | — | Chi tiết thuốc thương mại |
| `/interactions` | app | ✅ | — | — | Kiểm tra tương tác |
| `/chatbot` | app | ✅ | — | — | Chatbot AI |
| `/recommendations` | app | ✅ | — | — | Gợi ý thuốc AI |
| `/schedule` | app | ✅ | — | — | Lịch uống thuốc |
| `/admin` | admin | ✅ | ✅ | — | (redirect /admin/users) |
| `/admin/users` | admin | ✅ | ✅ | — | Quản lý người dùng |
| `/admin/users/:id` | admin | ✅ | ✅ | — | Chi tiết người dùng |
| `/admin/drugs` | admin | ✅ | ✅ | — | Quản lý thuốc |
| `/admin/interactions` | admin | ✅ | ✅ | — | Quản lý tương tác |
| `/admin/logs` | admin | ✅ | ✅ | — | Nhật ký hệ thống |
| `/forbidden` | none | — | — | — | Không có quyền |
| `/*` | none | — | — | — | Không tìm thấy |

---

## 5. Danh sách Screen/Page

### 5.1 Landing Page (`/`)

**Mục đích:** Giới thiệu sản phẩm, CTA đăng ký/đăng nhập  
**Auth:** Không yêu cầu  
**Components chính:**
- Hero section: Tiêu đề lớn, mô tả ngắn, 2 nút CTA (Bắt đầu → /register, Đăng nhập → /login)
- Feature cards (6): Quản lý đơn thuốc, Kiểm tra tương tác, Chatbot AI, Tra cứu thuốc, Gợi ý AI, Nhắc uống thuốc
- Stats section: Số liệu (5000+ thuốc, 10000+ tương tác...)
- Footer

---

### 5.2 Màn hình Auth

#### Login (`/login`)
**Mục đích:** Đăng nhập bằng username/password hoặc Google  
**Fields:** username (text), password (password + toggle visibility)  
**Actions:** Submit login, Google OAuth button, links đến /register, /forgot-password  
**Success:** Redirect về `?redirect` param hoặc `/dashboard`

#### Register (`/register`)
**Mục đích:** Đăng ký tài khoản mới  
**Fields:** full_name, phone, email, username, password, confirm_password  
**Success:** Hiển thị thông báo "Kiểm tra email để xác thực"

#### Forgot Password (`/forgot-password`)
**Flow:** 3 bước — Email → OTP → New Password

**Step 1 - Email Input:**
- Field: email
- Action: POST /auth/forgot-password/otp → OTP gửi email
- Success: Navigate to /verify-otp với email trong state/query

**Step 2 - OTP Verify (`/verify-otp`):**
- Component: OtpInput (6 ô số)
- Auto-focus next field on input
- Resend OTP button (cooldown 60 giây)
- Success: nhận `reset_token`, navigate to /reset-password

**Step 3 - Reset Password (`/reset-password`):**
- Fields: new_password, confirm_new_password (+ hidden reset_token)
- Success: redirect /login với message toast "Đặt lại mật khẩu thành công"

#### Verify Email (`/verify-email`)
**Trigger:** User click link trong email  
**Query Param:** `?token=<verification_token>`  
**Auto-call:** GET /auth/verify-email?token=... on mount  
**States:** Loading, Success (link /login), Error (token expired + Resend button)

#### OAuth Callback (`/auth/callback`)
**Trigger:** Google OAuth redirect  
**Query Params:** `?access_token=...&refresh_token=...`  
**Auto-action:** Lưu tokens → navigate /dashboard  
**Error:** Navigate /login?error=oauth_failed

---

### 5.3 Dashboard (`/dashboard`)

**Mục đích:** Tổng quan cá nhân hóa — khác nhau với user vs admin  
**Layout:** Two-column (sidebar + main), full responsive

**Phần User Dashboard:**
- Hero card gradient: Chào {user.full_name}, subtitle "Sức khỏe của bạn ngày hôm nay"
- Quick Actions (4 tile): Chat AI, Tạo đơn thuốc, Kiểm tra tương tác, Tra cứu thuốc
- Thống kê đơn thuốc: Tổng / Đang dùng / Đã hoàn thành
- Vòng tròn tuân thủ: Tuần này 92%, Tháng này 88% (placeholder/calculated)
- Đơn thuốc gần đây: 5 hàng với name, drug count, status badge, created date
- Activity feed: 5 hoạt động gần nhất (action icon + text + time)

**Phần Admin Dashboard (thay thế):**
- Stats cards (4): Tổng users, Drugs, Tương tác, Chat messages
- Quick links to admin sections

---

### 5.4 Profile (`/profile`)

**Layout:** Sidebar tabs (thông tin + bảo mật) + main content area  
**Components:**
- Avatar với upload overlay hover
- Form thông tin cá nhân: full_name, phone, date_of_birth, gender, address, occupation
- Tab Bảo mật: Đổi mật khẩu (chỉ local auth), Xóa lịch sử hoạt động, Xóa lịch sử chat

**Avatar Upload:**
- Click avatar → file input
- Preview inline
- POST /users/me/avatar (multipart)
- Hiển thị progress

---

### 5.5 Prescriptions (`/profile/prescriptions`)

**Mục đích:** CRUD đơn thuốc cá nhân  
**Layout:** Table/list + Create modal

**List Area:**
- Search input (debounce 300ms)
- Status filter: Tất cả / Đang dùng / Đã hoàn thành
- Bảng: Tên, Số thuốc, Trạng thái, Ngày tạo, Hành động
- Pagination
- Bulk delete checkbox

**Create/Edit Modal:**
- Section Notes: textarea
- Section Status: dropdown (active/completed)
- Section AI Suggestion Panel (collapsible accordion):
  - Textarea triệu chứng (Ctrl+Enter shortcut)
  - Nút "Gợi ý" (loading spinner khi đang xử lý)
  - Cards kết quả: tên thuốc, hoạt chất, chỉ định, liều tham khảo, điểm phù hợp
  - Nút "+ Thêm" → chuyển thành "✓ Đã thêm" + card xanh
- Section Drug Items:
  - Mỗi hàng: MarketDrugSearchField / tên thuốc AI (chip), dosage, frequency, duration, xóa
  - Nút "Thêm thuốc"
  - Tối thiểu 1 thuốc

**Detail Page (`/profile/prescriptions/:id`):**
- Full prescription info + items table
- Section Kiểm tra tương tác: Nút check + kết quả hiển thị inline
- Nút Sửa → mở edit modal
- Nút Xóa (chỉ khi status = completed)

---

### 5.6 Health Profiles (`/profile/health`)

**Mục đích:** Lưu trữ hồ sơ khám bệnh  
**Layout:** List + Create/Edit modal

**List:**
- Search by diagnosis_name
- Filter by exam_date range (from/to date picker)
- Cards: diagnosis_name, exam_date, facility, doctor, linked prescription badge
- Pagination

**Create/Edit Form:**
- diagnosis_name (required)
- exam_date (date picker, required)
- facility, doctor (optional text)
- symptoms, conclusion (textarea)
- prescription_id (link đến đơn thuốc có sẵn — dropdown search)
- notes (textarea)

**Detail Page (`/profile/health/:id`):**
- Full health record display
- Linked prescription card (nếu có)
- Edit/Delete actions

---

### 5.7 Drug Search (`/drugs`)

**Mục đích:** Tra cứu thuốc generic từ database  
**Auth:** Không cần  
**Layout:** Search bar nổi bật + result table + pagination

**Features:**
- Debounce search 400ms
- Columns: ID, Tên generic, Actions (xem chi tiết)
- Empty state khi chưa search: hướng dẫn

**Drug Detail (`/drugs/:id`):**
- generic_name (heading)
- description (rich text or plain)
- chemical_formula, molecular_formula
- Tabs: Cảnh báo / Dạng bào chế / Phân loại / Mã ATC / Tương tác
- Tab Tương tác: paginated list, source badge (DB/AI), confidence score

---

### 5.8 Market Drug Detail (`/market-drugs/:id`)

**Mục đích:** Chi tiết thuốc thương mại từ catalog DAV  
**Auth:** Không cần  
**Layout:** Product-style page (Pharmacity-inspired)

**Sections:**
- Tên sản phẩm (heading) + registration_number badge
- Badges: is_expired (Hết hạn), is_withdrawn (Đã thu hồi), is_active
- Thông tin cơ bản: dosage_form, packaging, route_name, shelf_life, quality_standard
- Thành phần: ingredient_summary list + ddi_drug_id links
- Thông tin đăng ký: registration_number, decision_number, registration_date, expiry_date
- CTA: "Kiểm tra tương tác" → /interactions với product pre-selected

---

### 5.9 Interaction Checker (`/interactions`)

**Mục đích:** Kiểm tra tương tác thuốc (2 chế độ)  
**Auth:** Bắt buộc

**Mode Toggle:** Tab "Thuốc thương mại" | "Thuốc hoạt chất"

**Market Drug Mode:**
- MarketDrugSearchField × max 10 products
- Mỗi hàng: tên sản phẩm + nút xóa
- Nút Kiểm tra
- POST /market-drugs/check-interactions
- Hiển thị unmapped_products nếu có

**Generic Drug Mode:**
- DrugSearchCombobox × max 20 drugs
- Mỗi hàng: tên + drug_id + nút xóa
- Nút Kiểm tra + Nút Xuất Excel
- POST /interactions/check

**Results (cả 2 chế độ):**
- Summary card: tổng cặp / cặp tương tác / cặp an toàn / dự đoán AI
- Interaction cards: cặp thuốc, loại sự kiện, nhãn, nguồn (DB/AI), confidence %
- Safe pairs: collapsed list
- Warning banner: Thăm khám bác sĩ nếu có tương tác

---

### 5.10 Chatbot (`/chatbot`)

**Mục đích:** Chat AI sức khỏe  
**Auth:** Bắt buộc  
**Layout:** Sidebar (chat history list) + Chat area

**Sidebar:**
- Danh sách sessions theo ngày (gom nhóm)
- Nút Xóa toàn bộ lịch sử
- Ẩn trên mobile, toggle bằng nút

**Chat Area:**
- Header: tên "Chatbot AI Sức khỏe" + nút toggle sidebar
- Health profile context banner (nếu có baseline)
- Messages area: cuộn ngược, bubble user (phải) / AI (trái)
- Typing indicator (3 dots animation)
- Quick suggestions khi chưa có tin nhắn (horizontal chips)
- Input: textarea tự mở rộng, Enter = gửi, Shift+Enter = xuống dòng, giới hạn 2000 ký tự, counter

**Message Features:**
- Timestamp hover
- Copy message
- Mark down rendering (bold, list, code)

---

### 5.11 AI Recommendations (`/recommendations`)

**Mục đích:** Gợi ý thuốc từ mô tả triệu chứng  
**Auth:** Bắt buộc

**Input Area:**
- Textarea triệu chứng (min 10 ký tự, max 1000)
- Optional: chọn health profile để AI tham khảo
- Optional: chọn đơn thuốc hiện tại để tránh tương tác
- Nút Gợi ý (spinner khi loading)

**Results Area:**
- General advice banner
- "Gặp bác sĩ nếu..." warning box
- Drug cards grid (2-3 columns responsive):
  - Tên thuốc (heading)
  - Hoạt chất
  - Chỉ định
  - Liều tham khảo
  - Điểm phù hợp: bar + badge màu (xanh ≥80, tím ≥60, xám <60)
  - Cảnh báo (nếu có)
  - has_interaction badge (nếu true)
- Nút Xuất Excel
- Nút Thêm vào đơn thuốc (navigate to /profile/prescriptions với suggestions pre-filled)

---

### 5.12 Schedule / Reminders (`/schedule`)

**Mục đích:** Quản lý lịch nhắc uống thuốc  
**Auth:** Bắt buộc

**Today's Schedule:**
- Timeline theo giờ (sắp xếp theo reminder_time)
- Mỗi reminder: tên thuốc, giờ, notes, is_active toggle

**Reminder List:**
- Tabs: Tất cả / Đang hoạt động / Đã tắt
- Cards: drug_name, reminder_time, frequency (daily/custom + days_of_week), notes
- Toggle switch is_active
- Edit button, Delete button

**Create/Edit Modal:**
- drug_name (text, required)
- reminder_time (time picker HH:MM)
- frequency: radio (daily / custom)
- days_of_week: checkbox grid (T2/T3/T4/T5/T6/T7/CN) — hiển thị khi frequency=custom
- prescription_item (optional link)
- notes (textarea)

---

### 5.13 Notifications

**Notification Bell (AppNavbar):**
- Badge với unread_count
- Dropdown: list 10 notifications mới nhất
- Mark as read khi click
- "Xem tất cả" link

**Notification Types & Icons:**
- `medication_reminder`: 💊 icon, màu primary
- `health_alert`: ⚠️ icon, màu warning
- `system`: 🔔 icon, màu neutral
- `daily_summary`: 📋 icon, màu secondary

**Priority Colors:**
- `urgent`: đỏ
- `high`: cam
- `medium`: xanh
- `low`: xám

**WebSocket:**
- Connect on authenticated route entry
- Reconnect on disconnect (exponential backoff: 1s, 2s, 4s, max 30s)
- Toast notification khi nhận push

---

### 5.14 Admin Screens

#### Admin Users (`/admin/users`)
- Stats cards: Tổng users, Active, New today, Admin count
- Table: Avatar + Username, Email, Họ tên, Role badge, Active status, Ngày tạo, Actions
- Search + Role filter + Active filter
- Toggle active button (inline)
- Link đến /admin/users/:id

#### Admin User Detail (`/admin/users/:id`)
- Profile summary (readonly)
- Edit form: full_name, phone, role, is_active
- Stats: prescription_count, health_profile_count, activity_log_count
- Activity log mini-list

#### Admin Drugs (`/admin/drugs`)
- Table: ID, Tên generic, Số cảnh báo, Ngày tạo, Actions
- Create modal: id (optional), generic_name, description, chemical_formula, molecular_formula
- Edit modal: same fields
- Delete confirm dialog
- Manage Warnings sub-section (inline): danh sách warning + add form

#### Admin Interactions (`/admin/interactions`)
- Table: Drug 1, Drug 2, Source, Confidence, Ngày tạo, Actions
- Filter by drug_id
- Create modal: drug_id (search), interacts_with_id (search)
- Delete confirm

#### Admin Logs (`/admin/logs`)
- Tabs: System Logs | Activity Logs
- System Logs:
  - Table: Level badge, Source, Message, Thời gian
  - Filter: level, source, date range
  - Export Excel button
- Activity Logs:
  - Table: User, Action, Entity, IP, Thời gian
  - Filter: user, action, date range
  - Export Excel button

---

### 5.15 Onboarding Flow

**Trigger:** First login → check `onboarding_completed` từ GET /users/me/onboarding  
**Route:** Modal overlay hoặc dedicated `/onboarding`  
**Steps:** 3 bước, có thể skip

**Step 1 — Sức khỏe cơ bản:**
- height_cm (number input), weight_kg (number input)
- blood_type (dropdown: O+, A+, B+, AB+, O-, A-, B-, AB-)
- is_pregnant (checkbox, hidden if male), is_breastfeeding (checkbox)
- kidney_function, liver_function (dropdown: normal/mild/moderate/severe impairment)

**Step 2 — Bệnh lý & Dị ứng:**
- Dual input: Free text Vietnamese OR structured list
- conditions_text (textarea, hint: "VD: Huyết áp cao, tiểu đường") + AI parse button
- allergies_text (textarea) + AI parse button
- Chips hiển thị parsed conditions và allergies

**Step 3 — Thuốc hiện tại & Mục tiêu:**
- medications_text (textarea) + AI parse button
- medications chips (name, dosage, frequency)
- health_goals (multi-select chips)

**Navigation:** Prev / Next / Skip / Submit

---

## 6. Workflow Chi Tiết

### 6.1 Quy trình Đăng Ký

```
/register
    │
    ├── Fill form → POST /auth/register
    │       └── 201: Toast "Kiểm tra email" → Stay on page with success msg
    │       └── 400 (duplicate email): Highlight email field
    │       └── 400 (duplicate username): Highlight username field
    │
/verify-email?token=xxx
    │
    ├── Auto-call GET /auth/verify-email?token=xxx on mount
    │       └── 200: "Xác thực thành công" + nút Đăng nhập → /login
    │       └── 400: "Token hết hạn" + nút Gửi lại email
    │
POST /auth/resend-verification (nếu cần)
```

### 6.2 Quy trình Tạo Đơn Thuốc với AI

```
Open Create Modal
    │
    ├── [Tùy chọn] Nhập triệu chứng → POST /recommendations
    │       └── Danh sách gợi ý (DrugSuggestion[])
    │       └── Click "+ Thêm" → addSuggestionToItems()
    │               ├── Tìm slot trống trong items[]
    │               ├── Set drug_name = suggestion.drug_name
    │               ├── Set drug_id = suggestion.drug_id
    │               └── Set dosage = suggestion.reference_dosage
    │
    ├── [Tùy chọn] Search thuốc thương mại → MarketDrugSearchField
    │       └── Select product → set market_product_id + drug_name
    │
    ├── Fill name, notes, status, dosage, frequency, duration
    │
    └── Submit → POST /users/me/prescriptions
            ├── 201: Toast "Tạo đơn thuốc thành công"
            │       └── If interaction_check.has_interaction:
            │               → Show interaction warning modal
            └── 422: Validation errors inline
```

### 6.3 Quy trình Kiểm Tra Tương Tác

```
/interactions
    │
    ├── Mode: Thuốc thương mại
    │       ├── Search + add products (max 10)
    │       └── Click Kiểm tra
    │               └── POST /market-drugs/check-interactions
    │                       ├── Success: hiển thị ddi_result
    │                       └── unmapped_products: hiển thị warning
    │
    └── Mode: Thuốc hoạt chất
            ├── Search + add generic drugs (max 20)
            └── Click Kiểm tra
                    └── POST /interactions/check
                            ├── Success: hiển thị interactions + safe_pairs
                            └── prediction_count > 0: "X dự đoán bởi AI" badge
```

### 6.4 Quy trình Quên Mật Khẩu (OTP)

```
/forgot-password
    ├── Enter email
    └── POST /auth/forgot-password/otp → email sent
            └── navigate /verify-otp?email=xxx

/verify-otp
    ├── Enter 6-digit OTP
    └── POST /auth/verify-reset-otp {email, otp}
            ├── 200: {reset_token} → sessionStorage.setItem('reset_token', token)
            │         navigate /reset-password
            └── 400: "OTP không đúng hoặc đã hết hạn"

/reset-password
    ├── new_password + confirm
    └── POST /auth/reset-password {token, new_password, confirm_new_password}
            └── 200: navigate /login?success=password_reset
```

### 6.5 Quy trình Notifications + WebSocket

```
App startup (authenticated):
    └── connect WebSocket ws://api/v1/notifications/ws?token=<jwt>

Receive message:
    ├── type="connected": log "WS ready"
    ├── type="notification":
    │       ├── Increment badge count (unread_count++)
    │       ├── Show toast (title + body, auto-dismiss 5s)
    │       └── Prepend to notification list
    └── type="pong": update heartbeat timestamp

Heartbeat: ping every 30s

Disconnect:
    └── Reconnect với exponential backoff

Mark as read:
    └── PATCH /notifications/{id}/read
            └── Decrement unread_count

Mark all read:
    └── PATCH /notifications/read-all
            └── Set unread_count = 0
```

---

## 7. Form Specification

### 7.1 Login Form

| Field | Type | Required | Validation | Placeholder |
|-------|------|----------|------------|-------------|
| username | text | ✅ | Non-empty | Tên đăng nhập |
| password | password | ✅ | Non-empty | Mật khẩu |

**Submit behavior:** Disable button + spinner khi loading

---

### 7.2 Register Form

| Field | Type | Required | Validation | Placeholder |
|-------|------|----------|------------|-------------|
| full_name | text | ✅ | Non-empty, max 100 | Họ và tên |
| phone | tel | ✅ | Non-empty | Số điện thoại |
| email | email | ✅ | Valid email format | Email |
| username | text | ✅ | 3-30 chars, a-z0-9_ | Tên đăng nhập |
| password | password | ✅ | ≥6 chars, 1 upper, 1 lower, 1 digit, 1 special | Mật khẩu |
| confirm_password | password | — | Must match password | Nhập lại mật khẩu |

---

### 7.3 Create Prescription Form

| Field | Type | Required | Validation | Notes |
|-------|------|----------|------------|-------|
| name | text | ✅ | max 200 | Tên đơn thuốc |
| status | select | ✅ | active/completed | Default: active |
| notes | textarea | — | max 1000 | Ghi chú |
| items[].drug_name | text | ✅ | max 200 | Tên thuốc |
| items[].market_product_id | number | — | — | ID thuốc thương mại |
| items[].drug_id | string | — | — | ID hoạt chất (từ AI) |
| items[].dosage | text | ✅ | max 100 | VD: 500mg |
| items[].frequency | text | — | max 100 | VD: 3 lần/ngày |
| items[].duration | text | — | max 100 | VD: 7 ngày |

**Constraint:** ít nhất 1 item; mỗi item cần drug_name hoặc market_product_id

---

### 7.4 Create Health Profile Form

| Field | Type | Required | Validation | Notes |
|-------|------|----------|------------|-------|
| diagnosis_name | text | ✅ | max 200 | Tên chẩn đoán |
| exam_date | date | ✅ | valid date, ≤ today | Ngày khám |
| facility | text | — | max 200 | Cơ sở y tế |
| doctor | text | — | max 100 | Bác sĩ |
| symptoms | textarea | — | — | Triệu chứng |
| conclusion | textarea | — | — | Kết luận |
| prescription_id | select | — | valid prescription id | Đơn thuốc liên quan |
| notes | textarea | — | — | Ghi chú |

---

### 7.5 Create Reminder Form

| Field | Type | Required | Validation | Notes |
|-------|------|----------|------------|-------|
| drug_name | text | ✅ | max 200 | Tên thuốc |
| reminder_time | time | ✅ | HH:MM format | Giờ nhắc |
| frequency | radio | ✅ | daily/custom | Default: daily |
| days_of_week | checkbox | Conditional | required if frequency=custom | T2-CN |
| notes | textarea | — | — | Ghi chú |

---

### 7.6 Onboarding Step 1

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| height_cm | number | — | 50-250 |
| weight_kg | number | — | 10-500 |
| blood_type | select | — | O+/A+/B+/AB+/O-/A-/B-/AB- |
| is_pregnant | checkbox | — | — |
| is_breastfeeding | checkbox | — | — |
| kidney_function | select | — | normal/mild_impairment/moderate_impairment/severe_impairment |
| liver_function | select | — | normal/mild_impairment/moderate_impairment/severe_impairment |

---

### 7.7 Change Password Form

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| old_password | password | ✅ | non-empty |
| new_password | password | ✅ | ≥6 chars, 1 upper, 1 lower, 1 digit, 1 special |
| confirm_password | password | ✅ | must match new_password |

---

## 8. Data Field Mapping

### 8.1 User Profile

| Frontend Label | Backend Field | Type | Notes |
|----------------|---------------|------|-------|
| Họ và tên | full_name | string\|null | — |
| Số điện thoại | phone | string\|null | — |
| Ngày sinh | date_of_birth | ISO datetime\|null | Date picker |
| Giới tính | gender | string\|null | male/female/other |
| Địa chỉ | address | string\|null | Textarea |
| Nghề nghiệp | occupation | string\|null | — |
| Ảnh đại diện | avatar_url | string\|null | URL |
| Nhà cung cấp | auth_provider | local\|google | Readonly |
| Quyền hạn | role | user\|admin | Readonly |

### 8.2 Prescription Item

| Frontend Label | Backend Field | Type | Notes |
|----------------|---------------|------|-------|
| Tên thuốc | drug_name | string | Required |
| Thuốc thương mại | market_product_id | int\|null | From MarketDrugSearch |
| Hoạt chất ID | drug_id | string\|null | From AI suggestion |
| Liều dùng | dosage | string | Required, e.g. "500mg" |
| Tần suất | frequency | string\|null | e.g. "3 lần/ngày" |
| Thời gian | duration | string\|null | e.g. "7 ngày" |

### 8.3 Drug Interaction Result

| Frontend Label | Backend Field | Type | Display |
|----------------|---------------|------|---------|
| Thuốc 1 | drug_name | string | — |
| Thuốc 2 | interacts_with_name | string | — |
| Loại sự kiện | event_type.event_name | string\|null | Badge |
| Nhãn | interaction_label | string\|null | — |
| Nguồn | source | database\|model_predicted | DB icon / AI icon |
| Độ tin cậy | confidence_score | float 0-1 | % badge |

### 8.4 Drug Suggestion (AI)

| Frontend Label | Backend Field | Type | Display |
|----------------|---------------|------|---------|
| Tên thuốc | drug_name | string | Heading |
| Hoạt chất | active_ingredient | string | Sub-text |
| Chỉ định | indication | string | Body text |
| Liều tham khảo | reference_dosage | string | Info line |
| Điểm phù hợp | suitability_score | int 0-100 | Bar + badge |
| Cảnh báo | warnings | string\|null | Warning box |
| Có tương tác | has_interaction | boolean | Warning chip |

### 8.5 Health Baseline

| Frontend Label | Backend Field | Type | Notes |
|----------------|---------------|------|-------|
| Chiều cao | height_cm | float\|null | cm |
| Cân nặng | weight_kg | float\|null | kg |
| Nhóm máu | blood_type | string\|null | O+, A+,... |
| Bệnh nền | chronic_conditions | JSON string | Array of strings |
| Dị ứng | allergies | JSON string | Array of {drug, reaction} |
| Thuốc đang dùng | current_medications | JSON string | Array of {name, dosage, frequency} |
| Chức năng thận | kidney_function | enum | normal=Bình thường, etc. |
| Chức năng gan | liver_function | enum | — |
| Mục tiêu sức khỏe | health_goals | JSON string | Array of strings |

### 8.6 Notification

| Frontend Label | Backend Field | Type |
|----------------|---------------|------|
| Tiêu đề | title | string |
| Nội dung | body | string |
| Loại | type | medication_reminder\|health_alert\|system\|daily_summary |
| Ưu tiên | priority | low\|medium\|high\|urgent |
| Đã đọc | is_read | boolean |
| Thời gian | created_at | ISO datetime |

---

## 9. UI/UX Style Guide

### 9.1 Design System

**Framework:** Tailwind CSS v4 với Material Design 3 tokens

### 9.2 Color Palette

```css
/* Primary — Teal/Green (sức khỏe) */
--color-primary:           #00897B  /* Teal 600 */
--color-primary-container: #B2DFDB  /* Teal 100 */
--color-on-primary:        #FFFFFF
--color-on-primary-container: #004D40

/* Secondary — Indigo */
--color-secondary:           #3949AB
--color-secondary-container: #C5CAE9
--color-on-secondary:        #FFFFFF

/* Tertiary — Purple */
--color-tertiary:           #7B1FA2
--color-tertiary-container: #E1BEE7

/* Error */
--color-error:           #B00020
--color-error-container: #FDECEA

/* Warning */
--color-warning:           #E65100
--color-warning-container: #FBE9E7

/* Surface */
--color-surface:      #FAFAFA
--color-surface-variant: #F5F5F5
--color-outline:      #E0E0E0
```

### 9.3 Typography

```css
/* Heading */
.text-h1: 2rem (32px), font-bold, tracking-tight
.text-h2: 1.5rem (24px), font-bold
.text-h3: 1.25rem (20px), font-semibold
.text-h4: 1rem (16px), font-semibold

/* Body */
.text-body-lg: 1rem, font-normal
.text-body:    0.875rem (14px), font-normal
.text-body-sm: 0.75rem (12px), font-normal

/* Label */
.text-label:    0.75rem, font-medium, tracking-wide
.text-caption:  0.625rem (10px), font-normal
```

### 9.4 Spacing

Base unit: 4px (Tailwind default)
- xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px, 2xl: 48px

### 9.5 Border Radius

```
rounded-sm: 4px   (inputs, badges)
rounded:    6px   (buttons)
rounded-lg: 8px   (cards)
rounded-xl: 12px  (modals, panels)
rounded-2xl: 16px (hero cards)
rounded-full: (pills, avatars)
```

### 9.6 Shadows

```
shadow-sm:   0 1px 2px rgba(0,0,0,0.05)    (cards inactive)
shadow:      0 2px 8px rgba(0,0,0,0.08)    (cards hover)
shadow-md:   0 4px 16px rgba(0,0,0,0.10)   (modals)
shadow-lg:   0 8px 32px rgba(0,0,0,0.12)   (dropdowns, toasts)
```

### 9.7 Component Variants

**Button:**
- `gradient`: bg-gradient primary→secondary, text-white (CTA chính)
- `outline`: border-primary, text-primary (hành động phụ)
- `ghost`: transparent, hover bg-surface-variant (hành động nhẹ)
- `danger`: bg-error, text-white (xóa, hủy)
- Sizes: `sm` | `md` (default) | `lg`
- States: hover, active, disabled (opacity-50), loading (spinner replace text)

**Input:**
- Border: outline-gray-200, focus:outline-primary
- Label: text-label floating hoặc stacked
- Error: outline-error + error message text-error below
- Hint: text-caption text-gray-500 below

**Badge/Status:**
- `active`: bg-green-100, text-green-700 → "Đang dùng"
- `completed`: bg-gray-100, text-gray-600 → "Đã hoàn thành"
- `expired`: bg-red-100, text-red-700 → "Hết hạn"
- `ai`: bg-purple-100, text-purple-700 → "AI"
- `db`: bg-blue-100, text-blue-700 → "Cơ sở dữ liệu"

### 9.8 Icons

Sử dụng Heroicons (outline style mặc định, solid cho active states)  
Size chuẩn: w-5 h-5 (inline), w-6 h-6 (action buttons), w-8 h-8 (feature cards)

### 9.9 Motion / Animation

- Transitions: 150ms ease-in-out (hover states)
- Modal: fade + scale (200ms)
- Toast: slide-in từ phải (300ms)
- Typing indicator: bounce dots (CSS animation)
- Accordion: max-height transition (200ms)
- Loading skeleton: shimmer animation

---

## 10. Component Breakdown

### 10.1 Layout Components

```
AppNavbar
├── Logo/Brand
├── Desktop: Nav links (horizontal)
├── Search trigger button → MarketDrugSearchModal
├── Notification bell (badge + dropdown)
├── User avatar menu (profile, logout)
└── Mobile: hamburger → AppSidebar overlay

AppSidebar
├── User mini-profile card
├── Nav items with icons
│   ├── Tổng quan (/dashboard)
│   ├── Đơn thuốc (/profile/prescriptions)
│   ├── Hồ sơ khám (/profile/health)
│   ├── Tra cứu thuốc (/drugs)
│   ├── Kiểm tra tương tác (/interactions)
│   ├── Chatbot AI (/chatbot)
│   ├── Gợi ý thuốc (/recommendations)
│   └── Lịch uống thuốc (/schedule)
└── Bottom: Profile link, Logout

AdminSidebar
├── Brand
└── Nav items
    ├── Người dùng (/admin/users)
    ├── Thuốc (/admin/drugs)
    ├── Tương tác (/admin/interactions)
    └── Nhật ký (/admin/logs)
```

### 10.2 UI Primitives

| Component | Props | Events |
|-----------|-------|--------|
| AppButton | variant, size, loading, disabled | click |
| AppInput | label, type, error, hint, modelValue | update:modelValue |
| AppSelect | label, options, error, modelValue | update:modelValue |
| AppTextarea | label, rows, error, modelValue | update:modelValue |
| AppModal | title, size, modelValue, hideFooter | update:modelValue, confirm |
| AppPagination | total, page, size | update:page, update:size |
| AppBadge | variant, size | — |
| AppAlert | type (info/warning/error/success) | close |
| AppToast | message, type, duration | close |
| AppConfirmDialog | title, message, dangerMode | confirm, cancel |
| AppSkeleton | width, height, rounded | — |
| AppSpinner | size, color | — |
| AppEmptyState | icon, title, description, action | action-click |
| StatCard | icon, value, label, change, changeType | — |
| AppAvatar | src, name, size | — |
| OtpInput | length (6) | complete |

### 10.3 Drug Components

```
MarketDrugSearchField
├── Input với debounce 300ms
├── Dropdown results (product_name, dosage_form, registration_number)
├── Selected state: chip với tên + X button
└── Loading spinner

MarketDrugSearchModal
├── Search input (full-width)
├── Results list (scrollable)
│   └── ProductCard: name, dosage_form, registration, ingredient_summary
└── Empty state / loading state

DrugSearchCombobox
├── Input với debounce 300ms
├── Dropdown: generic_name + id badge
└── Loading state

DrugInteractionCard
├── Drug pair header
├── Source badge (DB/AI) + confidence bar
├── Event type badge
├── Interaction label
└── Expand for details

MedicationCard
├── Drug name + AI badge (if ai_sourced)
├── dosage + frequency + duration
├── Market product link (if market_product_id)
└── Edit / Remove actions
```

### 10.4 Chat Components

```
ChatMessage
├── role="user": bubble phải, màu primary
├── role="assistant": bubble trái, màu surface, markdown rendered
├── Timestamp (hover)
└── Copy button (hover)

ChatTypingIndicator
└── 3 dots bounce animation

ChatSidebar
├── Search/filter input
├── Grouped by date
│   └── SessionItem: first message preview + date
└── Clear all button
```

### 10.5 Notification Components

```
NotificationBell
├── Bell icon
├── Badge (unread_count, hidden if 0)
└── Dropdown (click)
    ├── Header: "Thông báo" + "Đọc tất cả" button
    ├── List (max 10, scrollable)
    │   └── NotificationItem
    │       ├── Icon (type-based)
    │       ├── Title + body (truncated)
    │       ├── Time ago
    │       └── Unread indicator dot
    └── Footer: "Xem tất cả" link

NotificationToast (realtime push)
└── Toast với icon + title + body (5s auto-dismiss)
```

---

## 11. State Management

### 11.1 Pinia Stores

#### auth.store.ts
```typescript
interface AuthState {
  user: UserResponse | null
  initialized: boolean
}

// Computed
isAuthenticated: boolean    // user !== null
isAdmin: boolean            // user?.role === 'admin'

// Actions
setTokens(access: string, refresh: string): void
clearAuth(): void
fetchCurrentUser(): Promise<void>    // GET /auth/me
initialize(): Promise<void>          // Load token + fetch user on app start
logout(): Promise<void>              // POST /auth/logout + clearAuth()
```

**Storage:** Access token trong memory (reactive ref), Refresh token trong localStorage

#### ui.store.ts
```typescript
interface UiState {
  sidebarOpen: boolean
  notificationDropdownOpen: boolean
  commandPaletteOpen: boolean     // ⌘K search modal
}
```

#### notification.store.ts (cần thêm nếu chưa có)
```typescript
interface NotificationState {
  items: Notification[]
  unreadCount: number
  wsConnected: boolean
}

// Actions
connect(token: string): void        // Kết nối WebSocket
disconnect(): void
markAsRead(id: number): Promise<void>
markAllRead(): Promise<void>
addNotification(n: Notification): void
```

### 11.2 TanStack Query Patterns

```typescript
// Query keys convention
['prescriptions', { page, size, search, status }]
['prescription', id]
['prescription-interactions', id]
['drugs', { page, size, search }]
['drug', id]
['drug-interactions', id, { page, size }]
['market-drug', id]
['health-profiles', { page, size, search }]
['chat-history', { page }]
['notifications', { page, unread_only }]
['reminders']
['today-schedule']
['user-me']
['admin-stats']
['admin-users', params]
```

**Stale time recommendations:**
- Drug catalog: 10 phút (ít thay đổi)
- Interactions: 5 phút
- Prescriptions: 1 phút (user data)
- Chat history: 30 giây
- Admin stats: 2 phút

### 11.3 Token Management (axios.ts)

```typescript
// tokenManager singleton
{
  getAccessToken(): string | null
  getRefreshToken(): string | null
  setTokens(access, refresh): void
  clearTokens(): void
}

// Request interceptor: thêm Authorization header
// Response interceptor:
//   401 → try refresh token → retry original request
//   Refresh fails → clearAuth() → redirect /login
```

---

## 12. API Integration Plan

### 12.1 Base Config

```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})
```

### 12.2 Error Handling Convention

```typescript
// Wrapper để normalize lỗi API
function handleApiError(error: AxiosError): AppError {
  if (error.response?.status === 401) return { type: 'unauthorized' }
  if (error.response?.status === 403) return { type: 'forbidden' }
  if (error.response?.status === 422) {
    // Validation errors từ FastAPI
    return { type: 'validation', fields: error.response.data.detail }
  }
  const msg = error.response?.data?.detail || 'Lỗi không xác định'
  return { type: 'api', message: msg }
}
```

### 12.3 File Download Pattern

```typescript
// Excel export
async function downloadExcel(url: string, body: any, filename: string) {
  const response = await api.post(url, body, { responseType: 'blob' })
  const href = URL.createObjectURL(response.data)
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  a.click()
  URL.revokeObjectURL(href)
}
```

### 12.4 File Upload Pattern

```typescript
// Avatar upload
async function uploadAvatar(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/users/me/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
```

### 12.5 WebSocket Pattern

```typescript
class NotificationWebSocket {
  private ws: WebSocket | null = null
  private reconnectDelay = 1000
  private maxDelay = 30000

  connect(token: string) {
    const wsUrl = `${WS_BASE_URL}/notifications/ws?token=${token}`
    this.ws = new WebSocket(wsUrl)
    this.ws.onmessage = this.handleMessage
    this.ws.onclose = this.handleClose // → scheduleReconnect
    // Ping every 30s
  }
}
```

---

## 13. Validation Rules

### 13.1 Client-side (Zod Schemas)

#### Password
```typescript
const passwordSchema = z.string()
  .min(6, 'Mật khẩu tối thiểu 6 ký tự')
  .regex(/[A-Z]/, 'Cần có ít nhất 1 chữ hoa')
  .regex(/[a-z]/, 'Cần có ít nhất 1 chữ thường')
  .regex(/\d/, 'Cần có ít nhất 1 chữ số')
  .regex(/[@$!%*?&]/, 'Cần có ít nhất 1 ký tự đặc biệt (@$!%*?&)')
```

#### Username
```typescript
const usernameSchema = z.string()
  .min(3, 'Tối thiểu 3 ký tự')
  .max(30, 'Tối đa 30 ký tự')
  .regex(/^[a-zA-Z0-9_]+$/, 'Chỉ được dùng chữ cái, số và dấu _')
```

#### Email
```typescript
const emailSchema = z.string().email('Email không hợp lệ')
```

#### Prescription
```typescript
const prescriptionSchema = z.object({
  name: z.string().min(1, 'Tên đơn thuốc không được trống').max(200),
  status: z.enum(['active', 'completed']),
  notes: z.string().max(1000).optional(),
  items: z.array(prescriptionItemSchema).min(1, 'Cần ít nhất 1 thuốc')
})

const prescriptionItemSchema = z.object({
  drug_name: z.string().min(1).max(200),
  dosage: z.string().min(1, 'Liều dùng không được trống').max(100),
  frequency: z.string().max(100).optional(),
  duration: z.string().max(100).optional(),
  market_product_id: z.number().int().positive().optional().nullable(),
  drug_id: z.string().optional().nullable()
})
```

#### Health Profile
```typescript
const healthProfileSchema = z.object({
  diagnosis_name: z.string().min(1).max(200),
  exam_date: z.string().refine(isValidDate, 'Ngày không hợp lệ'),
  facility: z.string().max(200).optional(),
  doctor: z.string().max(100).optional(),
  // ...
})
```

#### Reminder
```typescript
const reminderSchema = z.object({
  drug_name: z.string().min(1).max(200),
  reminder_time: z.string().regex(/^\d{2}:\d{2}$/, 'Định dạng HH:MM'),
  frequency: z.enum(['daily', 'custom']),
  days_of_week: z.string().optional()
    .refine((val, ctx) => {
      if (ctx.parent.frequency === 'custom' && !val) return false
      return true
    }, 'Chọn ít nhất 1 ngày')
})
```

### 13.2 Server-side Error Display

Khi API trả về 422 với `detail` là array:
```typescript
// Map field path đến field error
const fieldErrors = error.detail.reduce((acc, err) => {
  const field = err.loc.slice(1).join('.')  // bỏ "body"
  acc[field] = err.msg
  return acc
}, {})

// Hiển thị dưới mỗi field tương ứng
```

### 13.3 Business Rule Validation (Client)

| Rule | Nơi check | Message |
|------|-----------|---------|
| Prescription chỉ xóa khi completed | Delete button disabled | "Chỉ xóa đơn thuốc đã hoàn thành" |
| Interaction check cần ≥ 2 drugs | Disable button | "Thêm ít nhất 2 thuốc để kiểm tra" |
| Market interaction max 10 | Disable add button | "Tối đa 10 thuốc" |
| Generic interaction max 20 | Disable add button | "Tối đa 20 thuốc" |
| Chatbot message max 2000 chars | Counter + disable | "Tối đa 2000 ký tự" |
| Recommendation symptoms min 10 | Disable button | "Nhập ít nhất 10 ký tự" |

---

## 14. Loading / Error / Empty States

### 14.1 Loading States

| Context | Pattern |
|---------|---------|
| Page load | Full skeleton layout (matching page structure) |
| List/table | Row skeletons (3-5 rows) |
| Card data | Card skeleton (rounded rect placeholders) |
| Button action | Spinner replace text + disabled |
| Search debounce | Spinner in input right icon |
| Chat AI response | Typing indicator bubble |
| Avatar upload | Overlay + progress ring |

### 14.2 Error States

| Error Type | Display | Action |
|------------|---------|--------|
| Network error | Full-page error với retry button | Retry |
| 401 Unauthorized | Redirect /login (silent) | — |
| 403 Forbidden | /forbidden page | Về trang chủ |
| 404 Not Found | /not-found page | Về trang chủ |
| 422 Validation | Inline field errors | Fix fields |
| 500 Server Error | Toast + error detail | Report / Retry |
| WS disconnect | Banner "Đã mất kết nối, đang kết nối lại..." | Auto retry |
| Upload fail | Toast + form reset | Retry |

### 14.3 Empty States

| Screen | Empty Message | Action |
|--------|--------------|--------|
| Prescriptions | "Bạn chưa có đơn thuốc nào" | + Tạo đơn thuốc |
| Health profiles | "Chưa có hồ sơ khám bệnh" | + Thêm hồ sơ |
| Drug search (no query) | "Nhập tên thuốc để tìm kiếm" | — |
| Drug search (no results) | "Không tìm thấy thuốc khớp với..." | Thử từ khóa khác |
| Chat (first open) | Quick suggestions (6 chips) | — |
| Notifications | "Chưa có thông báo nào" | — |
| Reminders | "Chưa có lịch nhắc thuốc" | + Thêm lịch |
| Activity logs | "Chưa có hoạt động nào" | — |
| Admin: no users found | "Không tìm thấy người dùng" | — |

---

## 15. Permission Matrix

### 15.1 Route Access

| Route | Guest | User | Admin |
|-------|-------|------|-------|
| / | ✅ | ✅ | ✅ |
| /login, /register | ✅ | ❌→/dashboard | ❌→/dashboard |
| /dashboard | ❌→/login | ✅ | ✅ |
| /profile/* | ❌→/login | ✅ | ❌ (no sidebar link, but accessible) |
| /drugs, /drugs/:id | ✅ | ✅ | ✅ |
| /market-drugs/:id | ✅ | ✅ | ✅ |
| /interactions | ❌→/login | ✅ | ✅ |
| /chatbot | ❌→/login | ✅ | ✅ |
| /recommendations | ❌→/login | ✅ | ✅ |
| /schedule | ❌→/login | ✅ | ✅ |
| /admin/* | ❌→/login | ❌→/forbidden | ✅ |

### 15.2 Feature-level Permissions

| Feature | Condition | Fallback |
|---------|-----------|----------|
| Đổi mật khẩu | auth_provider = local | Tab ẩn |
| Xóa đơn thuốc | status = completed | Button disabled |
| Export Excel (interactions) | isAuthenticated | Button ẩn |
| Kiểm tra tương tác prescription | items có ≥ 2 drug_id | Button disabled + tooltip |
| Admin stats | isAdmin | Component không render |
| Toggle user active | isAdmin | — |
| Import demo market drugs | isAdmin | — |

---

## 16. Responsive Behavior

### 16.1 Breakpoints

| Name | Min Width | Target |
|------|-----------|--------|
| xs | 0px | Mobile portrait |
| sm | 640px | Mobile landscape |
| md | 768px | Tablet |
| lg | 1024px | Desktop |
| xl | 1280px | Large desktop |

### 16.2 Layout Changes

**AppNavbar:**
- Mobile (< md): Chỉ hiện Logo + Hamburger + Notification bell
- Desktop (≥ md): Full nav links + search trigger + user menu

**AppSidebar:**
- Mobile: Hidden, slide-in từ trái khi hamburger click (overlay + backdrop)
- Desktop: Fixed left (240px width), always visible

**Main Content:**
- Mobile: full width (100%)
- Desktop: width - sidebar (calc(100% - 240px))

**Dashboard:**
- Mobile: Single column
- Desktop: 2-column (main 70% + sidebar 30%)

**Drug Search Results:**
- Mobile: Card list (stacked)
- Desktop: Table với columns

**Interaction Checker:**
- Mobile: Single column inputs + stacked results
- Desktop: 2-column form + full-width results

**Chat:**
- Mobile: Sidebar ẩn, full-width chat
- Desktop: Sidebar (280px) + chat area

**Admin Tables:**
- Mobile: Horizontal scroll
- Desktop: Full table

### 16.3 Touch Targets

- Minimum tap target: 44×44px
- Spacing giữa các action buttons ≥ 8px
- Modal: full-screen trên mobile (< sm)

---

## 17. Wireframe / Layout Description

### 17.1 App Layout (Desktop)

```
┌─────────────────────────────────────────────────────────────┐
│  NAVBAR (64px height, sticky)                               │
│  [Logo] [Nav links...]    [⌘K Search] [🔔] [👤 Menu]       │
├──────────────┬──────────────────────────────────────────────┤
│   SIDEBAR    │  MAIN CONTENT AREA                           │
│   (240px)    │                                              │
│  ┌─────────┐ │  ┌────────────────────────────────────────┐  │
│  │ Profile │ │  │  Page Title + Breadcrumb               │  │
│  │ mini    │ │  ├────────────────────────────────────────┤  │
│  ├─────────┤ │  │                                        │  │
│  │ Nav     │ │  │  Content (variable)                    │  │
│  │ Items   │ │  │                                        │  │
│  │         │ │  │                                        │  │
│  │         │ │  │                                        │  │
│  ├─────────┤ │  └────────────────────────────────────────┘  │
│  │ Profile │ │                                              │
│  │ Logout  │ │                                              │
│  └─────────┘ │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

### 17.2 Dashboard Layout

```
┌────────────────────────────────────────────────────────────┐
│  HERO CARD (gradient, 120px)                               │
│  "Xin chào, Nguyễn Văn A 👋"                              │
│  Subtitle + greeting based on time                         │
├──────────┬──────────┬──────────┬──────────┤
│ 💬 Chat  │ 💊 Đơn  │ ⚡ Check │ 🔍 Tìm  │  ← Quick Actions
│  AI      │ thuốc   │ tương tác│ thuốc   │
├──────────┴──────────┴──────────┴──────────┤
│  Thống kê đơn thuốc         Tuân thủ      │
│  ┌──────┐ ┌──────┐ ┌──────┐  ◯ 92% tuần  │
│  │  12  │ │  8   │ │  4   │  ◯ 88% tháng │
│  │ Tổng │ │Đang  │ │Hoàn  │              │
│  │      │ │dùng  │ │thành │              │
│  └──────┘ └──────┘ └──────┘              │
├────────────────────────┬───────────────────┤
│  Đơn thuốc gần đây     │  Hoạt động gần đây│
│  ┌────────────────────┐│ ─────────────────  │
│  │ Đơn 1  active  ... ││ • Đăng nhập 2p    │
│  │ Đơn 2  completed...││ • Tạo đơn thuốc 1h│
│  │ Đơn 3  active  ... ││ • Tra cứu thuốc 3h│
│  └────────────────────┘│                   │
└────────────────────────┴───────────────────┘
```

### 17.3 Prescription List Layout

```
┌────────────────────────────────────────────────────────┐
│  Đơn thuốc của tôi              [+ Tạo đơn thuốc]      │
├────────────────────────────────────────────────────────┤
│  [🔍 Tìm kiếm...]    [Trạng thái ▼]     [□ Chọn tất cả]│
├──┬──────────────────┬─────────┬────────┬────────┬──────┤
│□ │ Tên đơn          │ Số thuốc│ Trạng  │ Ngày   │ ...  │
├──┼──────────────────┼─────────┼────────┼────────┼──────┤
│□ │ Đơn khám định kỳ│    3    │🟢 Đang │16/05   │ ⋮    │
│□ │ Đơn cảm cúm      │    2    │⚫ Hoàn │15/05   │ ⋮    │
├──┴──────────────────┴─────────┴────────┴────────┴──────┤
│                   ← 1 2 3 ... →                        │
└────────────────────────────────────────────────────────┘
```

### 17.4 Interaction Checker Layout

```
┌────────────────────────────────────────────────────────┐
│  Kiểm tra tương tác thuốc                              │
├────────────────────────────────────────────────────────┤
│  [Thuốc thương mại]  [Thuốc hoạt chất]  ← Mode tabs    │
├────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────┐  │
│  │ + Thêm thuốc...                 🔍                │  │
│  │ ┌─────────────────────────────────────────┐       │  │
│  │ │ Paracetamol 500mg (DAV-001)          [×]│       │  │
│  │ │ Ibuprofen 400mg (DAV-002)            [×]│       │  │
│  │ └─────────────────────────────────────────┘       │  │
│  │                        [Kiểm tra tương tác]        │  │
│  └───────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────┤
│  ⚠️ Phát hiện 1 tương tác (2 cặp an toàn)              │
│  ┌───────────────────────────────────────────────────┐  │
│  │ ⚡ Paracetamol × Ibuprofen                        │  │
│  │ Loại: Tăng tác dụng phụ tiêu hóa                  │  │
│  │ Nguồn: 🗄️ Cơ sở dữ liệu | Độ tin cậy: 95%         │  │
│  └───────────────────────────────────────────────────┘  │
│  ▶ 2 cặp an toàn                                        │
└────────────────────────────────────────────────────────┘
```

### 17.5 Chatbot Layout

```
┌──────────────────────────────────────────────────────────┐
│ [☰ History]       Chatbot AI Sức khỏe              [⚙️]   │
├──────────────────────────────────────────────────────────┤
│  📋 Đang dùng: Paracetamol, Ibuprofen (từ profile)       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│           🤖 Xin chào! Tôi là trợ lý AI sức khỏe...    │
│                                                          │
│    ╭─────────────────────────────────╮                   │
│    │ Tôi đang bị đau đầu và sốt nhẹ │  → User bubble    │
│    ╰─────────────────────────────────╯                   │
│                                                          │
│ ╭──────────────────────────────────────────────╮         │
│ │ Dựa vào triệu chứng của bạn, đây là...      │ ← AI    │
│ │ 1. Nghỉ ngơi...                              │         │
│ │ 2. Uống đủ nước...                           │         │
│ ╰──────────────────────────────────────────────╯         │
│                                                          │
│ ●●●  ← Typing indicator                                  │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────┐  │
│  │ Nhập câu hỏi... (Enter gửi, Shift+Enter xuống dòng)│  │
│  └───────────────────────────────────────[📤 Gửi]─────┘  │
└──────────────────────────────────────────────────────────┘
```

### 17.6 Auth Form Layout (Centered)

```
┌──────────────────────────────────────────────────┐
│                  [Logo Medis]                    │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │         Đăng nhập vào Medis                │  │
│  │                                            │  │
│  │  Tên đăng nhập                             │  │
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │                                      │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  │                                            │  │
│  │  Mật khẩu                    [👁️]           │  │
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │                                      │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  │                                            │  │
│  │  [         Đăng nhập         ]             │  │
│  │                                            │  │
│  │  ─────────────── hoặc ─────────────────   │  │
│  │                                            │  │
│  │  [G  Tiếp tục với Google]                  │  │
│  │                                            │  │
│  │  Chưa có tài khoản? Đăng ký               │  │
│  │  Quên mật khẩu?                           │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 17.7 Admin Layout

```
┌─────────────────────────────────────────────────────────────┐
│  ADMIN NAVBAR                                               │
│  [Medis Admin]                              [👤 admin@...]  │
├──────────────┬──────────────────────────────────────────────┤
│ ADMIN SIDEBAR│  ADMIN CONTENT                               │
│  ┌─────────┐ │  ┌──────────────────────────────────────┐   │
│  │ Medis   │ │  │  Stats row: Total Users, Active,...  │   │
│  │ Admin   │ │  ├──────────────────────────────────────┤   │
│  ├─────────┤ │  │  [🔍 Search] [Role ▼] [Active ▼]     │   │
│  │👤 Users │ │  ├──────────────────────────────────────┤   │
│  │💊 Thuốc │ │  │  Table with pagination               │   │
│  │⚡ TTT   │ │  │                                      │   │
│  │📋 Logs  │ │  │                                      │   │
│  └─────────┘ │  └──────────────────────────────────────┘   │
└──────────────┴──────────────────────────────────────────────┘
```

---

## Phụ lục: Các Điểm Cần Chú Ý Khi Triển Khai

### A. Backend gaps / Cần bổ sung

| Gap | Mô tả | Giải pháp frontend tạm |
|-----|-------|------------------------|
| Onboarding check | Không có endpoint check `onboarding_completed` nhanh | GET /users/me/onboarding sau login |
| Drug search modal | AppNavbar search chưa kết nối | Sử dụng MarketDrugSearchModal đã tạo |
| Notification WS multiple tabs | Backend hỗ trợ connection list per user | Frontend chỉ dùng 1 tab WS |

### B. Chức năng chỉ ở frontend

| Feature | Mô tả |
|---------|-------|
| Compliance rings | Tính từ prescription items + reminders (frontend calculation) |
| Session timeout warning | Modal cảnh báo 5 phút trước khi token hết hạn |
| Offline detection | Banner "Không có kết nối mạng" |
| Print interactions | Window.print() với CSS print media query |

### C. Missing pages cần hoàn thiện

| Page | Status | Priority |
|------|--------|----------|
| PrescriptionDetailView | Route có, cần verify implementation | High |
| DrugDetailView | Route có, cần verify | High |
| HealthProfileDetailView | Route có, cần verify | Medium |
| ScheduleView | Route có, cần verify full implementation | High |
| Onboarding flow | Chưa có route, chỉ có API | High |

---

*Tài liệu này được tạo từ phân tích toàn bộ source code backend và frontend của Medis tính đến ngày 2026-05-16.*
