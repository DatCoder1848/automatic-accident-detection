import os
from moviepy import VideoFileClip

num = 3

# 1. Đường dẫn file gốc của cậu
input_video = f"E:/Downloads/Phuc_nor_{num}.mp4" # "D:/Viec_hoc/Hoc_ki_2_nam_3/CD_HTTM/project/AAD/automatic-accident-detection/data_storage/video_clips/positive/crash_6.mp4" #
output_dir = "../../data_storage/video_clips/negative/" # positive/" #
os.makedirs(output_dir, exist_ok=True)

# 2. Mảng 8 mốc thời gian cậu đã xác định
segments = [
    (0, 10)
]

print("BẮT ĐẦU TIẾN TRÌNH CẮT VIDEO...")
for i, (start_time, end_time) in enumerate(segments):
    output_filename = os.path.join(output_dir, f"normal_{i + 5 + num}.mp4")
    print(f"Đang xử lý Clip {i + 1} (Từ {start_time}s -> {end_time}s)...")

    try:
        clip = VideoFileClip(input_video)

        # Xử lý cắt theo hàm chuẩn của từng phiên bản
        if hasattr(clip, 'subclipped'):
            cut_clip = clip.subclipped(start_time, end_time)
        else:
            cut_clip = clip.subclip(start_time, end_time)

            # Xuất file (Tắt âm thanh)
        cut_clip.write_videofile(output_filename, codec="libx264", audio=False, logger=None)

        clip.close()
        cut_clip.close()

    except Exception as e:
        print(f"Lỗi ở clip {i + 1}: {e}")

print("ĐÃ HOÀN THÀNH XUẤT FILE MP4 ĐỘC LẬP!")