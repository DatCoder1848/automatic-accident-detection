from ultralytics import YOLO

print("[HỆ THỐNG] Khởi tạo quá trình biên dịch mô hình sang TensorRT...")

# 1. Tải mô hình gốc định dạng PyTorch
model = YOLO("../yolo11s.pt")

# 2. Thực thi lệnh Export
# format="engine": Chọn chuẩn TensorRT
# device=0: Ép chạy trên GPU CUDA đầu tiên (RTX 2050)
# half=True: Sử dụng chuẩn dấu phẩy động 16-bit (FP16) để tăng gấp đôi tốc độ xử lý
# workspace=2: Cấp phát tối đa 2GB VRAM cho quá trình biên dịch
model.export(format="engine", device=0, half=True, workspace=2)

print("[HỆ THỐNG] Đã hoàn tất biên dịch! Hãy kiểm tra file yolov8n.engine trong thư mục.")