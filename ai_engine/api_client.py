"""
API Client for communicating with the Backend API.
Supports 2-thread async flow:
  Thread 1: report_accident() -> instant alert (returns accidentId)
  Thread 2: upload_video() -> uploads evidence video, links to accidentId
"""
import requests
import os

# Backend API configuration
API_BASE_URL = os.environ.get("BACKEND_API_URL", "http://localhost:3000")
API_KEY = os.environ.get("AI_SERVICE_API_KEY", "ai-service-secret-key")

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
}


def report_accident(camera_id: str, confidence: float, severity: str,
                    description: str = None, latitude: float = None,
                    longitude: float = None) -> str | None:
    """
    Thread 1: Send instant accident alert (no video).
    Returns the accidentId for use in Thread 2, or None on failure.
    """
    payload = {
        "cameraId": camera_id,
        "confidence": confidence,
        "severity": severity,
    }
    if description:
        payload["description"] = description
    if latitude is not None:
        payload["latitude"] = latitude
    if longitude is not None:
        payload["longitude"] = longitude

    try:
        response = requests.post(
            f"{API_BASE_URL}/accidents",
            json=payload,
            headers=HEADERS,
            timeout=10
        )
        if response.status_code == 201:
            accident_id = response.json().get('id')
            print(f"[API] ✅ Thread 1 - Accident alert sent! ID: {accident_id}")
            return accident_id
        else:
            print(f"[API] ❌ Thread 1 - Failed. Status: {response.status_code}, Body: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"[API] ❌ Thread 1 - Cannot connect to backend at {API_BASE_URL}")
        return None
    except requests.exceptions.Timeout:
        print(f"[API] ❌ Thread 1 - Request timed out")
        return None
    except Exception as e:
        print(f"[API] ❌ Thread 1 - Unexpected error: {e}")
        return None


def upload_video(accident_id: str, video_path: str) -> str | None:
    """
    Thread 2: Upload video evidence and link to existing accident record.
    Backend will update DB and emit 'accident-video-ready' socket event.
    Returns the video URL, or None on failure.
    """
    if not accident_id:
        print("[API] ❌ Thread 2 - No accident_id provided, skipping upload")
        return None

    if not os.path.exists(video_path):
        print(f"[API] ❌ Thread 2 - Video file not found: {video_path}")
        return None

    try:
        with open(video_path, 'rb') as f:
            files = {'file': (os.path.basename(video_path), f, 'video/mp4')}
            data = {'accidentId': accident_id}
            headers = {'X-API-Key': API_KEY}  # No Content-Type (multipart auto-set)

            response = requests.post(
                f"{API_BASE_URL}/upload/video",
                files=files,
                data=data,
                headers=headers,
                timeout=60  # Video upload may take time
            )

        if response.status_code == 201:
            url = response.json().get('url')
            print(f"[API] ✅ Thread 2 - Video uploaded! URL: {url}")
            return url
        else:
            print(f"[API] ❌ Thread 2 - Upload failed. Status: {response.status_code}, Body: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"[API] ❌ Thread 2 - Cannot connect to backend at {API_BASE_URL}")
        return None
    except requests.exceptions.Timeout:
        print(f"[API] ❌ Thread 2 - Upload timed out (video too large?)")
        return None
    except Exception as e:
        print(f"[API] ❌ Thread 2 - Unexpected error: {e}")
        return None


def get_camera_id_by_source(source: str) -> str | None:
    """
    Map a video source path/URL to a camera ID from the backend.
    Falls back to fetching first active camera if no match found.
    """
    headers = {"X-API-Key": API_KEY}
    try:
        response = requests.get(f"{API_BASE_URL}/cameras?status=ACTIVE", headers=headers, timeout=5)
        if response.status_code == 200:
            cameras = response.json()
            for cam in cameras:
                if cam.get("streamUrl") == source:
                    return cam["id"]
            if cameras:
                return cameras[0]["id"]
    except Exception as e:
        print(f"[API] ⚠️ Could not fetch cameras: {e}")
    return None
