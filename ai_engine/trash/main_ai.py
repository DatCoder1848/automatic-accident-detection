import os
import cv2
from ultralytics import YOLO
# Nạp công cụ toán học và Class quản lý phương tiện từ file kinematics.py
from kinematics import calculate_iou, VehicleTrack
import math
import argparse
import json
from datetime import datetime, UTC
import base64
from video_utils import *
from api_client import report_accident, upload_video, get_camera_id_by_source
import threading

parser = argparse.ArgumentParser(description = 'AI core detecting accidents ')
parser.add_argument(
    "--source",
    type = str,
    required = True,
    help = 'path to video file'
)
parser.add_argument(
    "--camera-id",
    type = str,
    default = None,
    help = 'camera UUID from backend (auto-resolves if not provided)'
)

# Tien hanh doc tham so nguoi dung nhap vao tu Terminal
args = parser.parse_args()

# Resolve camera ID
camera_id = args.camera_id
if not camera_id:
    camera_id = get_camera_id_by_source(args.source)
    if camera_id:
        print(f"[INIT] Resolved camera ID: {camera_id}")
    else:
        print("[INIT] ⚠️ Could not resolve camera ID. Accidents will not be reported to backend.")

# Lấy đường dẫn tuyệt đối của thư mục chứa file code hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# Kết hợp với thư mục đích (nó sẽ tự tính toán chuẩn xác tương đương với ../)
output_dir = os.path.abspath(os.path.join(current_dir, '..', 'data_storage', 'video_clips', 'accidents'))

# Tự động tạo thư mục nếu hệ thống chưa có sẵn (tránh lỗi OpenCV không ghi được file)
os.makedirs(output_dir, exist_ok=True)


print("Đang khởi động hệ thống...")
model = YOLO("yolov8n.pt")
video_path = args.source
cap = cv2.VideoCapture(video_path)

# Dictionary quản lý các đối tượng xe đang xuất hiện trên màn hình thay cho bien vehicle_histories cũ
active_trackers = {}
# Danh sách lưu các vùng đang xảy ra sự cố: [{'centroid': (cx, cy), 'time': timestamp}]
active_incidents = []
INCIDENT_RADIUS = 200  # Tăng nhẹ bán kính lên 200 pixel cho an toàn
COOLDOWN_FRAMES = 200   # Đóng băng cảnh báo trong 90 frames (tương đương khoảng 3 giây video)
FRAME_SKIP = 2  # Hệ thống chỉ xử lý 1 khung hình sau mỗi 3 khung hình trôi qua
frame_count = 0        # Bộ đếm thời gian tuyệt đối của video

frame_buffer = deque(maxlen=150)  # Buffer luu lien tuc 150 frame gan nhat
# Lấy FPS gốc của video nguồn (nếu không lấy được, mặc định là 30)
CAMERA_FPS = int(cap.get(cv2.CAP_PROP_FPS)) or 30

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame_count += 1  # Đồng hồ thời gian của video bắt đầu tích tắc

    # THÊM DÒNG NÀY: Giảm độ phân giải video để tăng tốc độ xử lý FPS
    frame = cv2.resize(frame, (1024, 576))

    # Them frame hien tai vao buffer:
    frame_buffer.append(frame.copy())

    # ------------------ KỸ THUẬT FRAME SKIPPING ------------------
    # Nếu số thứ tự frame không chia hết cho 3 -> Bỏ qua, không gọi YOLO
    if frame_count % FRAME_SKIP != 0:
        continue
    # YOLO Tracking
    results = model.track(frame, classes=[2, 3, 5, 7], persist=True, tracker="bytetrack.yaml", verbose=False)

    # Danh sách ID các xe xuất hiện TRONG FRAME NÀY
    current_frame_ids = []

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.cpu().numpy().astype(int)

        # BỔ SUNG: Lấy thêm mảng ID phân loại xe và từ điển tên xe của YOLO
        cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)
        class_names = model.names

        # 1. CẬP NHẬT TRẠNG THÁI CHO TỪNG CHIẾC XE
        for box, track_id, cls_id in zip(boxes, ids, cls_ids):
            current_frame_ids.append(track_id)

            # Nếu đây là xe mới xuất hiện, khởi tạo đối tượng VehicleTrack mới cho nó
            if track_id not in active_trackers:
                # Trích xuất tên xe (VD: 'car', 'motorcycle') và truyền vào OOP
                veh_type = class_names[cls_id]
                active_trackers[track_id] = VehicleTrack(track_id, vehicle_type=veh_type)

            # Gọi hàm update() của đối tượng để nó tự động tính toán vận tốc, gia tốc, tọa độ
            current_vehicle = active_trackers[track_id]
            current_vehicle.update(box)

            # Lấy thông số từ đối tượng để vẽ lên màn hình
            x_min, y_min, x_max, y_max = map(int, box)

            # Lấy vận tốc hiện tại (nếu chưa đủ dữ liệu tính thì mặc định là 0)
            speed = current_vehicle.velocities[-1] if len(current_vehicle.velocities) > 0 else 0.0

            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
            cv2.putText(frame, f"ID:{track_id} v:{speed:.1f}", (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

            # --- ĐO LƯỜNG GIA TỐC ---
            # Chỉ in ra log nếu xe đang giảm tốc độ (gia tốc âm) để tránh rác màn hình
            # if current_vehicle.acceleration < -1.0:
            #     print(f"[LOG ĐỘNG HỌC] Frame {frame_count} | ID: {track_id} | Vận tốc: {speed:.1f} | Gia tốc: {current_vehicle.acceleration:.1f}")

        # 2. LOGIC BẮT VA CHẠM (SPATIO-TEMPORAL CLUSTERING)
        for i in range(len(current_frame_ids)):
            for j in range(i + 1, len(current_frame_ids)):
                id_A = current_frame_ids[i]
                id_B = current_frame_ids[j]

                vehicle_A = active_trackers[id_A]
                vehicle_B = active_trackers[id_B]

                iou_score = calculate_iou(vehicle_A.current_box, vehicle_B.current_box)

                if iou_score > 0.1:
                    # Lấy gia tốc thay vì vận tốc
                    a_A = vehicle_A.acceleration
                    a_B = vehicle_B.acceleration

                    if a_A <= -3.0 or a_B <= -3.0:
                        crash_cx = (vehicle_A.centroids[-1][0] + vehicle_B.centroids[-1][0]) / 2.0
                        crash_cy = (vehicle_A.centroids[-1][1] + vehicle_B.centroids[-1][1]) / 2.0

                        is_new_incident = True
                        for incident in active_incidents:
                            # Dùng frame_count để trừ đi frame lưu sự cố
                            if frame_count - incident['frame'] < COOLDOWN_FRAMES:  # Neu thoa dieu kien nghia la frame này vẫn đang trong vụ tai nạn gần nhất
                                dist = math.sqrt((crash_cx - incident['centroid'][0]) ** 2 + (
                                            crash_cy - incident['centroid'][1]) ** 2)
                                if dist < INCIDENT_RADIUS:
                                    is_new_incident = False  # Nằm trong vùng báo động cũ, bỏ qua!
                                    break

                        if is_new_incident:
                            # Lưu sự kiện theo tọa độ và số frame hiện tại
                            active_incidents.append({'centroid': (crash_cx, crash_cy), 'frame': frame_count})

                            cv2.putText(frame, "CANH BAO: TAI NAN!", (50, 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

                            # Thuc hien trich xuat frame thanh hinh anh va mã hóa base64:
                            base64_string = ""
                            is_success, encoded_img = cv2.imencode('.jpg', frame)
                            if is_success:
                                base64_string = base64.b64encode(encoded_img).decode('utf-8')
                            else:
                                print('❌ CANH BAO!!! -> Du lieu hinh anh khong the trich xuat!')

                            # Trich xuat doan video tai nan tu Buffer:
                            buffer_snapshot = list(frame_buffer)
                            output_path = os.path.join(output_dir, f'accident_{frame_count}.mp4')
                            video_thread = threading.Thread(
                                target=generate_video_from_buffer,
                                args=(buffer_snapshot, output_path, CAMERA_FPS)
                            )
                            video_thread.start()

                            # TẠO GÓI TIN JSON BÁO CÁO VÀ GỬI LÊN BACKEND
                            accident_payload = {
                                "camera_id": camera_id,
                                "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "accident_detected": True,
                                "confidence_score": round(float(iou_score), 2),
                                "alert_level": "HIGH",
                                "vehicles_involved": [vehicle_A.vehicle_type, vehicle_B.vehicle_type],
                                "evidence_image_base64": "", #base64_string,
                                "video_clip_path": output_path
                            }
                            # In ra Terminal để kiểm tra trước khi gửi API
                            print("\n[SYSTEM] ĐÃ ĐÓNG GÓI JSON THÀNH CÔNG:")
                            print(json.dumps(accident_payload, indent=2))
                            print(
                                f"[ALARM] Xác nhận va chạm khu vực tọa độ ({int(crash_cx)}, {int(crash_cy)}) | IoU: {iou_score:.2f} | Frame: {frame_count}")

                            # GỬI LÊN BACKEND API (2-THREAD ASYNC FLOW)
                            if camera_id:
                                # Map confidence to severity level
                                severity = "HIGH" if iou_score > 0.3 else "MEDIUM" if iou_score > 0.15 else "LOW"
                                description = f"Collision detected between {vehicle_A.vehicle_type} and {vehicle_B.vehicle_type} at frame {frame_count}"

                                # THREAD 1: Gửi cảnh báo tức thì (không chờ video)
                                def send_alert_then_video():
                                    accident_id = report_accident(
                                        camera_id,
                                        round(float(iou_score), 2),
                                        severity,
                                        description=description
                                    )
                                    # THREAD 2: Chờ video render xong rồi upload
                                    if accident_id:
                                        video_thread.join()  # Đợi video_thread xuất file xong
                                        upload_video(accident_id, output_path)

                                api_thread = threading.Thread(target=send_alert_then_video)
                                api_thread.start()

    # 3. DỌN DẸP BỘ NHỚ
    # Xóa các sự cố đã trôi qua quá 90 frames
    active_incidents = [inc for inc in active_incidents if frame_count - inc['frame'] < COOLDOWN_FRAMES]

    # Xóa các xe đã đi khuất
    ids_to_remove = [tid for tid in active_trackers if tid not in current_frame_ids]
    for tid in ids_to_remove:
        del active_trackers[tid]

    cv2.imshow("He Thong Phat Hien Tai Nan - OOP", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()