import math

IMG_W = 1920
IMG_H = 1080
TAN_HFOV_HALF = math.tan(math.radians(45.0))  # 90° FOV → tan(45°) = 1.0

def project_drone(drone_pos, cam_pos, fwd, rgt, up):
    v = (drone_pos[0] - cam_pos[0],
         drone_pos[1] - cam_pos[1],
         drone_pos[2] - cam_pos[2])
    depth = v[0]*fwd[0] + v[1]*fwd[1] + v[2]*fwd[2]
    if depth <= 0:
        return None
    r = v[0]*rgt[0] + v[1]*rgt[1] + v[2]*rgt[2]
    u = v[0]*up[0] + v[1]*up[1] + v[2]*up[2]
    norm_x = r / (depth * TAN_HFOV_HALF)
    norm_y = u / (depth * TAN_HFOV_HALF)
    return norm_x, norm_y, depth

def generate_labels(drone_positions, cam_pos, fwd, rgt, up,
                    drone_size_m=0.7, min_bbox_area_px=36):
    labels = []
    for pos in drone_positions:
        result = project_drone(pos, cam_pos, fwd, rgt, up)
        if result is None:
            continue
        norm_x, norm_y, depth = result
        if abs(norm_x) > 1.0 or abs(norm_y) > 1.0:
            continue
        side_px = (drone_size_m / depth) * (IMG_W / 2)
        if side_px * side_px < min_bbox_area_px:
            continue
        cx = (norm_x + 1) / 2
        cy = (1 - norm_y) / 2
        w = side_px / IMG_W
        h = side_px / IMG_H
        labels.append(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    return labels