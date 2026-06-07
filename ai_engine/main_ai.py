import cv2
import math
from ultralytics import YOLO
# Nạp công cụ toán học và Class quản lý phương tiện từ file kinematics.py
from kinematics import calculate_iou, VehicleTrack


print("Đang khởi động hệ thống...")
model = YOLO("yolov8n.pt")
video_path = "../data_storage/video_clips/positive/crash_7.mp4"
cap = cv2.VideoCapture(video_path)

# Dictionary quản lý các đối tượng xe đang xuất hiện trên màn hình thay cho bien vehicle_histories cũ
active_trackers = {}
reported_crashes = set() # Bộ nhớ chống spam cảnh báo

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

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

        # 2. LOGIC BẮT VA CHẠM DỰA TRÊN OOP VÀ IOU
        # Duyệt qua các cặp xe đang có mặt trong frame hiện tại để kiểm tra
        for i in range(len(current_frame_ids)):
            for j in range(i + 1, len(current_frame_ids)):
                id_A = current_frame_ids[i]
                id_B = current_frame_ids[j]

                vehicle_A = active_trackers[id_A]
                vehicle_B = active_trackers[id_B]

                # Gọi hàm toán học tính tỷ lệ giao nhau của 2 Bounding Box
                iou_score = calculate_iou(vehicle_A.current_box, vehicle_B.current_box)

                # NẾU tỷ lệ giao nhau > 10% (0.1) -> Có sự va chạm vật lý hoặc cực kỳ sát nhau
                if iou_score > 0.1:
                    pair_id = tuple(sorted([id_A, id_B]))

                    if pair_id not in reported_crashes:
                        # Kiểm tra thêm điều kiện vận tốc để loại bỏ xe đang đỗ cạnh nhau
                        v_A = vehicle_A.velocities[-1] if len(vehicle_A.velocities) > 0 else 0
                        v_B = vehicle_B.velocities[-1] if len(vehicle_B.velocities) > 0 else 0

                        if v_A > 2.0 or v_B > 2.0:
                            cv2.putText(frame, f"TAI NAN: {id_A} & {id_B}", (50, 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                            print(f"[ALARM] Va chạm giữa ID {id_A} và {id_B} | IoU: {iou_score:.2f}")

                            reported_crashes.add(pair_id)

    # 3. DỌN DẸP BỘ NHỚ (Memory Management)
    # Xóa các đối tượng xe đã đi khuất khỏi màn hình để giải phóng RAM
    ids_to_remove = [tid for tid in active_trackers if tid not in current_frame_ids]
    for tid in ids_to_remove:
        del active_trackers[tid]

    cv2.imshow("He Thong Phat Hien Tai Nan - OOP", frame)

    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()