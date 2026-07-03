import cv2
from collections import deque

# Trich xuat cac frame trong buffer thanh file mp4
def generate_video_from_buffer (frame_buffer, output_path, fps=30):
    # Kiem tra buffer:
    if not frame_buffer:
        print('❌ CẢNH BÁO!!! -> Buffer khong co du lieu!')
        return

    try:
        # Lay thong so kich thuoc tu frame dau tien:
        first_frame = frame_buffer[0]
        height, width, _ = first_frame.shape
        # Khoi tao bo ghi video (dung codec mp4v thong dung):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        for frame in frame_buffer:
            out.write(frame)

        out.release()
        print(f'✌️ Da xuat file Video thanh cong: {output_path}')
        return True
    except Exception as e:
        print(f'LOI XAY RA TRONG QUA TRINH TRICH XUAT VIDEO: {e}')
        return False



