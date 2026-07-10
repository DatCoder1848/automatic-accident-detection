# Hướng Dẫn Chạy Project — Automatic Accident Detection

## Yêu Cầu Hệ Thống

| Tool | Version |
|------|---------|
| Node.js | >= 20 |
| Python | >= 3.10 |
| npm | >= 9 |
| Git | latest |

---

## 1. Clone Project

```bash
git clone https://github.com/DatCoder1848/automatic-accident-detection.git
cd automatic-accident-detection
```

---

## 2. Backend API (NestJS)

### Cài đặt

```bash
cd backend_api
npm install
```

### Cấu hình `.env`

Tạo file `backend_api/.env`:

```env
# Supabase PostgreSQL
DATABASE_URL="postgresql://postgres.gviszhjxiyijcafobrts:[PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?pgbouncer=true"
DIRECT_URL="postgresql://postgres.gviszhjxiyijcafobrts:[PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

# JWT
JWT_SECRET="super-secret-key-change-in-production"

# AI Service
AI_SERVICE_API_KEY="ai-service-secret-key"

# Supabase Storage
SUPABASE_URL="https://gviszhjxiyijcafobrts.supabase.co"
SUPABASE_SERVICE_KEY="your-supabase-service-role-key"
```

> ⚠️ Thay `[PASSWORD]` bằng password thật từ Supabase Dashboard → Settings → Database

### Generate Prisma Client

```bash
npx prisma generate
```

### Chạy Migration (lần đầu)

```bash
npx prisma migrate dev --name init
```

### Seed Data (tạo user + camera mẫu)

```bash
npx tsx prisma/seed.ts
```

### Chạy Backend

```bash
npm run start:dev
```

Backend chạy tại: **http://localhost:3000**

### Tài khoản mẫu

| Email | Password | Role |
|-------|----------|------|
| admin@system.com | admin123 | ADMIN |
| operator@system.com | operator123 | OPERATOR |

---

## 3. Frontend Dashboard (React + Vite)

### Cài đặt

```bash
cd frontend_dashboard
npm install
```

### Chạy Frontend

```bash
npm run dev
```

Frontend chạy tại: **http://localhost:5173**

### Đăng nhập

Dùng tài khoản ở bảng trên → vào Dashboard.

---

## 4. AI Engine (Python)

### Cài đặt

```bash
cd ai_engine
pip install -r ../requirements.txt
```

### Chạy AI Detection

```bash
python main_ai.py --source path/to/video.mp4
```

Hoặc chỉ định camera ID:

```bash
python main_ai.py --source path/to/video.mp4 --camera-id <UUID>
```

> AI sẽ tự detect tai nạn và gửi kết quả lên backend qua API.

---

## 5. Kiểm Tra Hệ Thống

### Test API endpoints

```bash
# Health check
curl http://localhost:3000/

# Login
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@system.com","password":"admin123"}'

# Get cameras (cần JWT token)
curl http://localhost:3000/cameras \
  -H "Authorization: Bearer <TOKEN>"

# Simulate AI gửi accident (dùng API key)
curl -X POST http://localhost:3000/accidents \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ai-service-secret-key" \
  -d '{"cameraId":"<CAMERA_UUID>","confidence":0.85,"severity":"HIGH"}'
```

---

## 6. Cấu Trúc Thư Mục

```
automatic-accident-detection/
├── ai_engine/              # AI detection (Python + YOLOv8)
│   ├── main_ai.py          # Pipeline chính
│   ├── kinematics.py       # Tracking + IoU
│   ├── api_client.py       # Gọi API backend
│   └── video_utils.py      # Trích xuất video
├── backend_api/            # REST API (NestJS + Prisma)
│   ├── src/
│   │   ├── auth/           # JWT login/register
│   │   ├── users/          # CRUD users
│   │   ├── cameras/        # CRUD cameras
│   │   ├── accidents/      # CRUD accidents
│   │   ├── alerts/         # Alert management
│   │   ├── events/         # WebSocket gateway
│   │   └── upload/         # Video upload (Supabase Storage)
│   └── prisma/             # Schema + migrations
├── frontend_dashboard/     # Dashboard UI (React + Ant Design)
│   └── src/
│       ├── pages/          # Dashboard, Cameras, Accidents, Alerts, Login
│       ├── components/     # Layout, ProtectedRoute
│       └── hooks/          # useSocket (real-time)
└── data_storage/           # Video clips (positive/negative)
```

---

## 7. Ports

| Service | Port | URL |
|---------|------|-----|
| Backend API | 3000 | http://localhost:3000 |
| Frontend | 5173 | http://localhost:5173 |
| WebSocket | 3000 | ws://localhost:3000 |

---

## Troubleshooting

| Vấn đề | Giải pháp |
|--------|-----------|
| Port 3000 bị chiếm | Tắt app khác hoặc set `PORT=3001` |
| Prisma migrate bị treo | Đảm bảo dùng `DIRECT_URL` (port 5432), không phải pooler (6543) |
| Frontend 401 redirect loop | Xóa localStorage → login lại |
| AI không gửi được lên backend | Kiểm tra backend đang chạy + `AI_SERVICE_API_KEY` khớp |
