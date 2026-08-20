import threading
import queue
import time
from collections import deque

import cv2


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