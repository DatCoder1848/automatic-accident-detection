import numpy as np
from collections import deque
import cv2



# ============================== HÀM TÍNH TOÁN VÙNG GIAO NHAU (IoU) =============================== #
def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    return interArea / float(boxAArea + boxBArea - interArea)


# ============================== LỚP BẺ CONG KHÔNG GIAN (CAMERA CALIBRATION) =============================== #
class PerspectiveCamera:
    def __init__(self, src_pts, pixel_to_meter, bev_width=150, bev_height=250):
        # Nguồn: Nhận tọa độ động từ cấu hình
        self.src_pts = np.float32(src_pts)

        self.BEV_WIDTH = bev_width
        self.BEV_HEIGHT = bev_height
        self.PIXEL_TO_METER = pixel_to_meter

        self.dst_pts = np.float32([
            [0, 0],
            [self.BEV_WIDTH, 0],
            [self.BEV_WIDTH, self.BEV_HEIGHT],
            [0, self.BEV_HEIGHT]
        ])

        self.M = cv2.getPerspectiveTransform(self.src_pts, self.dst_pts)

    def transform_point(self, x, y):
        pts = np.array([[[x, y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(pts, self.M)
        return transformed[0][0][0], transformed[0][0][1]


# Biến toàn cục trống, sẽ được gán giá trị khi khởi động phần mềm
camera_calibrator = None


def init_calibrator(config_data):
    """Hàm khởi tạo camera dựa trên cấu hình JSON"""
    global camera_calibrator
    camera_calibrator = PerspectiveCamera(
        src_pts=config_data["src_pts"],
        pixel_to_meter=config_data["pixel_to_meter"],
        bev_width=config_data["bev_width"],
        bev_height=config_data["bev_height"]
    )



# ============================== QUẢN LÝ PHƯƠNG TIỆN (VEHICLE TRACKER) =============================== #
class VehicleTrack:
    def __init__(self, track_id, vehicle_type="unknown", max_history=5):
        self.track_id = track_id
        self.vehicle_type = vehicle_type

        # THÊM DÒNG NÀY: Lưu tọa độ pixel gốc để vẽ đồ họa
        self.centroids = deque(maxlen=max_history)

        # Lưu tọa độ TÂM XE nhưng ở góc nhìn TỪ TRÊN TRỜI XUỐNG (BEV)
        self.centroids_bev = deque(maxlen=max_history)

        # Vận tốc bây giờ sẽ mang đơn vị km/h
        self.velocities = deque(maxlen=max_history)
        self.current_box = None
        self.acceleration = 0.0

        # Hệ thống của cậu chạy 30 FPS, cấu hình FRAME_SKIP = 3
        # Tức là khoảng cách giữa 2 lần đo lường là 3/30 = 0.1 giây
        self.time_delta = 1/30

    def update(self, box):
        self.current_box = box

        # Tọa độ pixel thô từ camera
        cx = (box[0] + box[2]) / 2.0
        cy = (box[1] + box[3]) / 2.0

        # THÊM DÒNG NÀY: Nạp tọa độ vào mảng gốc
        self.centroids.append((cx, cy))

        # 1. BẺ CONG KHÔNG GIAN: Quy đổi pixel thô sang tọa độ chuẩn BEV
        bev_x, bev_y = camera_calibrator.transform_point(cx, cy)
        self.centroids_bev.append(np.array([bev_x, bev_y]))

        # 2. TÍNH VẬN TỐC (VẬT LÝ HỌC)
        if len(self.centroids_bev) >= 2:
            # Khoảng cách trên bản đồ (Pixel BEV)
            pixel_dist = np.linalg.norm(self.centroids_bev[-1] - self.centroids_bev[-2])

            # Khoảng cách thực tế (Mét)
            meter_dist = pixel_dist * camera_calibrator.PIXEL_TO_METER

            # Vận tốc $v = \frac{s}{t}$ (m/s)
            speed_mps = meter_dist / self.time_delta

            # Quy đổi m/s sang km/h (nhân với 3.6)
            speed_kmh = speed_mps * 3.6

            # Bộ lọc nhiễu: Nếu vận tốc lớn hơn 150km/h (ảo) do sai số YOLO giật khung hình, gán lại bằng vận tốc cũ
            if speed_kmh > 150.0 and len(self.velocities) > 0:
                speed_kmh = self.velocities[-1]

            self.velocities.append(speed_kmh)

        # 3. TÍNH GIA TỐC $a = \Delta v$
        if len(self.velocities) >= 2:
            self.acceleration = self.velocities[-1] - self.velocities[-2]