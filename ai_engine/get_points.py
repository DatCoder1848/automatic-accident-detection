import cv2

# Biến toàn cục lưu danh sách các điểm đã click
points = []


def click_event(event, x, y, flags, params):
    """Hàm lắng nghe sự kiện click chuột"""
    if event == cv2.EVENT_LBUTTONDOWN:  # Khi click chuột trái
        points.append((x, y))
        print(f"[TỌA ĐỘ] Điểm số {len(points)}: (x={x}, y={y})")

        # Vẽ một chấm đỏ và in tọa độ ngay trên ảnh để dễ nhìn
        cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(frame, f"{x},{y}", (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.imshow("Lay Toa Do (Click 4 diem roi bam Q)", frame)


if __name__ == "__main__":
    # Đường dẫn file video cậu đang test
    video_path = "../data_storage/video_clips/positive/crash_16.mp4" # negative/normal_11.mp4"  #
    cap = cv2.VideoCapture(video_path)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 50)
    # Lấy thử khung hình đầu tiên
    success, frame = cap.read()
    if not success:
        print("Lỗi: Không đọc được video.")
        exit()

    # BẮT BUỘC: Ép về đúng kích thước hệ thống đang chạy
    frame = cv2.resize(frame, (1024, 576))

    print("[HƯỚNG DẪN] Click chuột trái vào 4 điểm trên mặt đường tạo thành một hình chữ nhật thực tế.")
    print("[HƯỚNG DẪN] Bấm phím 'q' để thoát.")

    cv2.imshow("Lay Toa Do (Click 4 diem roi bam Q)", frame)

    # Gắn hàm lắng nghe chuột vào cửa sổ OpenCV
    cv2.setMouseCallback("Lay Toa Do (Click 4 diem roi bam Q)", click_event)

    cv2.waitKey(0)
    cap.release()
    cv2.destroyAllWindows()

    print("\n--- KẾT QUẢ ---")
    print(f"4 điểm của cậu là: {points}")