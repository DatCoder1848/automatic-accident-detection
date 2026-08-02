import cv2
import threading
import queue
import time
import requests
from collections import deque


class VideoReader:
    def __init__(self, source, queue_size=30):
        self.source = source
        self.stream = None
        self.connect_camera()  # Gọi hàm kết nối lần đầu

        self.frame_queue = queue.Queue(maxsize=queue_size)
        # Buffer lưu 5 giây video lùi về từ thời điểm hiện tại (5s * 30 fps = 150 frames)
        self.history_buffer = deque(maxlen=150)
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

            # ÉP KÍCH THƯỚC CHUẨN ĐỂ LƯU VIDEO ĐỒNG NHẤT
            frame = cv2.resize(frame, (1024, 576))

            # THÊM DÒNG NÀY: Copy 1 bản cất vào túi quá khứ trước khi ném lên băng chuyền AI
            self.history_buffer.append(frame.copy())

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
            print("\033[93m[⚠️ API NGHẼN] Băng chuyền API đã đầy! Hủy bỏ gói tin.\033[0m")

    def update(self):
        """Luồng chạy ngầm: Cứ có gói tin trên băng chuyền là nhặt ra gửi đi"""
        while not self.stopped:
            try:
                # Chờ lấy gói tin (đứng đợi tối đa 1s để còn quay lại check self.stopped)
                payload = self.api_queue.get(timeout=1)

                print(
                    f"\033[94m[🌐 API SEND] Frame: {payload.get('frame_count')} | Objects: {', '.join(payload.get('vehicles_involved', []))}...\033[0m")

                # --- PHẦN KẾT NỐI SERVER THẬT (Mở comment khi có server của Phúc) ---
                # response = requests.post(self.api_url, headers=self.headers, json=payload)
                # if response.status_code in [200, 201]:
                #     print("[NETWORK] Gửi thành công lên Backend!")
                # else:
                #     print(f"[NETWORK] Lỗi Backend trả về: {response.status_code}")

                # --- TRONG LÚC CHƯA CÓ SERVER, CHÚNG TA GIẢ LẬP GỬI MẤT 0.5 GIÂY ---
                time.sleep(0.5)
                print(f"\033[92m[🌐 API DONE] Đã gửi thành công gói tin Frame {payload.get('frame_count')}!\033[0m")

            except queue.Empty:
                continue  # Nếu băng chuyền trống thì lặp lại vòng lặp chờ đợi
            except Exception as e:
                print(f"[NETWORK ERROR] Lỗi luồng mạng: {e}")

    def stop(self):
        self.stopped = True


class VideoWriterWorker:
    def __init__(self, fps=30.0, resolution=(1024, 576)):
        # Băng chuyền số 3: Chứa các gói ảnh chờ ghi thành file
        self.task_queue = queue.Queue(maxsize=10)
        self.stopped = False
        self.fps = fps
        self.resolution = resolution

    def start(self):
        print("[HỆ THỐNG] Đang khởi động Luồng Ghi Video (Writer Thread)...")
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        return self

    def save_clip(self, frames, filepath):
        """Hàm cho AI gọi: Quăng túi ảnh qua đây rồi đi làm việc tiếp"""
        if not self.task_queue.full():
            self.task_queue.put({'frames': frames, 'filepath': filepath})

    def update(self):
        """Tiến trình ngầm: Ghi file ra ổ SSD"""
        while not self.stopped:
            try:
                task = self.task_queue.get(timeout=1)
                frames = task['frames']
                filepath = task['filepath']

                print(f"\033[95m[💾 DISK WRITE] Đang xuất file bằng chứng: {filepath}...\033[0m")

                # Bộ mã hóa mp4
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(filepath, fourcc, self.fps, self.resolution)

                for f in frames:
                    out.write(f)
                out.release()

                print(f"\033[92m[💾 DISK DONE] Đã lưu thành công clip: {filepath}\033[0m")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[WRITER ERROR] Lỗi ghi video: {e}")

    def stop(self):
        self.stopped = True



# THÊM HÀM NÀY BÊN NGOÀI
def is_in_edge(box, margin=40, frame_w=1024, frame_h=576):
    x_min, y_min, x_max, y_max = box
    # Nếu hộp bao chạm vào vùng 40 pixel tính từ các mép camera
    return (x_min < margin or y_min < margin or x_max > frame_w - margin or y_max > frame_h - margin)

def calculate_ios(boxA, boxB):
    # Tính tỷ lệ Giao nhau / Diện tích của hộp bao NHỎ HƠN
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    smaller_area = min(areaA, areaB)
    if smaller_area == 0: return 0.0
    return interArea / smaller_area
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
    import csv
    from utils import log_raw_crash_data

    # 1. ĐỌC CẤU HÌNH CAMERA TỪ FILE JSON
    CONFIG_FILE = "cameras_config.json"
    CAMERA_ID = "CAM_CRASH_9" # "CAM_NOR_4" # Chỉ cần đổi tên ID ở đây, toàn bộ hệ thống sẽ tự thay máu

    print(f"[HỆ THỐNG] Đang tải cấu hình cho {CAMERA_ID}...")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        all_cameras = json.load(f)

    cam_config = all_cameras[CAMERA_ID]

    # Tiêm cấu hình toán học vào bộ nhớ
    init_calibrator(cam_config)

    # 2. KHỞI TẠO CÁC CÔNG NHÂN VÀ MÔ HÌNH
    print("[HỆ THỐNG] Đang tải mô hình YOLO11s...")
    model = YOLO("yolo11s.pt")#.to("cuda")

    # Lấy đường dẫn video động từ JSON
    test_video_path = cam_config["source"]

    # Bật Luồng Đọc
    reader = VideoReader(test_video_path, queue_size=30).start()

    # Bật Luồng Mạng
    API_URL = "http://localhost:3000/accidents"
    API_KEY = "ai-service-secret-key"
    network_worker = NetworkWorker(API_URL, API_KEY).start()

    # Bật Luồng Ghi Video
    video_writer_worker = VideoWriterWorker().start()

    # 2. KHỞI TẠO CÁC BIẾN TRẠNG THÁI CỦA THUẬT TOÁN ĐỘNG HỌC
    active_trackers = {}
    active_incidents = []
    pending_incidents = []  # Hàng đợi chứa các Vùng nghi ngờ
    INCIDENT_RADIUS = 200
    COOLDOWN_FRAMES = 200
    VALIDATION_FRAMES = 90  # Thời gian kiểm chứng 3 giây (30fps * 3s)

    # Các biến bổ sung phục vụ hiển thị UI cảnh báo giữ trong 5 giây
    last_incident_time = 0.0
    SHOW_ALERT_DURATION = 5.0  # Thời gian hiển thị cảnh báo (giây)

    start_time = time.time()
    frame_count = 0

    # THÊM ĐOẠN NÀY DÀNH CHO ĐO FPS:
    smoothed_fps = 0.0  # Dùng EMA để làm mượt FPS hiển thị
    csv_file = open('fps_log_thuc_te.csv', 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Frame', 'So_Xe', 'FPS'])  # Tiêu đề cột cho Excel

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

            # --- BẮT ĐẦU BẤM GIỜ XỬ LÝ LÕI AI ---
            # Dùng perf_counter() chính xác hơn time.time() ở cấp độ mili-giây
            frame_start_time = time.perf_counter()

            # --- CHẠY YOLO TRACKING ---
            results = model.track(frame, classes=[2, 3, 5, 7], persist=True, imgsz=1024, agnostic_nms=False,
                                  tracker="botsort.yaml", conf=0.2, iou=0.7, verbose=False, device=0)

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

                # --- NHÁT CẮT 2: CODE DỌN DẸP 1 XE 2 ID SAU KHI ĐÃ CẬP NHẬT TỌA ĐỘ ---
                ids_to_kill = set()
                for i in range(len(current_frame_ids)):
                    for j in range(i + 1, len(current_frame_ids)):
                        id_1 = current_frame_ids[i]
                        id_2 = current_frame_ids[j]

                        if id_1 in active_trackers and id_2 in active_trackers:
                            box_1 = active_trackers[id_1].current_box
                            box_2 = active_trackers[id_2].current_box

                            # Tính IoU giữa 2 ID này
                            ios_dup = calculate_ios(box_1, box_2)

                            # Nếu đè nhau quá 65% -> 100% là 1 xe bị nhận diện thành 2 ID
                            if ios_dup > 0.7:
                                age_1 = len(active_trackers[id_1].centroids)
                                age_2 = len(active_trackers[id_2].centroids)

                                # Khai tử ID nào mới sinh ra (tuổi nhỏ hơn)
                                if age_1 > age_2:
                                    ids_to_kill.add(id_2)
                                else:
                                    ids_to_kill.add(id_1)

                # Xóa các ID giả khỏi current_frame_ids trước khi hệ thống kịp đưa chúng vào tính toán va chạm
                current_frame_ids = [tid for tid in current_frame_ids if tid not in ids_to_kill]
                # Loại bỏ ID giả khỏi frame hiện tại và xóa luôn khỏi bộ nhớ để nó không lọt xuống dưới
                for tid in ids_to_kill:
                    if tid in active_trackers:
                        del active_trackers[tid]
                # ------------------------------------------
            # -------------------------------------------------------------------------

                # ================= ĐÃ LÙI LỀ RA NGOÀI VÒNG LẶP =================
                # ================= BẮT ĐẦU KHỐI LOGIC LÕI =================
                # HÀM BỔ TRỢ TÍNH GIA TỐC MƯỢT (CHỐNG JITTER)
                def get_smooth_accel(vehicle, frames_back=10, fps=30.0):
                    vels = list(vehicle.velocities)
                    if len(vels) < frames_back + 1:
                        return vehicle.acceleration
                    v_now = vels[-1]
                    v_past = vels[-(frames_back + 1)]
                    return (v_now - v_past) / (frames_back / fps)

                # 2.2 LOGIC BẮT VA CHẠM (GIAI ĐOẠN 1: KÍCH HOẠT VÙNG NGHI NGỜ)
                all_active_ids = list(active_trackers.keys())
                # Dùng current_frame_ids để chỉ tính toán các xe đang có mặt trên màn hình
                for i in range(len(current_frame_ids)):
                    for j in range(i + 1, len(current_frame_ids)):
                        id_A = current_frame_ids[i]
                        id_B = current_frame_ids[j]

                        vehicle_A = active_trackers[id_A]
                        vehicle_B = active_trackers[id_B]

                        if vehicle_A.current_box is None or vehicle_B.current_box is None:
                            continue

                        cy_A = vehicle_A.centroids[-1][1]
                        cy_B = vehicle_B.centroids[-1][1]
                        if cy_A < cam_config.get("horizon_y", 200) or cy_B < cam_config.get("horizon_y", 200):
                            continue

                        iou_score = calculate_iou(vehicle_A.current_box, vehicle_B.current_box)

                        # Tính toán vô điều kiện để lấy data thô
                        bev_A = vehicle_A.centroids_bev[-1]
                        bev_B = vehicle_B.centroids_bev[-1]
                        pixel_dist = math.sqrt((bev_A[0] - bev_B[0]) ** 2 + (bev_A[1] - bev_B[1]) ** 2)
                        real_dist_meters = pixel_dist * cam_config["pixel_to_meter"]

                        # MỞ CỬA CHO GIA TỐC: Khoảng cách dưới 5.0 mét (Đủ bắt tâm xe tải 3.4m)
                        if real_dist_meters < 5.0 or iou_score > 0.03:

                            smooth_a_A = get_smooth_accel(vehicle_A, frames_back=10)
                            smooth_a_B = get_smooth_accel(vehicle_B, frames_back=10)

                            v_A = vehicle_A.velocities[-1] if len(vehicle_A.velocities) > 0 else 0.0
                            v_B = vehicle_B.velocities[-1] if len(vehicle_B.velocities) > 0 else 0.0

                            max_v_A = max(list(vehicle_A.velocities)[-5:]) if len(vehicle_A.velocities) > 0 else 0.0
                            max_v_B = max(list(vehicle_B.velocities)[-5:]) if len(vehicle_B.velocities) > 0 else 0.0

                            edge_A = is_in_edge(vehicle_A.current_box)
                            edge_B = is_in_edge(vehicle_B.current_box)

                            # --- GỌI HÀM DEBUG TỪ UTILS.PY ---
                            log_raw_crash_data(
                                frame_count, id_A, id_B,
                                vehicle_A.vehicle_type, vehicle_B.vehicle_type,
                                iou_score, real_dist_meters,
                                edge_A, edge_B,
                                v_A, max_v_A, smooth_a_A,
                                v_B, max_v_B, smooth_a_B
                            )
                            # ---------------------------------

                            if iou_score > 0.15:
                                # Tính khoảng cách Mét thực tế
                                bev_A = vehicle_A.centroids_bev[-1]
                                bev_B = vehicle_B.centroids_bev[-1]
                                pixel_dist = math.sqrt((bev_A[0] - bev_B[0]) ** 2 + (bev_A[1] - bev_B[1]) ** 2)
                                real_dist_meters = pixel_dist * cam_config["pixel_to_meter"]

                                # Tính toán toàn bộ thông số Động học & Không gian trước khi lọc
                                smooth_a_A = get_smooth_accel(vehicle_A)
                                smooth_a_B = get_smooth_accel(vehicle_B)

                                v_A = vehicle_A.velocities[-1] if len(vehicle_A.velocities) > 0 else 0.0
                                v_B = vehicle_B.velocities[-1] if len(vehicle_B.velocities) > 0 else 0.0
                                max_v_A = max(list(vehicle_A.velocities)[-5:]) if len(
                                    vehicle_A.velocities) > 0 else 0.0
                                max_v_B = max(list(vehicle_B.velocities)[-5:]) if len(
                                    vehicle_B.velocities) > 0 else 0.0
                                delta_v_A = max_v_A - v_A
                                delta_v_B = max_v_B - v_B
                                age_A = len(vehicle_A.centroids)
                                age_B = len(vehicle_B.centroids)

                                # ================= LOG CHI TIẾT ĐỂ BẮT LỖI TẬN GỐC =================
                                # In log khi hai xe ở gần (< 5m) và có động học bất thường (phanh/văng) hoặc đè nhau
                                if real_dist_meters < 5.0 and (
                                        smooth_a_A < -3.0 or smooth_a_B < -3.0 or iou_score > 0.15):
                                    box_A_str = f"[{int(vehicle_A.current_box[0])},{int(vehicle_A.current_box[1])},{int(vehicle_A.current_box[2])},{int(vehicle_A.current_box[3])}]"
                                    box_B_str = f"[{int(vehicle_B.current_box[0])},{int(vehicle_B.current_box[1])},{int(vehicle_B.current_box[2])},{int(vehicle_B.current_box[3])}]"

                                    print(
                                        f"\n[DEBUG-AI] Frame {frame_count} | {vehicle_A.vehicle_type}(ID:{id_A}) & {vehicle_B.vehicle_type}(ID:{id_B})")
                                    print(
                                        f"  -> Không gian: IoU 2D = {iou_score:.2f} | Khoảng cách thực = {real_dist_meters:.1f}m")
                                    print(f"  -> ID {id_A} (Tuổi: {age_A}f): Box = {box_A_str}")
                                    print(
                                        f"     Động học: v={v_A:.1f} | max_v={max_v_A:.1f} | dV={delta_v_A:.1f} | a_mượt={smooth_a_A:.1f}")
                                    print(f"  -> ID {id_B} (Tuổi: {age_B}f): Box = {box_B_str}")
                                    print(
                                        f"     Động học: v={v_B:.1f} | max_v={max_v_B:.1f} | dV={delta_v_B:.1f} | a_mượt={smooth_a_B:.1f}")
                                # ===================================================================

                                # 1. KIỂM TRA BÓNG MA (GHOST DUPLICATION)
                                is_ghost_A = hasattr(vehicle_A, 'lost_frames') and vehicle_A.lost_frames > 0
                                is_ghost_B = hasattr(vehicle_B, 'lost_frames') and vehicle_B.lost_frames > 0
                                if (is_ghost_A or is_ghost_B) and iou_score > 0.4:
                                    continue

                                # LỌC BÒ CHẬM (CRAWLING FILTER): Bỏ qua nếu cả 2 xe đều đang đi rà rà (< 5 km/h)
                                if max_v_A < 5.0 and max_v_B < 5.0:
                                    continue

                                # TÍNH NGƯỠNG GIA TỐC ĐỘNG
                                t_near = cam_config.get("thresh_near", -6.0)
                                t_far = cam_config.get("thresh_far", -9.0)
                                y_split = cam_config.get("y_split", 400)
                                horizon_y = cam_config.get("horizon_y", 200)


                                def get_dynamic_thresh(cy):
                                    if cy >= y_split: return t_near
                                    if cy <= horizon_y: return t_far
                                    ratio = (cy - horizon_y) / (y_split - horizon_y)
                                    return t_far + ratio * (t_near - t_far)


                                thresh_A = get_dynamic_thresh(cy_A)
                                thresh_B = get_dynamic_thresh(cy_B)

                                # KHÓA CHẶT RÌA MÀN HÌNH CHO CẢ 2 ĐIỀU KIỆN
                                edge_A = is_in_edge(vehicle_A.current_box)
                                edge_B = is_in_edge(vehicle_B.current_box)

                                is_physical_crush = (iou_score > 0.25) and (real_dist_meters < 1.5) and not (
                                            edge_A or edge_B)
                                # Chỉ công nhận gia tốc sốc nếu chiếc xe bị sốc ĐANG CÓ ĐÀ CHẠY thật sự (> 5.0 km/h)
                                valid_shock_A = (smooth_a_A < thresh_A) and (max_v_A > 5.0)
                                valid_shock_B = (smooth_a_B < thresh_B) and (max_v_B > 5.0)
                                is_kinematic_shock = (real_dist_meters < 2.5) and (valid_shock_A or valid_shock_B) and not (edge_A or edge_B)

                                if is_physical_crush or is_kinematic_shock:
                                    crash_cx = (vehicle_A.centroids[-1][0] + vehicle_B.centroids[-1][0]) / 2.0
                                    crash_cy = (vehicle_A.centroids[-1][1] + vehicle_B.centroids[-1][1]) / 2.0
                                    bev_cx = (bev_A[0] + bev_B[0]) / 2.0
                                    bev_cy = (bev_A[1] + bev_B[1]) / 2.0

                                    is_new_suspect = True
                                    for incident in active_incidents:
                                        if frame_count - incident['frame'] < COOLDOWN_FRAMES:
                                            dist = math.sqrt((crash_cx - incident['centroid'][0]) ** 2 + (
                                                    crash_cy - incident['centroid'][1]) ** 2)
                                            if dist < 100:
                                                is_new_suspect = False;
                                                break

                                    for pending in pending_incidents:
                                        dist = math.sqrt((crash_cx - pending['centroid'][0]) ** 2 + (
                                                crash_cy - pending['centroid'][1]) ** 2)
                                        if dist < 100:
                                            is_new_suspect = False;
                                            break

                                    if is_new_suspect:
                                        reasons_cache = [f"Khoảng cách: {real_dist_meters:.1f}m"]
                                        if is_physical_crush: reasons_cache.append(
                                            f"Giao nhau (IoU: {iou_score:.2f})")
                                        if is_kinematic_shock: reasons_cache.append(
                                            f"Phanh/Văng (aA:{smooth_a_A:.1f}, aB:{smooth_a_B:.1f})")

                                        print(
                                            f"\033[93m[⚠️ SUSPECT] Đưa vào diện tình nghi tại Frame {frame_count}. Chờ 3s kiểm chứng...\033[0m")
                                        pending_incidents.append({
                                            'centroid': (crash_cx, crash_cy),
                                            'bev_centroid': (bev_cx, bev_cy),
                                            'start_frame': frame_count,
                                            'vehicle_types': [vehicle_A.vehicle_type, vehicle_B.vehicle_type],
                                            'ids': [id_A, id_B],
                                            'reasons': reasons_cache
                                        })

                # --- GIAI ĐOẠN 2: KIỂM CHỨNG THEO ĐỐI TƯỢNG VÀ KHÔNG GIAN THỰC (METERS) ---
                VALIDATION_RADIUS_METERS = 6.0  # Quét phạm vi 6 mét để bắt gọn xe trượt văng

                surviving_pending = []
                for pending in pending_incidents:
                    age_frames = frame_count - pending['start_frame']

                    if age_frames < VALIDATION_FRAMES:
                        surviving_pending.append(pending)
                        continue

                    bev_orig_x, bev_orig_y = pending['bev_centroid']
                    stuck_vehicles = 0
                    evidence_logs = []

                    for track_id, vehicle in active_trackers.items():
                        if hasattr(vehicle, 'lost_frames') and vehicle.lost_frames > 0:
                            continue

                        v_current = vehicle.velocities[-1] if len(vehicle.velocities) > 0 else 0.0
                        if v_current > 2.0:  # Bắt buộc phải bất động (v < 2.0km/h), loại bỏ xe bò rà phanh
                            continue

                        # Đổi khoảng cách trên ảnh sang khoảng cách Mét thực tế
                        curr_bev_x, curr_bev_y = vehicle.centroids_bev[-1]
                        dist_px = math.sqrt((curr_bev_x - bev_orig_x) ** 2 + (curr_bev_y - bev_orig_y) ** 2)
                        real_dist_meters = dist_px * cam_config["pixel_to_meter"]

                        if real_dist_meters < VALIDATION_RADIUS_METERS:
                            #track_age = len(vehicle.centroids)
                            # is_original_victim = track_id in pending['ids']
                            # is_new_object = track_age < VALIDATION_FRAMES  # Xe/Người bị văng, Tracker cấp ID mới
                            #
                            # # Chỉ chốt tai nạn nếu vật thể nằm lại đường ĐÚNG LÀ phương tiện liên quan
                            # if is_original_victim or is_new_object:
                            #     stuck_vehicles += 1
                            # SỬA LẠI ĐÚNG NHƯ SAU:
                            # NHÁT CẮT 3: TỪ CHỐI NHẬN VƠ
                            is_original_victim = track_id in pending['ids']

                            # CHỈ chấp nhận chính phương tiện gốc nằm lại hiện trường
                            if is_original_victim:
                                stuck_vehicles += 1
                                evidence_logs.append(
                                    f"ID:{track_id}({vehicle.vehicle_type}) bất động cách {real_dist_meters:.1f}m")

                    if stuck_vehicles >= 1:
                        cx, cy = pending['centroid']
                        active_incidents.append({'centroid': (cx, cy), 'frame': frame_count})
                        last_incident_time = time.time()

                        print("\n" + "=" * 60)
                        print(
                            f"\033[1;31m🚨 [CRASH CONFIRMED] XÁC NHẬN TAI NẠN (TỪ NGHI NGỜ FRAME {pending['start_frame']})! 🚨\033[0m")
                        print(
                            f"📍 Đối tượng ban đầu: {pending['vehicle_types'][0]}(ID:{pending['ids'][0]}) & {pending['vehicle_types'][1]}(ID:{pending['ids'][1]})")
                        print(f"🔍 Bằng chứng khởi phát: {' + '.join(pending['reasons'])}")
                        print(f"🔍 Bằng chứng hiện trường: {stuck_vehicles} nạn nhân.")
                        for log_msg in evidence_logs:
                            print(f"   -> {log_msg}")
                        print("=" * 60 + "\n")

                        clip_frames = list(reader.history_buffer)
                        clip_path = f"accident_evid_{CAMERA_ID}_{frame_count}.mp4"
                        #video_writer_worker.save_clip(clip_frames, clip_path)

                        accident_payload = {
                            "camera_id": CAMERA_ID,
                            "frame_count": frame_count,
                            "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "accident_detected": True,
                            "confidence_score": 0.85,
                            "alert_level": "HIGH",
                            "vehicles_involved": pending['vehicle_types'],
                            "video_clip_path": clip_path
                        }
                        network_worker.send_alert(accident_payload)
                    else:
                        print(
                            f"\033[92m[✅ FALSE ALARM] Hủy nghi ngờ Frame {pending['start_frame']}. Hiện trường đã giải tỏa.\033[0m")

                pending_incidents = surviving_pending


            # 3. DỌN DẸP BỘ NHỚ AI
            active_incidents = [inc for inc in active_incidents if frame_count - inc['frame'] < COOLDOWN_FRAMES]
            for tid in list(active_trackers.keys()):
                if tid not in current_frame_ids:
                    if not hasattr(active_trackers[tid], 'lost_frames'):
                        active_trackers[tid].lost_frames = 0
                    active_trackers[tid].lost_frames += 1
                    if active_trackers[tid].lost_frames >= 30:
                        del active_trackers[tid]
                else:
                    active_trackers[tid].lost_frames = 0

            # 4. ĐO LƯỜNG VÀ HIỂN THỊ
            # ================= Code tính fps cũ =================== #
            # elapsed_time = time.time() - start_time
            # fps = frame_count / elapsed_time if elapsed_time > 0 else 0
            #
            # # Vẽ thanh trạng thái nền đen phía trên cùng
            # cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
            # cv2.putText(frame, f"AI FPS: {fps:.1f} | Frame: {frame_count}", (15, 25),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            # ================= Hết Code tính fps cũ =================== #
            # --- DỪNG BẤM GIỜ ---
            frame_process_time = time.perf_counter() - frame_start_time

            # Tính FPS tức thời (Tránh chia cho 0)
            instant_fps = 1.0 / frame_process_time if frame_process_time > 0 else 0.0

            # Làm mượt FPS bằng công thức EMA (giống hệt cách cậu làm với vận tốc)
            if smoothed_fps == 0.0:
                smoothed_fps = instant_fps
            else:
                smoothed_fps = 0.8 * smoothed_fps + 0.2 * instant_fps

            # Ghi dữ liệu ra file CSV để lát nữa mở bằng Excel vẽ biểu đồ
            num_vehicles = len(active_trackers)
            csv_writer.writerow([frame_count, num_vehicles, round(smoothed_fps, 2)])

            # Vẽ thanh trạng thái nền đen phía trên cùng
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
            cv2.putText(frame, f"AI FPS: {smoothed_fps:.1f} | Frame: {frame_count} | Xe: {num_vehicles}",
                        (15, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # --- CODE THÊM MỚI: KHOANH VÙNG TAI NẠN ---
            # Duyệt qua danh sách các vụ tai nạn đang active và vẽ vòng tròn đỏ tại tâm
            for incident in active_incidents:
                cx, cy = int(incident['centroid'][0]), int(incident['centroid'][1])
                # Vẽ vòng tròn bán kính 60px, độ dày viền 3px, màu Đỏ (0, 0, 255)
                cv2.circle(frame, (cx, cy), 60, (0, 0, 255), 3)
                # Thêm nhãn text ngay cạnh vùng tai nạn
                cv2.putText(frame, "TAI NAN", (cx - 40, cy - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            # ----------------------------------------

            # --- CƠ CHẾ GIỮ CẢNH BÁO TRÊN MÀN HÌNH TRONG 5 GIÂY (CẢNH BÁO SAU ĐÈ CẢNH BÁO TRƯỚC) ---
            if time.time() - last_incident_time < SHOW_ALERT_DURATION:
                # Vẽ một panel đỏ mờ hoặc viền khung chữ cảnh báo nổi bật
                cv2.rectangle(frame, (30, 60), (450, 120), (0, 0, 150), -1)  # Nền đỏ sẫm cho chữ
                cv2.putText(frame, "CANH BAO: TAI NAN!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 255), 3, cv2.LINE_AA)

            cv2.imshow("He Thong Loi AI - Thuc Chien", frame)

            # --- CƠ CHẾ GỠ LỖI (DEBUG MODE) ---
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):  # Bấm 'q' để thoát an toàn
                break
            elif key == ord('p'):  # Bấm 'p' (Pause) để đóng băng thời gian
                print("[DEBUG] Hệ thống tạm dừng. Bấm phím bất kỳ trên bàn phím để chạy tiếp...")
                cv2.waitKey(0)  # Số 0 nghĩa là: Đứng hình vĩnh viễn cho đến khi người dùng gõ phím

    except KeyboardInterrupt:
        print("[HỆ THỐNG] Người dùng cưỡng chế dừng chương trình.")
    finally:
        # Tắt toàn bộ hệ thống an toàn
        reader.stop()
        network_worker.stop()
        video_writer_worker.stop()
        cv2.destroyAllWindows()
        csv_file.close()
        print("[HỆ THỐNG] Đã tắt luồng an toàn.")