# API Guide for AI Team

## Base URL
```
http://localhost:3000
```

## Authentication
Tất cả request từ AI dùng header:
```
X-API-Key: ai-service-secret-key
```

---

## 1. Lấy danh sách Camera + Config

```
GET /cameras
```

**Response:**
```json
[
  {
    "id": "e6f9795e-b0b0-46a2-acb5-b70455a897dd",
    "name": "CAM_CRASH_1",
    "location": "Crash Zone 1",
    "streamUrl": "../data_storage/video_clips/positive/crash_1.mp4",
    "status": "ACTIVE",
    "aiConfig": {
      "src_pts": [[432,61],[541,561],[1015,511],[750,59]],
      "pixel_to_meter": 0.05,
      "bev_width": 150,
      "bev_height": 250,
      "horizon_y": 50,
      "y_split": 150,
      "thresh_near": -4.0,
      "thresh_far": -35.0,
      "dist_thresh": 3.0
    }
  },
  ...
]
```

**AI sử dụng:**
- `id` → dùng làm `cameraId` khi report accident
- `streamUrl` → video source path
- `aiConfig` → load calibration params

---

## 2. Report Accident (khi phát hiện va chạm)

```
POST /accidents
```

**Headers:**
```
Content-Type: application/json
X-API-Key: ai-service-secret-key
```

**Body:**
```json
{
  "cameraId": "e6f9795e-b0b0-46a2-acb5-b70455a897dd",
  "incidentId": "INC-20260806-001",
  "confidence": 0.85,
  "severity": "HIGH",
  "description": "Phát hiện va chạm giữa: car, motorcycle",
  "vehiclesInvolved": ["car", "motorcycle"],
  "detectedAt": "2026-08-06T12:00:00Z",
  "thumbnailUrl": "https://res.cloudinary.com/xxx/snapshot.jpg",
  "videoClipUrl": "https://res.cloudinary.com/xxx/clip.mp4"
}
```

**Response (201):**
```json
{
  "id": "uuid-accident-created",
  "cameraId": "...",
  "incidentId": "INC-20260806-001",
  "confidence": 0.85,
  "severity": "HIGH",
  "status": "PENDING",
  "videoClipUrl": "https://res.cloudinary.com/xxx/clip.mp4",
  "thumbnailUrl": "https://res.cloudinary.com/xxx/snapshot.jpg",
  "vehiclesInvolved": ["car", "motorcycle"],
  "description": "Phát hiện va chạm giữa: car, motorcycle",
  "detectedAt": "2026-08-06T12:00:00.000Z",
  "createdAt": "2026-08-06T12:00:01.000Z",
  "updatedAt": "2026-08-06T12:00:01.000Z"
}
```

---

## 3. Field Reference

### Required fields:
| Field | Type | Mô tả |
|-------|------|--------|
| `cameraId` | string (UUID) | Lấy từ GET /cameras |
| `confidence` | number (0-1) | Độ tin cậy phát hiện |
| `severity` | string | `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |

### Optional fields:
| Field | Type | Mô tả |
|-------|------|--------|
| `incidentId` | string | ID nội bộ AI (dedup) |
| `description` | string | Mô tả sự cố |
| `vehiclesInvolved` | string[] | ["car", "motorcycle", ...] |
| `detectedAt` | string (ISO) | Timestamp phát hiện |
| `thumbnailUrl` | string | URL ảnh snapshot (Cloudinary) |
| `videoClipUrl` | string | URL video clip (Cloudinary) |
| `latitude` | number | GPS (optional) |
| `longitude` | number | GPS (optional) |

---

## 4. Ví dụ code Python

```python
import requests

API_URL = "http://localhost:3000"
API_KEY = "ai-service-secret-key"
HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY}

# 1. Lấy list camera
cameras = requests.get(f"{API_URL}/cameras", headers=HEADERS).json()
cam = cameras[0]
CAMERA_ID = cam["id"]
config = cam["aiConfig"]  # calibration params

# 2. Report accident
payload = {
    "cameraId": CAMERA_ID,
    "incidentId": "INC-001",
    "confidence": 0.85,
    "severity": "HIGH",
    "description": "Phát hiện va chạm giữa: car, motorcycle",
    "vehiclesInvolved": ["car", "motorcycle"],
    "detectedAt": "2026-08-06T12:00:00Z",
    "thumbnailUrl": "https://res.cloudinary.com/xxx/snapshot.jpg",
    "videoClipUrl": "https://res.cloudinary.com/xxx/clip.mp4"
}

res = requests.post(f"{API_URL}/accidents", json=payload, headers=HEADERS)
print(res.json()["id"])  # UUID của accident vừa tạo
```

---

## 5. Lưu ý

- **Unknown fields sẽ bị bỏ qua** — gửi thừa field không gây lỗi
- **`incidentId`** được lưu DB nhưng backend không dùng để dedup (AI tự handle)
- **Video/Thumbnail** chỉ cần gửi URL (Cloudinary) — backend lưu string, FE hiển thị
- **WebSocket** sẽ tự emit `new-accident` event cho frontend khi POST thành công
- **Severity mapping gợi ý:** confidence > 0.8 → CRITICAL, > 0.5 → HIGH, > 0.3 → MEDIUM, else LOW
