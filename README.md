# 🚨 Automatic Accident Detection System

Real-time traffic accident detection system using AI computer vision, with instant alerts and video evidence.

## Architecture

```
┌──────────────────┐       POST /accidents        ┌────────────────────┐       ┌──────────────┐
│   AI Engine      │ ──── Thread 1 (instant) ───→ │   Backend API      │ ────→ │  Supabase    │
│ (Python/YOLOv8)  │                              │   (NestJS)         │       │  PostgreSQL  │
│                  │       POST /upload/video      │                    │       └──────────────┘
│                  │ ──── Thread 2 (delayed) ────→ │  ┌──────────────┐ │       ┌──────────────┐
└──────────────────┘                              │  │  WebSocket   │ │ ────→ │  Supabase    │
                                                  │  │  Gateway     │ │       │  Storage     │
                                                  │  └──────┬───────┘ │       └──────────────┘
                                                  └─────────┼─────────┘
                                                            │ socket.io
                                                            ▼
                                                  ┌────────────────────┐
                                                  │  Frontend Dashboard │
                                                  │  (React + Ant Design)│
                                                  └────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Engine | Python, YOLOv8, OpenCV, ByteTrack |
| Backend API | NestJS 11, Prisma 7, TypeScript |
| Frontend | React 19, Vite 8, Ant Design, TanStack Query |
| Database | PostgreSQL (Supabase) |
| Storage | Supabase Storage |
| Real-time | Socket.IO (WebSocket) |
| Auth | JWT + API Key |

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
| GET | `/cameras` | List cameras (filter: `?status=ACTIVE`) |
| GET | `/cameras/:id` | Get camera by ID |
| POST | `/cameras` | Create camera (JWT only) |
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

## WebSocket Events

| Event | Direction | Trigger |
|-------|-----------|---------|
| `new-accident` | Server → Client | New accident created |
| `accident-updated` | Server → Client | Accident status changed |
| `accident-video-ready` | Server → Client | Video evidence uploaded |

## Data Flow (2-Thread Async)

```
AI detects accident
    ├── Thread 1 (instant): POST /accidents → DB save → socket "new-accident" → FE alert popup
    └── Thread 2 (5s later): POST /upload/video → Storage upload → DB update → socket "accident-video-ready" → FE shows video
```

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

Server: http://localhost:3000
Swagger: http://localhost:3000/api/docs

### 2. Frontend

```bash
cd frontend_dashboard
npm install
npm run dev
```

Dashboard: http://localhost:5173

### 3. AI Engine

```bash
cd ai_engine
pip install -r ../requirements.txt
python main_ai.py --source path/to/video.mp4
```

## Default Accounts

| Email | Password | Role |
|-------|----------|------|
| admin@system.com | admin123 | ADMIN |
| operator@system.com | operator123 | OPERATOR |

## Environment Variables

```env
# Database
DATABASE_URL="postgresql://..."
DIRECT_URL="postgresql://..."

# Auth
JWT_SECRET="your-secret"
AI_SERVICE_API_KEY="ai-service-secret-key"

# Supabase Storage
SUPABASE_URL="https://xxx.supabase.co"
SUPABASE_SERVICE_KEY="your-service-role-key"
```

## Project Structure

```
├── ai_engine/              # AI detection (Python + YOLOv8)
│   ├── main_ai.py          # Main detection pipeline
│   ├── kinematics.py       # Vehicle tracking + IoU
│   ├── api_client.py       # 2-thread API client
│   └── video_utils.py      # Video frame extraction
├── backend_api/            # REST API + WebSocket (NestJS)
│   └── src/
│       ├── auth/           # JWT + API key authentication
│       ├── accidents/      # Core accident CRUD
│       ├── cameras/        # Camera management
│       ├── alerts/         # Alert notifications
│       ├── events/         # WebSocket gateway
│       ├── upload/         # Video upload (Supabase Storage)
│       └── prisma/         # Database service
├── frontend_dashboard/     # Dashboard UI (React + Ant Design)
│   └── src/
│       ├── pages/          # Dashboard, Cameras, Accidents, Alerts, Login
│       ├── components/     # Layout, ProtectedRoute
│       └── hooks/          # useSocket (real-time)
└── data_storage/           # Video samples
```

## License

UNLICENSED — University project.
