import torch
from ultralytics import YOLO

print("--- KIỂM TRA MÔI TRƯỜNG PHẦN CỨNG ---")
print("1. PyTorch có nhận diện được GPU CUDA không?:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("2. Tên Card Đồ Họa:", torch.cuda.get_device_name(0))

model = YOLO("../yolo11s.pt")
# Gọi thử một lệnh dự đoán rỗng để ép YOLO khởi tạo phần cứng
model.predict(source="https://ultralytics.com/images/bus.jpg", imgsz=640, verbose=False)
print("3. YOLO đang thực thi trên thiết bị:", model.device)