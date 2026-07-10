import cv2
import threading
import queue
import time
import requests


class VideoReader:
    def __init__(self, source, queue_size=30):
        self.source = source
        self.stream = None
        self.connect_camera()  # Gọi hàm kết nối lần đầu

        self.frame_queue = queue.Queue(maxsize=queue_size)
        self.stopped = False

    def connect_camera(self):
        """Hàm độc lập chuyên xử lý việc Mở/Mở lại kết nối"""
        if self.stream is not None:
            self.stream.release()

        self.stream = cv2.VideoCapture(self.source)
        if not self.stream.isOpened():
            print(f"[MẠNG] Lỗi: Không thể vươn tới địa chỉ: {self.source}")
            return False

        self.success, self.frame = self.stream.read()
        return True

    def start(self):
        print("[HỆ THỐNG] Đang khởi động Luồng Đọc Video (I/O Thread)...")
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            if self.frame_queue.full():
                time.sleep(0.01)
                continue

            self.success, frame = self.stream.read()

            # --- CƠ CHẾ TỰ PHỤC HỒI (FAIL-SAFE) ---
            if not self.success:
                print("[CẢNH BÁO MẠNG] Mất tín hiệu camera! Đang thử kết nối lại sau 3 giây...")
                time.sleep(3)  # Ngủ đông 3 giây để không làm treo CPU

                # Xóa sạch các ảnh cũ đang kẹt trên băng chuyền (tránh AI xử lý ảnh tồn đọng khi rớt mạng)
                with self.frame_queue.mutex:
                    self.frame_queue.queue.clear()

                # Cố gắng kết nối lại
                if self.connect_camera():
                    print("[HỆ THỐNG] Đã khôi phục tín hiệu mạng. Tiếp tục giám sát 24/7!")
                continue  # Bỏ qua các lệnh dưới, quay lại đầu vòng lặp while

            self.frame_queue.put(frame)

    def read(self):
        try:
            # Chỉ đứng đợi tối đa 0.1 giây, nếu trống thì báo hiệu None
            return self.frame_queue.get(timeout=0.1)
        except queue.Empty:
            return None

    def stop(self):
        self.stopped = True
        if self.stream is not None:
            self.stream.release()

# =================================================================== #

# =================================================================== #

class NetworkWorker:
    def __init__(self, api_url, api_key, queue_size=50):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        # Băng chuyền số 2: Chuyên chứa gói tin JSON báo cáo tai nạn chờ gửi đi
        self.api_queue = queue.Queue(maxsize=queue_size)
        self.stopped = False

    def start(self):
        print("[HỆ THỐNG] Đang khởi động Luồng Giao tiếp (Network Thread)...")
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        return self

    def send_alert(self, payload):
        """Hàm dành cho Luồng AI: Ném gói tin lên băng chuyền rồi đi làm việc khác"""
        if not self.api_queue.full():
            self.api_queue.put(payload)
        else:
            print("[CẢNH BÁO] Nghẽn mạng! Băng chuyền API đã đầy, phải hủy bỏ gói tin.")

    def update(self):
        """Luồng chạy ngầm: Cứ có gói tin trên băng chuyền là nhặt ra gửi đi"""
        while not self.stopped:
            try:
                # Chờ lấy gói tin (đứng đợi tối đa 1s để còn quay lại check self.stopped)
                payload = self.api_queue.get(timeout=1)

                print(f"[NETWORK] Đang gửi API báo cáo tai nạn (Frame: {payload.get('frame_count')})...")

                # --- PHẦN KẾT NỐI SERVER THẬT (Mở comment khi có server của Phúc) ---
                # response = requests.post(self.api_url, headers=self.headers, json=payload)
                # if response.status_code in [200, 201]:
                #     print("[NETWORK] Gửi thành công lên Backend!")
                # else:
                #     print(f"[NETWORK] Lỗi Backend trả về: {response.status_code}")

                # --- TRONG LÚC CHƯA CÓ SERVER, CHÚNG TA GIẢ LẬP GỬI MẤT 0.5 GIÂY ---
                time.sleep(0.5)
                print("[NETWORK] Đã gửi xong (Giả lập)!")

            except queue.Empty:
                continue  # Nếu băng chuyền trống thì lặp lại vòng lặp chờ đợi
            except Exception as e:
                print(f"[NETWORK ERROR] Lỗi luồng mạng: {e}")

    def stop(self):
        self.stopped = True


# =================================================================== #

# =================================================================== #
if __name__ == "__main__":
    import json
    from ultralytics import YOLO
    from kinematics import init_calibrator, calculate_iou, VehicleTrack
    import math
    from datetime import datetime, UTC
    import time
    import cv2

    # 1. ĐỌC CẤU HÌNH CAMERA TỪ FILE JSON
    CONFIG_FILE = "cameras_config.json"
    CAMERA_ID = "CAM_CRASH_7"  # Chỉ cần đổi tên ID ở đây, toàn bộ hệ thống sẽ tự thay máu

    print(f"[HỆ THỐNG] Đang tải cấu hình cho {CAMERA_ID}...")
    with open(CONFIG_FILE, "r") as f:
        all_cameras = json.load(f)

    cam_config = all_cameras[CAMERA_ID]

    # Tiêm cấu hình toán học vào bộ nhớ
    init_calibrator(cam_config)

    # 2. KHỞI TẠO CÁC CÔNG NHÂN VÀ MÔ HÌNH
    print("[HỆ THỐNG] Đang tải mô hình YOLOv8...")
    model = YOLO("yolov8n.pt")

    # Lấy đường dẫn video động từ JSON
    test_video_path = cam_config["source"]

    # Bật Luồng Đọc
    reader = VideoReader(test_video_path, queue_size=30).start()

    # Bật Luồng Mạng
    API_URL = "http://localhost:3000/accidents"
    API_KEY = "ai-secret-key-123"
    network_worker = NetworkWorker(API_URL, API_KEY).start()

    # 2. KHỞI TẠO CÁC BIẾN TRẠNG THÁI CỦA THUẬT TOÁN ĐỘNG HỌC
    active_trackers = {}
    active_incidents = []
    INCIDENT_RADIUS = 200
    COOLDOWN_FRAMES = 200

    start_time = time.time()
    frame_count = 0

    print("[HỆ THỐNG] Đang khởi chạy Luồng Suy Luận (AI Thread)...")

    try:
        while True:
            # Nếu mất mạng quá lâu và queue trống thì tự động thoát (Hoặc cậu có thể để nó chạy vĩnh viễn)
            if reader.stopped and reader.frame_queue.empty():
                break

            # --- RÚT ẢNH TỪ BĂNG CHUYỀN ---
            frame = reader.read()

            # Nếu băng chuyền trống (do mạng đang đứt), vẫn phải lắng nghe phím Q
            if frame is None:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue  # Bỏ qua AI, quay lại vòng lặp chờ ảnh mới

            frame_count += 1

            # --- CHẠY YOLO TRACKING ---
            results = model.track(frame, classes=[2, 3, 5, 7], persist=True, tracker="bytetrack.yaml", verbose=False)

            current_frame_ids = []

            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                ids = results[0].boxes.id.cpu().numpy().astype(int)
                cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)
                class_names = model.names

                # 2.1 CẬP NHẬT TRẠNG THÁI CHO TỪNG CHIẾC XE
                for box, track_id, cls_id in zip(boxes, ids, cls_ids):
                    current_frame_ids.append(track_id)

                    if track_id not in active_trackers:
                        veh_type = class_names[cls_id]
                        active_trackers[track_id] = VehicleTrack(track_id, vehicle_type=veh_type)

                    current_vehicle = active_trackers[track_id]
                    current_vehicle.update(box)

                    x_min, y_min, x_max, y_max = map(int, box)
                    speed = current_vehicle.velocities[-1] if len(current_vehicle.velocities) > 0 else 0.0

                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
                    cv2.putText(frame, f"ID:{track_id} v:{speed:.1f}", (x_min, y_min - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

                # 2.2 LOGIC BẮT VA CHẠM (SPATIO-TEMPORAL CLUSTERING)
                for i in range(len(current_frame_ids)):
                    for j in range(i + 1, len(current_frame_ids)):
                        id_A = current_frame_ids[i]
                        id_B = current_frame_ids[j]

                        vehicle_A = active_trackers[id_A]
                        vehicle_B = active_trackers[id_B]

                        iou_score = calculate_iou(vehicle_A.current_box, vehicle_B.current_box)

                        if iou_score > 0.1:
                            a_A = vehicle_A.acceleration
                            a_B = vehicle_B.acceleration

                            if a_A <= -3.0 or a_B <= -3.0:
                                crash_cx = (vehicle_A.centroids[-1][0] + vehicle_B.centroids[-1][0]) / 2.0
                                crash_cy = (vehicle_A.centroids[-1][1] + vehicle_B.centroids[-1][1]) / 2.0

                                is_new_incident = True
                                for incident in active_incidents:
                                    if frame_count - incident['frame'] < COOLDOWN_FRAMES:
                                        dist = math.sqrt((crash_cx - incident['centroid'][0]) ** 2 + (
                                                    crash_cy - incident['centroid'][1]) ** 2)
                                        if dist < INCIDENT_RADIUS:
                                            is_new_incident = False
                                            break

                                if is_new_incident:
                                    active_incidents.append({'centroid': (crash_cx, crash_cy), 'frame': frame_count})
                                    cv2.putText(frame, "CANH BAO: TAI NAN!", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                                (0, 0, 255), 3)

                                    # --- GIAO TIẾP MẠNG ĐA LUỒNG ---
                                    # Đóng gói JSON (Bỏ hoàn toàn Base64 ảnh nặng nề)
                                    accident_payload = {
                                        "camera_id": "CAM_HCMC_GOLVAP_01",
                                        "frame_count": frame_count,
                                        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                        "accident_detected": True,
                                        "confidence_score": round(float(iou_score), 2),
                                        "alert_level": "HIGH",
                                        "vehicles_involved": [vehicle_A.vehicle_type, vehicle_B.vehicle_type],
                                        # Tạm thời cấu hình đường dẫn vật lý, khâu cắt video sẽ bổ sung sau
                                        "video_clip_path": f"../data_storage/video_clips/accidents/accident_{frame_count}_v2.mp4"
                                    }

                                    # Ném gói tin lên băng chuyền để Luồng Mạng tự xử lý, AI tiếp tục chạy không chờ đợi!
                                    network_worker.send_alert(accident_payload)

            # 3. DỌN DẸP BỘ NHỚ AI
            active_incidents = [inc for inc in active_incidents if frame_count - inc['frame'] < COOLDOWN_FRAMES]
            ids_to_remove = [tid for tid in active_trackers if tid not in current_frame_ids]
            for tid in ids_to_remove:
                del active_trackers[tid]

            # 4. ĐO LƯỜNG VÀ HIỂN THỊ
            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time if elapsed_time > 0 else 0

            # Vẽ thanh trạng thái
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
            cv2.putText(frame, f"AI FPS: {fps:.1f} | Frame: {frame_count}", (15, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("He Thong Loi AI - Thuc Chien", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("[HỆ THỐNG] Người dùng cưỡng chế dừng chương trình.")
    finally:
        # Tắt toàn bộ hệ thống an toàn
        reader.stop()
        network_worker.stop()
        cv2.destroyAllWindows()
        print("[HỆ THỐNG] Đã tắt luồng an toàn.")