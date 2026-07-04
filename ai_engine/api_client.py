"""
API Client for communicating with the Backend API.
Sends accident detection results to POST /accidents endpoint.
"""
import requests
import os

# Backend API configuration
API_BASE_URL = os.environ.get("BACKEND_API_URL", "http://localhost:3000")
API_KEY = os.environ.get("AI_SERVICE_API_KEY", "ai-service-secret-key")


def report_accident(camera_id: str, confidence: float, severity: str,
                    video_clip_url: str = None, description: str = None,
                    latitude: float = None, longitude: float = None):
    """
    Send accident detection result to the backend API.
    
    Args:
        camera_id: UUID of the camera that detected the accident
        confidence: Detection confidence score (0.0 - 1.0)
        severity: One of 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
        video_clip_url: Path/URL to the saved video clip
        description: Text description of the incident
        latitude: GPS latitude (optional)
        longitude: GPS longitude (optional)
    
    Returns:
        Response JSON from the backend, or None on failure
    """
    payload = {
        "cameraId": camera_id,
        "confidence": confidence,
        "severity": severity,
    }

    if video_clip_url:
        payload["videoClipUrl"] = video_clip_url
    if description:
        payload["description"] = description
    if latitude is not None:
        payload["latitude"] = latitude
    if longitude is not None:
        payload["longitude"] = longitude

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/accidents",
            json=payload,
            headers=headers,
            timeout=10
        )
        if response.status_code == 201:
            print(f"[API] ✅ Accident reported successfully. ID: {response.json().get('id')}")
            return response.json()
        else:
            print(f"[API] ❌ Failed to report accident. Status: {response.status_code}, Body: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"[API] ❌ Cannot connect to backend at {API_BASE_URL}")
        return None
    except requests.exceptions.Timeout:
        print(f"[API] ❌ Request timed out")
        return None
    except Exception as e:
        print(f"[API] ❌ Unexpected error: {e}")
        return None


def get_camera_id_by_source(source: str) -> str:
    """
    Map a video source path/URL to a camera ID from the backend.
    Falls back to fetching first active camera if no match found.
    """
    headers = {"X-API-Key": API_KEY}
    try:
        response = requests.get(f"{API_BASE_URL}/cameras?status=ACTIVE", headers=headers, timeout=5)
        if response.status_code == 200:
            cameras = response.json()
            # Try matching by stream URL
            for cam in cameras:
                if cam.get("streamUrl") == source:
                    return cam["id"]
            # Fallback: return first active camera
            if cameras:
                return cameras[0]["id"]
    except Exception as e:
        print(f"[API] ⚠️ Could not fetch cameras: {e}")

    return None
