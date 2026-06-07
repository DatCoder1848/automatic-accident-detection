import cv2
import math
from ultralytics import YOLO


# ----------------- HÀM TOÁN HỌC KIỂM TRA VA CHẠM -----------------
def check_overlap(box1, box2):
    """Áp dụng công thức tìm vùng giao nhau của 2 Bounding Box"""
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    x_left = max(x1_min, x2_min)
    x_right = min(x1_max, x2_max)
    y_top = max(y1_min, y2_min)
    y_bottom = min(y1_max, y2_max)

    # Nếu thỏa mãn điều kiện này, 2 hộp đang đè lên nhau
    if x_left < x_right and y_top < y_bottom:
        return True
    return False


# -----------------------------------------------------------------

print("Đang khởi động hệ thống...")
model = YOLO("yolov8n.pt")
video_path = "../data_storage/video_clips/positive/crash_7.mp4"
cap = cv2.VideoCapture(video_path)

vehicle_history = {}
reported_crashes = set() # Bộ nhớ chống spam cảnh báo

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    results = model.track(frame, classes=[2, 3, 5, 7], persist=True, tracker="bytetrack.yaml", verbose=False)

    # Mảng tạm thời để lưu thông tin của tất cả các xe trong khung hình HIỆN TẠI
    current_frame_vehicles = []

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        ids = results[0].boxes.id.cpu().numpy().astype(int)

        for box, track_id in zip(boxes, ids):
            x_min, y_min, x_max, y_max = box
            cx = int((x_min + x_max) / 2)
            cy = int((y_min + y_max) / 2)

            speed = 0.0
            if track_id in vehicle_history:
                prev_cx, prev_cy = vehicle_history[track_id]
                speed = math.sqrt((cx - prev_cx) ** 2 + (cy - prev_cy) ** 2)

            vehicle_history[track_id] = (cx, cy)

            # Đóng gói dữ liệu xe hiện tại vào mảng
            current_frame_vehicles.append({
                "id": track_id,
                "box": box,
                "speed": speed,
                "centroid": (cx, cy)
            })

            # Vẽ giao diện cơ bản
            cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
            cv2.putText(frame, f"ID:{track_id} S:{speed:.1f}", (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        # ----------------- LOGIC QUÉT VA CHẠM (COLLISION SCANNER) -----------------
        for i in range(len(current_frame_vehicles)):
            for j in range(i + 1, len(current_frame_vehicles)):
                xe_A = current_frame_vehicles[i]
                xe_B = current_frame_vehicles[j]

                # Kiểm tra Không gian: Khung chữ nhật đè lên nhau?
                if check_overlap(xe_A["box"], xe_B["box"]):

                    # Tạo một định danh duy nhất cho vụ va chạm này (vd: cặp 1 và 22)
                    pair_id = tuple(sorted([xe_A["id"], xe_B["id"]]))

                    # Màng lọc 1: Kiểm tra xem vụ này đã báo động chưa?
                    if pair_id not in reported_crashes:

                        # Màng lọc 2: Kiểm tra Động học (Loại bỏ xe đỗ)
                        if xe_A["speed"] > 2.0 or xe_B["speed"] > 2.0:
                            cv2.putText(frame, "CANH BAO: TAI NAN!", (50, 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                            cv2.line(frame, xe_A["centroid"], xe_B["centroid"], (0, 0, 255), 3)

                            print(f"[ALARM] Xác nhận va chạm vật lý giữa ID {xe_A['id']} và ID {xe_B['id']}")

                            # Lưu vào bộ nhớ để khóa cảnh báo cho cặp ID này
                            reported_crashes.add(pair_id)

    cv2.imshow("He Thong Phat Hien Tai Nan", frame)

    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()