import cv2
from ultralytics import YOLO

# 1. Tải mô hình YOLOv8 phiên bản Nano (Siêu nhẹ, chạy mượt trên CPU)
# Lần chạy đầu tiên, máy sẽ tự động tải file yolov8n.pt (khoảng 6MB) về thư mục dự án
print("Đang tải mô hình não bộ YOLOv8...")
model = YOLO("yolov8n.pt")

# 2. Mở file video số 7 để test
video_path = "../data_storage/video_clips/positive/crash_7.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Lỗi: Không đọc được video!")
    exit()

print("Bắt đầu nhận diện...")
while True:
    success, frame = cap.read()
    if not success:
        break

    # 3. Đưa khung hình cho YOLO quét
    # tham số classes=[2, 3, 5, 7] dùng để bộ lọc chỉ nhận diện (Ô tô, Xe máy, Xe buýt, Xe tải)
    results = model(frame, classes=[2, 3, 5, 7], verbose=False)

    # 4. Lấy bức ảnh đã được YOLO vẽ sẵn khung chữ nhật
    annotated_frame = results[0].plot()

    # Hiển thị lên màn hình
    cv2.imshow("He Thong Nhan Dien - YOLOv8", annotated_frame)

    # Nhấn 'q' để thoát
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()