import cv2
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import cloudinary
import cloudinary.uploader

# =======================================================
# CẤU HÌNH CLOUDINARY (Cậu thay bằng API Key của dự án nhé)
# =======================================================
cloudinary.config(
    cloud_name="lxesrdty",
    api_key="851936876939665",
    api_secret="7EEcJeJKgzmCoJvxAlG0k8mz_3o"
)


class CloudAlertManager:
    def __init__(self, api_url, api_key, max_workers=3):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        # Executor cha: Quản lý tối đa 3 vụ tai nạn xảy ra cùng lúc
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def process_and_send(self, frame, clip_frames, base_payload, camera_id, frame_count):
        """
        AI Thread chỉ cần gọi hàm này. Hàm sẽ quăng việc vào luồng ngầm và trả lại ngay.
        Tuyệt đối không làm block AI.
        """
        self.executor.submit(self._async_pipeline, frame, clip_frames, base_payload, camera_id, frame_count)

    def _async_pipeline(self, frame, clip_frames, base_payload, camera_id, frame_count):
        """
        Tiến trình ngầm: Render -> Upload Song Song -> Cập nhật Payload -> Bắn API Backend
        """
        incident_id = base_payload.get('incidentId', 'UNKNOWN_INCIDENT')
        snap_path = f"temp_snap_{camera_id}_{frame_count}.jpg"
        clip_path = f"temp_vid_{camera_id}_{frame_count}.mp4"

        try:
            print(f"\033[93m[CLOUD WORKER] Bắt đầu xử lý hậu kỳ cho {incident_id}...\033[0m")

            # 1. Render Video và Lưu Ảnh ra ổ cứng tạm thời
            self._render_video(clip_frames, clip_path)
            cv2.imwrite(snap_path, frame)

            # 2. Upload song song lên Cloudinary (Dùng 2 worker con)
            # Việc này giúp tiết kiệm thời gian mạng thay vì chờ upload tuần tự
            with ThreadPoolExecutor(max_workers=2) as uploader_pool:
                future_img = uploader_pool.submit(cloudinary.uploader.upload, snap_path, folder="accident_snaps")
                # resource_type="video" là bắt buộc khi up mp4 lên Cloudinary
                future_vid = uploader_pool.submit(cloudinary.uploader.upload, clip_path, folder="accident_vids",
                                                  resource_type="video")

                # Hàm .result() sẽ đứng block luồng ngầm này cho đến khi up xong
                img_result = future_img.result()
                vid_result = future_vid.result()

            # Lấy URL Public chuẩn HTTPS từ Cloudinary trả về
            image_url = img_result.get("secure_url")
            video_url = vid_result.get("secure_url")

            print(f"\033[94m[CLOUD WORKER] Đã upload xong mây cho {incident_id}. Đang gửi Backend...\033[0m")

            # 3. Bơm URL xịn vào base_payload để ra được payload hoàn chỉnh
            base_payload["thumbnailUrl"] = image_url
            base_payload["videoClipUrl"] = video_url

            # 4. Gửi API cho Backend
            response = requests.post(self.api_url, headers=self.headers, json=base_payload)
            if response.status_code in [200, 201]:
                print(f"\033[92m[API DONE] Gửi thành công cảnh báo lên Hệ thống: {incident_id}!\033[0m")
            else:
                print(f"\033[40;31m[API ERROR] Backend từ chối với mã lỗi: {response.status_code}\033[0m")

        except Exception as e:
            print(f"\033[40;31m[CLOUD ERROR] Thất bại toàn tập khi xử lý {incident_id}. Lỗi: {e}\033[0m")
        finally:
            # 5. Quan trọng: Xóa rác local để tránh đầy ổ cứng SSD
            if os.path.exists(snap_path): os.remove(snap_path)
            if os.path.exists(clip_path): os.remove(clip_path)

    def _render_video(self, frames, filepath, fps=30.0, resolution=(1024, 576)):
        """Hàm nội bộ xử lý ghi file MP4"""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filepath, fourcc, fps, resolution)
        for f in frames:
            out.write(f)
        out.release()