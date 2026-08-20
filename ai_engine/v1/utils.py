def log_raw_crash_data(frame_count, id_A, id_B, type_A, type_B, iou_score, real_dist_meters, edge_A, edge_B, v_A, max_v_A, smooth_a_A, v_B, max_v_B, smooth_a_B):
    """
    Hàm debug tạm thời: Đổ toàn bộ data thô ra terminal nếu 2 vật thể cách nhau < 15m.
    """
    if real_dist_meters < 15.0:
        print(f"\n[RAW-DATA] Frame {frame_count} | {type_A}(ID:{id_A}) & {type_B}(ID:{id_B})")
        print(f" -> Không gian: IoU = {iou_score:.4f} | Khoảng cách thực = {real_dist_meters:.2f}m")
        print(f" -> Rìa màn hình: Xe A = {edge_A} | Xe B = {edge_B}")
        print(f" -> ID {id_A}: v = {v_A:.2f} | max_v = {max_v_A:.2f} | a_mượt = {smooth_a_A:.2f}")
        print(f" -> ID {id_B}: v = {v_B:.2f} | max_v = {max_v_B:.2f} | a_mượt = {smooth_a_B:.2f}")