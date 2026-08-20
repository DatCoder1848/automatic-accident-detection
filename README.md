# 🚨 Automatic Accident Detection System

Real-time traffic accident detection system using AI computer vision, with instant alerts and video evidence.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              AUTOMATIC ACCIDENT DETECTION                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌──────────────────┐                    ┌────────────────────┐                     │
│  │   🎥 AI Engine   │   POST /accidents  │   🖥️  Backend API  │                     │
│  │  ─────────────── │ ─────────────────→ │  ─────────────────  │                     │
│  │  Python + YOLOv8 │   X-API-Key auth   │   NestJS + Prisma  │                     │
│  │  OpenCV + BEV    │                    │   JWT + WebSocket  │                     │
│  │  ByteTrack       │   GET /cameras     │                    │                     │
│  │                  │ ←───────────────── │                    │                     │
│  └──────────────────┘   (fetch config)   └─────────┬──────────┘                     │
│         │                                          │                                │
│         │ Upload to                                │ CRUD + Real-time               │
│         ▼ Cloudinary                               ▼                                │
│  ┌──────────────────┐                    ┌────────────────────┐                     │
│  │  ☁️  Cloudinary   │                    │  🐘 Supabase       │                     │
│  │  (Video/Image)   │                    │  PostgreSQL + Store │                     │
│  └──────────────────┘                    └─────────┬──────────┘                     │
│                                                    │                                │
│                                          socket.io │ WebSocket                      │
│                                                    ▼                                │
│                                          ┌────────────────────┐                     │
│                                          │  🌐 Frontend        │                     │
│                                          │  React + Ant Design │                     │
│                                          │  Real-time Dashboard│                     │
│                                          └────────────────────┘                     │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ERD (Entity Relationship Diagram)

```
┌─────────────────────────┐       ┌──────────────────────────────────┐
│         USERS            │       │            CAMERAS                │
├─────────────────────────┤       ├──────────────────────────────────┤
│ PK  id          UUID     │       │ PK  id            UUID            │
│     email       VARCHAR  │◄──┐   │     name          VARCHAR         │
│     password    VARCHAR  │   │   │     location      VARCHAR         │
│     name        VARCHAR? │   │   │     stream_url    VARCHAR         │
│     role        ENUM     │   │   │     status        ENUM            │
│     created_at  DATETIME │   │   │     ai_config     JSONB?          │
│     updated_at  DATETIME │   │   │     created_at    DATETIME        │
└─────────────────────────┘   │   │     updated_at    DATETIME        │
                               │   └───────────────┬──────────────────┘
                               │                   │
                               │                   │ 1:N
                               │                   ▼
┌─────────────────────────┐   │   ┌──────────────────────────────────┐
│         ALERTS           │   │   │           ACCIDENTS               │
├─────────────────────────┤   │   ├──────────────────────────────────┤
│ PK  id          UUID     │   │   │ PK  id              UUID          │
│ FK  accident_id UUID     │───┼──►│     incident_id     VARCHAR?      │
│ FK  user_id    UUID      │───┘   │ FK  camera_id       UUID          │
│     type       ENUM      │       │     detected_at     DATETIME      │
│     status     ENUM      │       │     confidence      FLOAT         │
│     message    VARCHAR?  │       │     severity        ENUM          │
│     sent_at    DATETIME  │       │     status          ENUM          │
│     read_at    DATETIME? │       │     video_clip_url  VARCHAR?      │
└─────────────────────────┘       │     thumbnail_url   VARCHAR?      │
                                   │     vehicles_involved TEXT[]       │
                                   │     latitude        FLOAT?        │
                                   │     longitude       FLOAT?        │
                                   │     description     VARCHAR?      │
                                   │     created_at      DATETIME      │
                                   │     updated_at      DATETIME      │
                                   └──────────────────────────────────┘

Relationships:
  Camera  1 ──── N  Accident    (một camera có nhiều accidents)
  Accident 1 ──── N  Alert      (một accident tạo alerts cho nhiều users)
  User    1 ──── N  Alert       (một user nhận nhiều alerts)
```

### Enums

| Enum | Values |
|------|--------|
| Role | `ADMIN`, `OPERATOR`, `VIEWER` |
| CameraStatus | `ACTIVE`, `INACTIVE`, `MAINTENANCE` |
| AccidentSeverity | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| AccidentStatus | `PENDING`, `CONFIRMED`, `FALSE_ALARM`, `RESOLVED` |
| AlertType | `NOTIFICATION`, `EMAIL`, `SMS` |
| AlertStatus | `UNREAD`, `READ`, `DISMISSED` |

---

## Sequence Diagram — Accident Detection Flow

```
┌────────┐          ┌────────┐          ┌────────┐          ┌────────┐          ┌────────┐
│   AI   │          │Cloudinary│         │Backend │          │  DB    │          │Frontend│
│ Engine │          │         │          │  API   │          │Supabase│          │Dashboard│
└───┬────┘          └───┬────┘          └───┬────┘          └───┬────┘          └───┬────┘
    │                   │                   │                   │                   │
    │ 1. Detect accident                    │                   │                   │
    │──────────────────────────────────────►│                   │                   │
    │   POST /accidents (no video yet)      │                   │                   │
    │                                       │ 2. Save to DB     │                   │
    │                                       │──────────────────►│                   │
    │                                       │                   │                   │
    │                                       │ 3. Create alerts  │                   │
    │                                       │──────────────────►│                   │
    │                                       │                   │                   │
    │                                       │ 4. Emit WebSocket "new-accident"      │
    │                                       │──────────────────────────────────────►│
    │                                       │                   │                   │
    │                                       │                   │        5. 🚨 Popup│
    │                                       │                   │         notification
    │                                       │                   │                   │
    │ 6. Upload video                       │                   │                   │
    │──────────────►│                       │                   │                   │
    │               │ 7. Return URL         │                   │                   │
    │◄──────────────│                       │                   │                   │
    │                                       │                   │                   │
    │ 8. POST /accidents with videoClipUrl  │                   │                   │
    │──────────────────────────────────────►│                   │                   │
    │                                       │ 9. Update record  │                   │
    │                                       │──────────────────►│                   │
    │                                       │                   │                   │
    │                                       │ 10. Emit "accident-video-ready"       │
    │                                       │──────────────────────────────────────►│
    │                                       │                   │                   │
    │                                       │                   │       11. Show    │
    │                                       │                   │         video     │
    │                                       │                   │                   │
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| AI Engine | Python, YOLOv8, OpenCV, ByteTrack | Vehicle detection + tracking |
| AI Calibration | Bird's Eye View (BEV), Homography | Speed/distance measurement |
| Backend API | NestJS 11, Prisma 7, TypeScript | REST API + business logic |
| Database | PostgreSQL (Supabase) | Persistent storage |
| File Storage | Cloudinary | Video clips + thumbnails |
| Real-time | Socket.IO (WebSocket) | Push notifications |
| Frontend | React 19, Vite 8, Ant Design | Dashboard UI |
| State Mgmt | TanStack Query | Server state + caching |
| Auth | JWT (frontend) + API Key (AI service) | Access control |

---

## API Endpoints

### Auth (Public)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login, returns JWT |

### Users (JWT Required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List all users |
| GET | `/users/:id` | Get user by ID |
| POST | `/users` | Create user |
| PATCH | `/users/:id` | Update user |

### Cameras (JWT or API Key)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cameras` | List cameras + aiConfig (filter: `?status=ACTIVE`) |
| GET | `/cameras/:id` | Get camera by ID |
| POST | `/cameras` | Create camera with aiConfig (JWT only) |
| PATCH | `/cameras/:id` | Update camera (JWT only) |
| DELETE | `/cameras/:id` | Delete camera (JWT only) |

### Accidents
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/accidents` | API Key | AI reports accident (returns `id`) |
| GET | `/accidents` | JWT | List (filter: `?severity=&status=&cameraId=`) |
| GET | `/accidents/:id` | JWT | Get detail with camera info |
| PATCH | `/accidents/:id` | JWT | Update status |

### Alerts (JWT Required)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/alerts` | Get alerts (filter: `?userId=`) |
| GET | `/alerts/:id` | Get alert by ID |
| PATCH | `/alerts/:id/read` | Mark as read |

### Upload (API Key)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload/video` | Upload video + link to accident |

---

## WebSocket Events

| Event | Direction | Payload | Trigger |
|-------|-----------|---------|---------|
| `new-accident` | Server → Client | `{id, severity, confidence, ...}` | New accident created |
| `accident-updated` | Server → Client | `{id, status, ...}` | Status changed |
| `accident-video-ready` | Server → Client | `{accidentId, videoClipUrl}` | Video uploaded |

---

## Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                    BACKEND API                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │   Auth    │  │  Users    │  │  Cameras  │       │
│  │  Module   │  │  Module   │  │  Module   │       │
│  └───────────┘  └───────────┘  └───────────┘       │
│                                                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │ Accidents │  │  Alerts   │  │  Upload   │       │
│  │  Module   │  │  Module   │  │  Module   │       │
│  └───────────┘  └───────────┘  └───────────┘       │
│                                                     │
│  ┌───────────┐  ┌───────────┐                       │
│  │  Prisma   │  │  Events   │  (WebSocket Gateway)  │
│  │  Module   │  │  Module   │                       │
│  └───────────┘  └───────────┘                       │
│                                                     │
├─────────────────────────────────────────────────────┤
│  Guards: JwtAuthGuard | ApiKeyGuard | JwtOrApiKey   │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Node.js >= 20
- Python >= 3.10
- Supabase project (PostgreSQL + Storage)

### 1. Backend

```bash
cd backend_api
npm install
cp .env.example .env  # Fill in Supabase credentials
npx prisma generate
npx prisma migrate dev --name init
npx tsx prisma/seed.ts
npm run start:dev
```

- Server: http://localhost:3000
- Swagger: http://localhost:3000/api/docs

### 2. Frontend

```bash
cd frontend_dashboard
npm install
npm run dev
```

- Dashboard: http://localhost:5173

### 3. AI Engine

```bash
cd ai_engine
pip install -r ../requirements.txt
python main_ai.py --source path/to/video.mp4
```

---

## Default Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@system.com | admin123 | ADMIN |
| operator@system.com | operator123 | OPERATOR |

---

## Environment Variables

```env
# Database (add &sslmode=require on Windows)
DATABASE_URL="postgresql://postgres.xxx:[PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?pgbouncer=true"
DIRECT_URL="postgresql://postgres.xxx:[PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

# Auth
JWT_SECRET="your-secret"
AI_SERVICE_API_KEY="ai-service-secret-key"

# Supabase Storage
SUPABASE_URL="https://xxx.supabase.co"
SUPABASE_SERVICE_KEY="your-service-role-key"
```

---

## Project Structure

```
automatic-accident-detection/
├── ai_engine/                  # AI detection (Python + YOLOv8)
│   ├── main_ai.py             # Main detection pipeline
│   ├── kinematics.py          # Vehicle tracking + IoU + BEV
│   ├── api_client.py          # HTTP client for backend API
│   └── video_utils.py         # Video frame extraction
├── backend_api/                # REST API + WebSocket (NestJS)
│   ├── prisma/
│   │   ├── schema.prisma      # Database schema
│   │   ├── migrations/        # SQL migrations
│   │   └── seed.ts            # Seed data (users + cameras)
│   └── src/
│       ├── auth/              # JWT + API key guards
│       ├── users/             # User CRUD
│       ├── cameras/           # Camera CRUD + aiConfig
│       ├── accidents/         # Core accident management
│       ├── alerts/            # Alert notifications
│       ├── events/            # WebSocket gateway
│       ├── upload/            # Video upload service
│       └── prisma/            # Database connection
├── frontend_dashboard/         # Dashboard UI (React + Ant Design)
│   └── src/
│       ├── pages/             # Dashboard, Cameras, Accidents, Alerts, Login
│       ├── components/        # AppLayout, ProtectedRoute
│       ├── hooks/             # useSocket (real-time)
│       └── api/               # Axios client + interceptors
├── data_storage/               # Test video clips
│   └── video_clips/
│       ├── positive/          # Accident videos (crash_1..12.mp4)
│       └── negative/          # Normal traffic (normal_1..9.mp4)
├── API_GUIDE_AI.md            # API guide for AI team
├── SETUP_GUIDE.md             # Full setup instructions
└── README.md                  # This file
```

---

## License

UNLICENSED — University project (HTTM course).
