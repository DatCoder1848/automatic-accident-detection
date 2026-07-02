# Intersection "giao" over "tren" Union "hop"
def calculate_iou(boxA, boxB):
    # box format: [x_min, y_min, x_max, y_max]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Tính diện tích phần giao (Intersection)
    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0

    # Tính diện tích của từng hộp
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    # Tính tỷ lệ IoU
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou


# ============================== Cấu trúc dữ liệu quản lý Phương tiện (VehicleTracker) =============================== #

import numpy as np
from collections import deque


class VehicleTrack:
    def __init__(self, track_id, vehicle_type="unknown", max_history=5):
        self.track_id = track_id
        self.vehicle_type = vehicle_type
        # Hàng đợi lưu tâm xe (cx, cy) của N frames gần nhất
        self.centroids = deque(maxlen=max_history)
        # Hàng đợi lưu vận tốc của N frames gần nhất
        self.velocities = deque(maxlen=max_history)

        self.current_box = None
        self.acceleration = 0.0

    def update(self, box):
        """Cập nhật tọa độ mới mỗi khi có frame mới và tính toán động học"""
        self.current_box = box
        cx = (box[0] + box[2]) / 2.0
        cy = (box[1] + box[3]) / 2.0

        # 1. Cập nhật vị trí
        self.centroids.append(np.array([cx, cy]))

        # 2. Tính vận tốc (Dựa trên khoảng cách Euclidean với frame trước)
        if len(self.centroids) >= 2:
            dist = np.linalg.norm(self.centroids[-1] - self.centroids[-2])
            self.velocities.append(dist)

        # 3. Tính gia tốc (Dựa trên sự thay đổi vận tốc)
        if len(self.velocities) >= 2:
            self.acceleration = self.velocities[-1] - self.velocities[-2]