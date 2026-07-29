# Weekly Report — Week 2 (June 30 - July 4, 2026)

## Objective
Integrate AI Engine with Backend API — complete the data pipeline from accident detection to database storage.

---

## Completed

### AI Engine Integration
| Task | Status |
|------|--------|
| Create `api_client.py` module | ✅ |
| `report_accident()` — sends POST /accidents with API key | ✅ |
| `get_camera_id_by_source()` — auto-resolve camera from backend | ✅ |
| Update `main_ai.py` to call API on accident detection | ✅ |
| Non-blocking API calls (threaded) | ✅ |
| Add `--camera-id` CLI argument | ✅ |
| Map confidence → severity (HIGH/MEDIUM/LOW) | ✅ |

### Backend Updates
| Task | Status |
|------|--------|
| `ApiKeyGuard` — service-to-service auth via `X-API-Key` header | ✅ |
| `JwtOrApiKeyGuard` — accepts JWT (frontend) or API key (AI) | ✅ |
| POST /accidents — protected by API key (AI access) | ✅ |
| GET /cameras — accessible by both JWT and API key | ✅ |
| Switch runtime to `tsx` (Prisma 7 ESM compatibility fix) | ✅ |
| Install `@prisma/adapter-pg`, `tsx` | ✅ |
| Fix all imports for `nodenext` module resolution | ✅ |

---

## Architecture (Current State)

```
┌─────────────┐     POST /accidents      ┌──────────────┐      Supabase
│  AI Engine  │ ───────────────────────→  │  Backend API │ ───→ PostgreSQL
│  (Python)   │     X-API-Key auth        │  (NestJS)    │
└─────────────┘                           └──────────────┘
                                                ↑
                                          JWT auth │
                                                │
                                          ┌──────────────┐
                                          │   Frontend   │
                                          │ (React+Antd) │
                                          └──────────────┘
```

---

## How to Run

```bash
# Backend
cd backend_api
npm run start:dev    # runs on port 3000

# AI Engine (detect from video)
cd ai_engine
python3 main_ai.py --source ../path/to/video.mp4

# Frontend
cd frontend_dashboard
npm run dev          # runs on port 5173
```

---

## Known Issues / Notes

| Issue | Impact | Workaround |
|-------|--------|-----------|
| Port 3000 conflict (other Next.js app) | Backend can't start | Set `PORT=3001` or stop the other app |
| Prisma 7 generates ESM-only `.ts` files | Can't use `nest build` + `node dist/` | Use `tsx` runtime directly (dev mode) |
| No end-to-end test video available | Can't verify full pipeline | Need sample video in `data_storage/video_clips/positive/` |

---

## Next Week Plan (Week 3) — Real-time + Frontend Polish

- [ ] WebSocket: push notification when new accident detected
- [ ] Video upload to Supabase Storage
- [ ] Frontend: accident detail page with video playback
- [ ] Frontend: real-time alert notifications
- [ ] Dashboard auto-refresh with live data
- [ ] Responsive UI improvements

---

## Commits This Week

| Hash | Message |
|------|---------|
| `600495a` | feat: integrate AI engine with backend API |
