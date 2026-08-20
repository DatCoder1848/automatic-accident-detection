import json
from ultralytics import YOLO

from ai_engine.kinematics import calculate_real_distance_meters
from ai_engine.video_stream import VideoReader
from kinematics import init_calibrator, calculate_iou, VehicleTrack, calculate_ios, get_smooth_accel, is_in_edge
import math
from datetime import datetime, UTC
import time
import cv2
import csv
from cloud_service import CloudAlertManager

if __name__ == "__main__":

    # 1. ĐỌC CẤU HÌNH CAMERA TỪ FILE JSON
    CONFIG_FILE = "cameras_config.json"
    CAMERA_ID =  "CAM_NOR_1" #  "CAM_CRASH_5" #  Chỉ cần đổi tên ID ở đây, toàn bộ hệ thống sẽ tự thay máu

    print(f"[HỆ THỐNG] Đang tải cấu hình cho {CAMERA_ID}...")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        all_cameras = json.load(f)

    cam_config = all_cameras[CAMERA_ID]

    # Tiêm cấu hình toán học vào bộ nhớ
    init_calibrator(cam_config)

    # 2. KHỞI TẠO CÁC CÔNG NHÂN VÀ MÔ HÌNH
    print("[HỆ THỐNG] Đang tải mô hình YOLO11s...")
    model = YOLO("../yolo11s.pt")#.to("cuda")

    # Lấy đường dẫn video động từ JSON
    test_video_path = cam_config["source"]

    # Bật Luồng Đọc
    reader = VideoReader(test_video_path, queue_size=30).start()

    # Bật Luồng Mạng
    API_URL = "http://localhost:3000/accidents"
    API_KEY = "ai-service-secret-key"
    cloud_manager = CloudAlertManager(API_URL, API_KEY)

    # 2. KHỞI TẠO CÁC BIẾN TRẠNG THÁI CỦA THUẬT TOÁN ĐỘNG HỌC
    active_trackers = {}
    active_incidents = []
    pending_incidents = []  # Hàng đợi chứa các Vùng nghi ngờ
    COOLDOWN_FRAMES = 900
    SPATIAL_COOLDOWN_METERS = 12.0
    VALIDATION_FRAMES = 90  # Thời gian kiểm chứng 3 giây (30fps * 3s)

    # Các biến bổ sung phục vụ hiển thị UI cảnh báo giữ trong 5 giây
    last_incident_time = 0.0
    SHOW_ALERT_DURATION = 5.0  # Thời gian hiển thị cảnh báo (giây)

    start_time = time.time()
    frame_count = 0

    # THÊM ĐOẠN NÀY DÀNH CHO ĐO FPS:
    smoothed_fps = 0.0  # Dùng EMA để làm mượt FPS hiển thị
    csv_file = open('fps_log_thuc_te_02.csv', 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Frame', 'So_Xe', 'FPS'])  # Tiêu đề cột cho Excel

    print("[HỆ THỐNG] Đang khởi chạy Luồng Suy Luận (AI Thread)...")

    try:
        while True:
            # Nếu mất mạng quá lâu và queue trống thì tự động thoát (Hoặc cậu có thể để nó chạy vĩnh viễn)
            if reader.stopped and reader.frame_queue.empty():
                break

            # --- RÚT ẢNH TỪ BĂNG CHUYỀN ---
            frame = reader.read()

            # Nếu băng chuyền trống (do mạng đang đứt), vẫn phải lắng nghe phím Q
            if frame is None:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue  # Bỏ qua AI, quay lại vòng lặp chờ ảnh mới

            frame_count += 1

            # --- BẮT ĐẦU BẤM GIỜ XỬ LÝ LÕI AI ---
            # Dùng perf_counter() chính xác hơn time.time() ở cấp độ mili-giây
            frame_start_time = time.perf_counter()

            # --- CHẠY YOLO TRACKING ---
            results = model.track(frame, classes=[2, 3, 5, 7], persist=True, imgsz=1024, agnostic_nms=False,
                                  tracker="botsort.yaml", conf=0.2, iou=0.7, verbose=False) #, device=0)

            current_frame_ids = []

            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                ids = results[0].boxes.id.cpu().numpy().astype(int)
                cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)
                class_names = model.names

                # 2.1 CẬP NHẬT TRẠNG THÁI CHO TỪNG CHIẾC XE
                for box, track_id, cls_id in zip(boxes, ids, cls_ids):
                    current_frame_ids.append(track_id)

                    if track_id not in active_trackers:
                        veh_type = class_names[cls_id]
                        active_trackers[track_id] = VehicleTrack(track_id, vehicle_type=veh_type)

                    current_vehicle = active_trackers[track_id]
                    current_vehicle.update(box)

                    x_min, y_min, x_max, y_max = map(int, box)
                    speed = current_vehicle.velocities[-1] if len(current_vehicle.velocities) > 0 else 0.0

                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
                    cv2.putText(frame, f"ID:{track_id} v:{speed:.1f}", (x_min, y_min - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

                # --- NHÁT CẮT 2: CODE DỌN DẸP 1 XE 2 ID SAU KHI ĐÃ CẬP NHẬT TỌA ĐỘ ---
                ids_to_kill = set()
                for i in range(len(current_frame_ids)):
                    for j in range(i + 1, len(current_frame_ids)):
                        id_1 = current_frame_ids[i]
                        id_2 = current_frame_ids[j]

                        if id_1 in active_trackers and id_2 in active_trackers:
                            box_1 = active_trackers[id_1].current_box
                            box_2 = active_trackers[id_2].current_box

                            # Tính IoS giữa 2 ID này
                            ios_dup = calculate_ios(box_1, box_2)

                            # Nếu đè nhau quá 65% -> 100% là 1 xe bị nhận diện thành 2 ID
                            if ios_dup > 0.7:
                                age_1 = len(active_trackers[id_1].centroids)
                                age_2 = len(active_trackers[id_2].centroids)

                                # Khai tử ID nào mới sinh ra (tuổi nhỏ hơn)
                                if age_1 > age_2:
                                    ids_to_kill.add(id_2)
                                else:
                                    ids_to_kill.add(id_1)

                # Xóa các ID giả khỏi current_frame_ids trước khi hệ thống kịp đưa chúng vào tính toán va chạm
                current_frame_ids = [tid for tid in current_frame_ids if tid not in ids_to_kill]
                # Loại bỏ ID giả khỏi frame hiện tại và xóa luôn khỏi bộ nhớ để nó không lọt xuống dưới
                for tid in ids_to_kill:
                    if tid in active_trackers:
                        del active_trackers[tid]
                # ------------------------------------------
            # -------------------------------------------------------------------------

                # ================= ĐÃ LÙI LỀ RA NGOÀI VÒNG LẶP =================
                # ================= BẮT ĐẦU KHỐI LOGIC LÕI =================

                # 2.2 LOGIC BẮT VA CHẠM (GIAI ĐOẠN 1: KÍCH HOẠT VÙNG NGHI NGỜ)
                all_active_ids = list(active_trackers.keys())
                # Dùng current_frame_ids để chỉ tính toán các xe đang có mặt trên màn hình
                for i in range(len(current_frame_ids)):
                    for j in range(i + 1, len(current_frame_ids)):
                        id_A = current_frame_ids[i]
                        id_B = current_frame_ids[j]

                        vehicle_A = active_trackers[id_A]
                        vehicle_B = active_trackers[id_B]

                        # Neu hai xe duoc canh bao truoc do thi bo qua
                        if vehicle_A.is_reported and vehicle_B.is_reported:
                            continue

                        if vehicle_A.current_box is None or vehicle_B.current_box is None:
                            continue

                        cy_A = vehicle_A.centroids[-1][1]
                        cy_B = vehicle_B.centroids[-1][1]
                        if cy_A < cam_config.get("horizon_y", 200) or cy_B < cam_config.get("horizon_y", 200):
                            continue

                        iou_score = calculate_iou(vehicle_A.current_box, vehicle_B.current_box)

                        # Tính toán vô điều kiện để lấy data thô
                        bev_A = vehicle_A.centroids_bev[-1]
                        bev_B = vehicle_B.centroids_bev[-1]
                        real_dist_meters = calculate_real_distance_meters(bev_A, bev_B, cam_config["pixel_to_meter"])

                        dist_limit = cam_config.get("dist_thresh", 5.0)
                        if real_dist_meters < dist_limit or iou_score > 0.03:
                            # Tính toán toàn bộ thông số Động học & Không gian trước khi lọc
                            smooth_a_A = get_smooth_accel(vehicle_A)
                            smooth_a_B = get_smooth_accel(vehicle_B)

                            v_A = vehicle_A.velocities[-1] if len(vehicle_A.velocities) > 0 else 0.0
                            v_B = vehicle_B.velocities[-1] if len(vehicle_B.velocities) > 0 else 0.0
                            max_v_A = max(list(vehicle_A.velocities)[-5:]) if len(
                                vehicle_A.velocities) > 0 else 0.0
                            max_v_B = max(list(vehicle_B.velocities)[-5:]) if len(
                                vehicle_B.velocities) > 0 else 0.0
                            delta_v_A = max_v_A - v_A
                            delta_v_B = max_v_B - v_B
                            age_A = len(vehicle_A.centroids)
                            age_B = len(vehicle_B.centroids)

                            # ================= LOG CHI TIẾT ĐỂ BẮT LỖI TẬN GỐC =================
                            # In log khi hai xe ở gần (< 5m) và có động học bất thường (phanh/văng) hoặc đè nhau
                            if real_dist_meters < 5.0 and (
                                    smooth_a_A < -3.0 or smooth_a_B < -3.0 or iou_score > 0.15):
                                box_A_str = f"[{int(vehicle_A.current_box[0])},{int(vehicle_A.current_box[1])},{int(vehicle_A.current_box[2])},{int(vehicle_A.current_box[3])}]"
                                box_B_str = f"[{int(vehicle_B.current_box[0])},{int(vehicle_B.current_box[1])},{int(vehicle_B.current_box[2])},{int(vehicle_B.current_box[3])}]"

                                print(
                                    f"\n[DEBUG-AI] Frame {frame_count} | {vehicle_A.vehicle_type}(ID:{id_A}) & {vehicle_B.vehicle_type}(ID:{id_B})")
                                print(
                                    f"  -> Không gian: IoU 2D = {iou_score:.2f} | Khoảng cách thực = {real_dist_meters:.1f}m")
                                print(f"  -> ID {id_A} (Tuổi: {age_A}f): Box = {box_A_str}")
                                print(
                                    f"     Động học: v={v_A:.1f} | max_v={max_v_A:.1f} | dV={delta_v_A:.1f} | a_mượt={smooth_a_A:.1f}")
                                print(f"  -> ID {id_B} (Tuổi: {age_B}f): Box = {box_B_str}")
                                print(
                                    f"     Động học: v={v_B:.1f} | max_v={max_v_B:.1f} | dV={delta_v_B:.1f} | a_mượt={smooth_a_B:.1f}")
                            # ===================================================================

                            # 1. KIỂM TRA BÓNG MA (GHOST DUPLICATION)
                            is_ghost_A = hasattr(vehicle_A, 'lost_frames') and vehicle_A.lost_frames > 0
                            is_ghost_B = hasattr(vehicle_B, 'lost_frames') and vehicle_B.lost_frames > 0
                            if (is_ghost_A or is_ghost_B) and iou_score > 0.4:
                                continue

                            # LỌC BÒ CHẬM (CRAWLING FILTER): Bỏ qua nếu cả 2 xe đều đang đi rà rà (< 5 km/h)
                            if max_v_A < 5.0 and max_v_B < 5.0:
                                continue

                            # TÍNH NGƯỠNG GIA TỐC ĐỘNG
                            t_near = cam_config.get("thresh_near", -6.0)
                            t_far = cam_config.get("thresh_far", -9.0)
                            y_split = cam_config.get("y_split", 400)
                            horizon_y = cam_config.get("horizon_y", 200)


                            def get_dynamic_thresh(cy):
                                if cy >= y_split: return t_near
                                if cy <= horizon_y: return t_far
                                ratio = (cy - horizon_y) / (y_split - horizon_y)
                                return t_far + ratio * (t_near - t_far)


                            thresh_A = get_dynamic_thresh(cy_A)
                            thresh_B = get_dynamic_thresh(cy_B)

                            # KHÓA CHẶT RÌA MÀN HÌNH CHO CẢ 2 ĐIỀU KIỆN
                            edge_A = is_in_edge(vehicle_A.current_box)
                            edge_B = is_in_edge(vehicle_B.current_box)

                            is_physical_crush = (iou_score > 0.15) and (real_dist_meters < 2.5) and not (
                                        edge_A or edge_B)

                            # 1. THÊM: Lưu lại danh sách các xe vốn dĩ đang đỗ (Vật thể nền / Hòn đá)
                            background_objs = []
                            if max_v_A < 2.0: background_objs.append(id_A)
                            if max_v_B < 2.0: background_objs.append(id_B)


                            # 2. SỬA: Thêm điều kiện (iou_score > 0.01) để chống báo ảo khi 2 xe không hề chạm nhau
                            # 1. TÍNH IOU MỞ RỘNG (DILATION):
                            # Nới rộng mỗi hộp bao ra 30 pixel để bắt các vụ đâm ngang sườn (IoU bị hụt do góc cam)
                            def get_expanded_box(box, expand=30):
                                return [box[0] - expand, box[1] - expand, box[2] + expand, box[3] + expand]


                            boxA_exp = get_expanded_box(vehicle_A.current_box)
                            boxB_exp = get_expanded_box(vehicle_B.current_box)
                            iou_expanded = calculate_iou(boxA_exp, boxB_exp)

                            # 2. KIỂM TRA ĐÀ CHẠY
                            # Shock: Gia tốc âm sốc và khoảng cách < 5.0m (Bắt cú đâm tâm xe tải 3.4m)
                            # Đồng thời siết chặt: Phải CÓ ĐÀ chạy thực sự (> 5.0) mới được tính là phanh gấp, tránh nhiễu tĩnh.
                            valid_shock_A = (smooth_a_A < thresh_A) and (max_v_A > 5.0)
                            valid_shock_B = (smooth_a_B < thresh_B) and (max_v_B > 5.0)

                            # 3. LUẬT PHẢN ỨNG VẬT LÝ (FLINCH RULE):
                            # Để là một cặp va chạm thực sự, nếu 1 xe bị sốc, xe kia bắt buộc phải là hòn đá (< 2.0)
                            # HOẶC phải có phản ứng vật lý (a_mượt < -3.0 hoặc dV > 4.5).
                            flinch_A = (max_v_A < 2.0) or (smooth_a_A < -3.0) or (delta_v_A > 4.5)
                            flinch_B = (max_v_B < 2.0) or (smooth_a_B < -3.0) or (delta_v_B > 4.5)

                            # 4. CHỐT KÍCH HOẠT:
                            is_kinematic_shock = (real_dist_meters < 5.0) and (iou_expanded > 0.01) and \
                                                 ((valid_shock_A and flinch_B) or (valid_shock_B and flinch_A)) and \
                                                 not (edge_A or edge_B)

                            if is_physical_crush or is_kinematic_shock:
                                crash_cx = (vehicle_A.centroids[-1][0] + vehicle_B.centroids[-1][0]) / 2.0
                                crash_cy = (vehicle_A.centroids[-1][1] + vehicle_B.centroids[-1][1]) / 2.0
                                bev_cx = (bev_A[0] + bev_B[0]) / 2.0
                                bev_cy = (bev_A[1] + bev_B[1]) / 2.0

                                is_new_suspect = True
                                for incident in active_incidents:
                                    if frame_count - incident['frame'] < COOLDOWN_FRAMES:
                                        bev_inc_x, bev_inc_y = incident['bev_centroid']
                                        dist_meters = calculate_real_distance_meters((bev_cx, bev_cy), (bev_inc_x, bev_inc_y), cam_config["pixel_to_meter"])

                                        if dist_meters < SPATIAL_COOLDOWN_METERS:
                                            is_new_suspect = False
                                            break

                                for pending in pending_incidents:
                                    bev_pend_x, bev_pend_y = pending['bev_centroid']
                                    dist_bev_px = math.sqrt((bev_cx - bev_pend_x) ** 2 + (bev_cy - bev_pend_y) ** 2)
                                    dist_meters = calculate_real_distance_meters((bev_cx, bev_cy), (bev_pend_x, bev_pend_y), cam_config["pixel_to_meter"])

                                    if dist_meters < SPATIAL_COOLDOWN_METERS:
                                        is_new_suspect = False
                                        break

                                if is_new_suspect:
                                    reasons_cache = [f"Khoảng cách: {real_dist_meters:.1f}m"]
                                    if is_physical_crush: reasons_cache.append(
                                        f"Giao nhau (IoU: {iou_score:.2f})")
                                    if is_kinematic_shock: reasons_cache.append(
                                        f"Phanh/Văng (aA:{smooth_a_A:.1f}, aB:{smooth_a_B:.1f})")

                                    print(
                                        f"\033[93m[⚠️ SUSPECT] Đưa vào diện tình nghi tại Frame {frame_count}. Chờ 3s kiểm chứng...\033[0m")
                                    pending_incidents.append({
                                        'centroid': (crash_cx, crash_cy),
                                        'bev_centroid': (bev_cx, bev_cy),
                                        'start_frame': frame_count,
                                        'vehicle_types': [vehicle_A.vehicle_type, vehicle_B.vehicle_type],
                                        'ids': [id_A, id_B],
                                        'background_objs': background_objs,
                                        'reasons': reasons_cache
                                    })

                # --- GIAI ĐOẠN 2: KIỂM CHỨNG THEO ĐỐI TƯỢNG VÀ KHÔNG GIAN THỰC (METERS) ---
                VALIDATION_RADIUS_METERS = 6.0  # Quét phạm vi 6 mét để bắt gọn xe trượt văng

                surviving_pending = []
                for pending in pending_incidents:
                    age_frames = frame_count - pending['start_frame']

                    if age_frames < VALIDATION_FRAMES:
                        surviving_pending.append(pending)
                        continue

                    bev_orig_x, bev_orig_y = pending['bev_centroid']
                    stuck_vehicles = 0
                    evidence_logs = []

                    # ĐỌC CẤU HÌNH MẬT ĐỘ ĐƯỜNG TỪ JSON
                    require_stuck = cam_config.get("require_stuck_vehicle", True)

                    for track_id, vehicle in active_trackers.items():
                        if hasattr(vehicle, 'lost_frames') and vehicle.lost_frames > 0:
                            continue

                        v_current = vehicle.velocities[-1] if len(vehicle.velocities) > 0 else 0.0

                        # ĐỌC NGƯỠNG ĐỘNG TỪ FILE JSON CỦA TỪNG CAMERA (Mặc định là 2.0 nếu không cấu hình)
                        max_allowed_v = cam_config.get("validation_max_v", 2.0)

                        if v_current > max_allowed_v:  # Bắt buộc phải bất động (v < 2.0km/h), loại bỏ xe bò rà phanh
                            continue

                        # Đổi khoảng cách trên ảnh sang khoảng cách Mét thực tế
                        curr_bev_x, curr_bev_y = vehicle.centroids_bev[-1]
                        real_dist_meters = calculate_real_distance_meters((curr_bev_x, curr_bev_y), (bev_orig_x, bev_orig_y), cam_config["pixel_to_meter"])

                        if real_dist_meters < VALIDATION_RADIUS_METERS:
                            # NHÁT CẮT 3: TỪ CHỐI NHẬN VƠ
                            # 1. Xe này có phải là 1 trong 2 xe liên quan ban đầu không?
                            is_original_victim = track_id in pending['ids']

                            # 2. THÊM: Xe này có nằm trong danh sách DỪNG ĐỖ từ đầu không?
                            is_background = track_id in pending.get('background_objs', [])

                            # 3. SỬA: CHỈ chấp nhận xe gốc nằm lại VÀ xe đó KHÔNG PHẢI DỪNG ĐỖ
                            if is_original_victim and not is_background:
                                stuck_vehicles += 1
                                evidence_logs.append(
                                    f"ID:{track_id}({vehicle.vehicle_type}) bất động cách {real_dist_meters:.1f}m")

                    # --- QUYẾT ĐỊNH XÁC NHẬN TAI NẠN DỰA TRÊN CẤU HÌNH CAMERA ---
                    is_crash_confirmed = False
                    if not require_stuck:
                        # TRƯỜNG HỢP 1: Camera hẻm
                        # Chỉ cần qua đủ thời gian kiểm chứng 3 giây mà vùng nghi ngờ hợp lệ là chốt luôn!
                        is_crash_confirmed = True
                        evidence_logs.append("Xác nhận tai nạn phương tiện tốc độ cao rời khỏi hiện trường.")
                    else:
                        # TRƯỜNG HỢP 2: Camera đường đông / negative
                        # Bắt buộc hiện trường phải có ít nhất 1 phương tiện bất động/dừng lại
                        if stuck_vehicles >= 1:
                            is_crash_confirmed = True

                    if is_crash_confirmed:
                        cx, cy = pending['centroid']
                        # 1. Lưu tâm BEV vào active_incidents
                        bev_cx, bev_cy = pending['bev_centroid']
                        active_incidents.append({'centroid': (cx, cy), 'bev_centroid': (bev_cx, bev_cy), 'frame': frame_count})
                        # 2. Đánh dấu các ID liên quan là ĐÃ BÁO CÁO
                        for vic_id in pending['ids']:
                            if vic_id in active_trackers:
                                active_trackers[vic_id].is_reported = True
                        last_incident_time = time.time()

                        print("\n" + "=" * 60)
                        print(
                            f"\033[1;31m🚨 [CRASH CONFIRMED] XÁC NHẬN TAI NẠN (TỪ NGHI NGỜ FRAME {pending['start_frame']})! 🚨\033[0m")
                        print(
                            f"📍 Đối tượng ban đầu: {pending['vehicle_types'][0]}(ID:{pending['ids'][0]}) & {pending['vehicle_types'][1]}(ID:{pending['ids'][1]})")
                        print(f"🔍 Bằng chứng khởi phát: {' + '.join(pending['reasons'])}")
                        print(f"🔍 Bằng chứng hiện trường: {stuck_vehicles} nạn nhân.")
                        for log_msg in evidence_logs:
                            print(f"   -> {log_msg}")
                        print("=" * 60 + "\n")

                        # ==================== ĐOẠN CODE MỚI BẮT ĐẦU TỪ ĐÂY ====================

                        # 1. Trích xuất ngay dữ liệu video thô từ băng chuyền quá khứ
                        clip_frames = list(reader.history_buffer)

                        # 2. Tạo Incident ID và Timestamp
                        timestamp = datetime.now(UTC)
                        incident_id = f"INC_{CAMERA_ID}_{frame_count}"

                        vehicles_list = pending.get('vehicle_types', [])
                        vehicles_str = ", ".join(vehicles_list) if vehicles_list else "Chưa xác định"

                        # 3. Tạo Payload cơ sở (CHƯA CÓ URL)

                        base_payload = {
                            "cameraId": cam_config["uuid"],
                            "incidentId": incident_id,
                            "confidence": 0.85,
                            "severity": "HIGH",
                            "description": f"Phát hiện va chạm giữa: {vehicles_str}",
                            "vehiclesInvolved": vehicles_list,
                            "detectedAt": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
                        }

                        # 4. Giao việc cho Cloud Manager xử lý ngầm (Bắn và quên)
                        # Hàm copy() rất quan trọng để tránh frame bị luồng AI vẽ chèn lên trong lúc luồng kia đang upload
                        cloud_manager.process_and_send(
                            frame=frame.copy(),
                            clip_frames=clip_frames,
                            base_payload=base_payload,
                            camera_id=CAMERA_ID,
                            frame_count=frame_count
                        )
                        # =====================================================================
                    else:
                        print(
                            f"\033[92m[✅ FALSE ALARM] Hủy nghi ngờ Frame {pending['start_frame']}. Hiện trường đã giải tỏa.\033[0m")

                pending_incidents = surviving_pending


            # 3. DỌN DẸP BỘ NHỚ AI
            active_incidents = [inc for inc in active_incidents if frame_count - inc['frame'] < COOLDOWN_FRAMES]
            for tid in list(active_trackers.keys()):
                if tid not in current_frame_ids:
                    if not hasattr(active_trackers[tid], 'lost_frames'):
                        active_trackers[tid].lost_frames = 0
                    active_trackers[tid].lost_frames += 1
                    if active_trackers[tid].lost_frames >= 30:
                        del active_trackers[tid]
                else:
                    active_trackers[tid].lost_frames = 0

            # 4. ĐO LƯỜNG VÀ HIỂN THỊ
            # --- DỪNG BẤM GIỜ ---
            frame_process_time = time.perf_counter() - frame_start_time

            # Tính FPS tức thời (Tránh chia cho 0)
            instant_fps = 1.0 / frame_process_time if frame_process_time > 0 else 0.0

            # Làm mượt FPS bằng công thức EMA (giống hệt cách cậu làm với vận tốc)
            if smoothed_fps == 0.0:
                smoothed_fps = instant_fps
            else:
                smoothed_fps = 0.8 * smoothed_fps + 0.2 * instant_fps

            # Ghi dữ liệu ra file CSV để lát nữa mở bằng Excel vẽ biểu đồ
            num_vehicles = len(active_trackers)
            csv_writer.writerow([frame_count, num_vehicles, round(smoothed_fps, 2)])

            # Vẽ thanh trạng thái nền đen phía trên cùng
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), -1)
            cv2.putText(frame, f"AI FPS: {smoothed_fps:.1f} | Frame: {frame_count} | Xe: {num_vehicles}",
                        (15, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # --- CODE THÊM MỚI: KHOANH VÙNG TAI NẠN ---
            # Duyệt qua danh sách các vụ tai nạn đang active và vẽ vòng tròn đỏ tại tâm
            for incident in active_incidents:
                cx, cy = int(incident['centroid'][0]), int(incident['centroid'][1])
                # Vẽ vòng tròn bán kính 60px, độ dày viền 3px, màu Đỏ (0, 0, 255)
                cv2.circle(frame, (cx, cy), 60, (0, 0, 255), 3)
                # Thêm nhãn text ngay cạnh vùng tai nạn
                cv2.putText(frame, "TAI NAN", (cx - 40, cy - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            # ----------------------------------------

            # --- CƠ CHẾ GIỮ CẢNH BÁO TRÊN MÀN HÌNH TRONG 5 GIÂY (CẢNH BÁO SAU ĐÈ CẢNH BÁO TRƯỚC) ---
            if time.time() - last_incident_time < SHOW_ALERT_DURATION:
                # Vẽ một panel đỏ mờ hoặc viền khung chữ cảnh báo nổi bật
                cv2.rectangle(frame, (30, 60), (450, 120), (0, 0, 150), -1)  # Nền đỏ sẫm cho chữ
                cv2.putText(frame, "CANH BAO: TAI NAN!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 255), 3, cv2.LINE_AA)

            cv2.imshow("He Thong Loi AI - Thuc Chien", frame)

            # --- CƠ CHẾ GỠ LỖI (DEBUG MODE) ---
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):  # Bấm 'q' để thoát an toàn
                break
            elif key == ord('p'):  # Bấm 'p' (Pause) để đóng băng thời gian
                print("[DEBUG] Hệ thống tạm dừng. Bấm phím bất kỳ trên bàn phím để chạy tiếp...")
                cv2.waitKey(0)  # Số 0 nghĩa là: Đứng hình vĩnh viễn cho đến khi người dùng gõ phím

    except KeyboardInterrupt:
        print("[HỆ THỐNG] Người dùng cưỡng chế dừng chương trình.")
    finally:
        # Tắt toàn bộ hệ thống an toàn
        reader.stop()
        cv2.destroyAllWindows()
        csv_file.close()
        print("[HỆ THỐNG] Đã tắt luồng an toàn.")