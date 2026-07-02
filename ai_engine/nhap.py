import cv2
import math
from ultralytics import YOLO
# Nạp công cụ toán học và Class quản lý phương tiện từ file kinematics.py
from kinematics import calculate_iou, VehicleTrack
import time

print("Đang khởi động hệ thống...")
model = YOLO("yolov8n.pt")
video_path = "../data_storage/video_clips/positive/crash_7.mp4"
cap = cv2.VideoCapture(video_path)

# Dictionary quản lý các đối tượng xe đang xuất hiện trên màn hình thay cho bien vehicle_histories cũ
active_trackers = {}
# Danh sách lưu các vùng đang xảy ra sự cố: [{'centroid': (cx, cy), 'time': timestamp}]
active_incidents = []
INCIDENT_RADIUS = 200  # Tăng nhẹ bán kính lên 200 pixel cho an toàn
COOLDOWN_FRAMES = 200  # Đóng băng cảnh báo trong 90 frames (tương đương khoảng 3 giây video)
FRAME_SKIP = 1  # Hệ thống chỉ xử lý 1 khung hình sau mỗi 3 khung hình trôi qua
frame_count = 0  # Bộ đếm thời gian tuyệt đối của video

# --- CÁC BIẾN ĐIỀU KHIỂN TỐC ĐỘ VÀ TRẠNG THÁI VIDEO ---
is_paused = False  # Trạng thái tạm dừng video
delay_ms = 1  # Độ trễ mặc định giữa các khung hình (ms). Tăng số này = Video chạy chậm đi.

while cap.isOpened():
    # Nếu không bị tạm dừng thì mới đọc khung hình mới
    if not is_paused:
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1  # Đồng hồ thời gian của video bắt đầu tích tắc

        # ------------------ KỸ THUẬT FRAME SKIPPING ------------------
        # Nếu số thứ tự frame không chia hết cho 3 -> Bỏ qua, không gọi YOLO
        if frame_count % FRAME_SKIP != 0:
            continue

        # THÊM DÒNG NÀY: Giảm độ phân giải video để tăng tốc độ xử lý FPS
        frame = cv2.resize(frame, (1024, 576))

        # YOLO Tracking
        results = model.track(frame, classes=[2, 3, 5, 7], persist=True, tracker="bytetrack.yaml", verbose=False)

        # Danh sách ID các xe xuất hiện TRONG FRAME NÀY
        current_frame_ids = []

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)

            # 1. CẬP NHẬT TRẠNG THÁI CHO TỪNG CHIẾC XE
            for box, track_id in zip(boxes, ids):
                current_frame_ids.append(track_id)

                # Nếu đây là xe mới xuất hiện, khởi tạo đối tượng VehicleTrack mới cho nó
                if track_id not in active_trackers:
                    active_trackers[track_id] = VehicleTrack(track_id)

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

            # 2. LOGIC BẮT VA CHẠM (SPATIO-TEMPORAL CLUSTERING)
            for i in range(len(current_frame_ids)):
                for j in range(i + 1, len(current_frame_ids)):
                    id_A = current_frame_ids[i]
                    id_B = current_frame_ids[j]

                    vehicle_A = active_trackers[id_A]
                    vehicle_B = active_trackers[id_B]

                    iou_score = calculate_iou(vehicle_A.current_box, vehicle_B.current_box)

                    if iou_score > 0.1:
                        v_A = vehicle_A.velocities[-1] if len(vehicle_A.velocities) > 0 else 0
                        v_B = vehicle_B.velocities[-1] if len(vehicle_B.velocities) > 0 else 0

                        if v_A > 2.0 or v_B > 2.0:
                            crash_cx = (vehicle_A.centroids[-1][0] + vehicle_B.centroids[-1][0]) / 2.0
                            crash_cy = (vehicle_A.centroids[-1][1] + vehicle_B.centroids[-1][1]) / 2.0

                            is_new_incident = True
                            for incident in active_incidents:
                                # Dùng frame_count để trừ đi frame lưu sự cố
                                if frame_count - incident[
                                    'frame'] < COOLDOWN_FRAMES:  # Neu thoa dieu kien nghia la frame này vẫn đang trong vụ tai nạn gần nhất
                                    dist = math.sqrt((crash_cx - incident['centroid'][0]) ** 2 + (
                                            crash_cy - incident['centroid'][1]) ** 2)
                                    if dist < INCIDENT_RADIUS:
                                        is_new_incident = False  # Nằm trong vùng báo động cũ, bỏ qua!
                                        break

                            if is_new_incident:
                                # Lưu sự kiện theo tọa độ và số frame hiện tại
                                active_incidents.append({'centroid': (crash_cx, crash_cy), 'frame': frame_count})

                                cv2.putText(frame, "CANH BAO: TAI NAN!", (50, 100),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                                print(
                                    f"[ALARM] Xác nhận va chạm khu vực tọa độ ({int(crash_cx)}, {int(crash_cy)}) | IoU: {iou_score:.2f} | Frame: {frame_count}")

        # 3. DỌN DẸP BỘ NHỚ
        # Xóa các sự cố đã trôi qua quá 90 frames
        active_incidents = [inc for inc in active_incidents if frame_count - inc['frame'] < COOLDOWN_FRAMES]

        # Xóa các xe đã đi khuất (giữ nguyên code cũ của cậu)
        ids_to_remove = [tid for tid in active_trackers if tid not in current_frame_ids]

    # --- THIẾT KẾ THANH HƯỚNG DẪN Ở TRÊN CÙNG (TOP CONTROL BAR) ---
    # Vẽ một hình chữ nhật màu đen phủ lên phần trên cùng của frame (chiều cao 40 pixel)
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)

    # Chuỗi văn bản trạng thái và hướng dẫn phím bấm
    status_text = "PAUSED" if is_paused else f"RUNNING (Delay: {delay_ms}ms)"
    info_str = f"Frame: {frame_count} | Status: {status_text}"
    guide_str = "[Space]: Pause | [F]: Faster | [S]: Slower | [A]: Rewind | [D]: Forward | [Q]: Quit"

    # Vẽ chữ đè lên thanh bar màu đen
    cv2.putText(frame, info_str, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, guide_str, (frame.shape[1] - 620, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1,
                cv2.LINE_AA)

    cv2.imshow("He Thong Phat Hien Tai Nan - OOP", frame)

    # --- XỬ LÝ BÀN PHÍM (KEYBOARD EVENTS) ---
    key = cv2.waitKey(0 if is_paused else delay_ms) & 0xFF

    if key == ord('q'):  # Thoát chương trình
        break
    elif key == ord(' '):  # Phím cách: Tạm dừng / Tiếp tục
        is_paused = not is_paused
    elif key == ord('f'):  # Phím F: Tăng tốc video (giảm delay)
        delay_ms = max(1, delay_ms - 5)
        print(f"[CONTROL] Tăng tốc độ chiếu. Delay hiện tại: {delay_ms}ms")
    elif key == ord('s'):  # Phím S: Giảm tốc video (tăng delay)
        delay_ms += 5
        print(f"[CONTROL] Giảm tốc độ chiếu. Delay hiện tại: {delay_ms}ms")
    elif key == ord('d'):  # Phím D: Tua tiến 30 frames
        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + 30)
        frame_count += 30
        print(f"[CONTROL] Tua tiến 30 frames.")
    elif key == ord('a'):  # Phím A: Tua lùi 30 frames
        current_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        new_frame = max(0, current_frame - 30)
        cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)
        frame_count = max(0, frame_count - 30)
        print(f"[CONTROL] Tua lùi 30 frames.")

cap.release()
cv2.destroyAllWindows()
