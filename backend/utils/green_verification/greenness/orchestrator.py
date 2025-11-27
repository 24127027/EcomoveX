import numpy as np
from segmentation import TreeSegmenter
from depth import DepthEstimator

def compute_green_score(image, depth_map, mask):
    # 1. % diện tích xanh
    green_count = np.sum(mask > 0)
    total = mask.size
    area_ratio = green_count / total

    # Nếu không tìm thấy cây, trả về 0 ngay
    if green_count == 0:
        return 0.0

    # 2. Độ phức tạp chiều sâu trong vùng cây
    depth_vals = depth_map[mask > 0]
    
    # Chuẩn hóa depth về 0-1 để tính variance chính xác hơn
    min_d, max_d = depth_vals.min(), depth_vals.max()
    if max_d - min_d == 0:
        depth_norm = np.zeros_like(depth_vals)
    else:
        depth_norm = (depth_vals - min_d) / (max_d - min_d)
    
    depth_variance = float(np.var(depth_norm))

    # Công thức: Bạn có thể điều chỉnh trọng số (weight)
    score = 0.6 * area_ratio + 0.4 * depth_variance
    return round(score, 4)

def run_green_verification_pipeline(image_path, model_path="yolov11x-seg.pt"):
    
    print(f"--- Processing: {image_path} ---")
    
    print(f"🚀 Starting Green Verification for: {image_path}")
    print(f"🔮 Using Model: {model_path}")
    # 1. SEGMENTATION
    segmenter = TreeSegmenter(model_name=model_path) # Sẽ tự tìm model yolov11x-seg.pt
    mask, tree_img = segmenter.process_image(image_path)

    if tree_img is None or np.sum(mask) == 0:
        print("No tree detected.")
        return None

    # 2. DEPTH ESTIMATION
    # Lưu ý: MiDaS hoạt động tốt hơn trên ảnh đầy đủ, 
    # nhưng để tập trung vào cây, ta có thể đưa ảnh đã tách nền (nền đen/xám) vào.
    # Tuy nhiên, tốt nhất là đưa ảnh gốc vào để lấy depth, sau đó mới crop theo mask.
    
    # Cách tối ưu: Tính depth trên toàn ảnh gốc để có ngữ cảnh đúng, sau đó mới mask vùng cây.
    # Nhưng theo code cũ của bạn là đưa `tree_img` (đã mask) vào. Mình sẽ giữ logic đó nhưng fix nền xám.
    
    img_for_depth = tree_img.copy()
    img_for_depth[mask == 0] = 128 # Nền xám trung tính giúp depth ổn định hơn nền đen tuyệt đối

    depth_estimator = DepthEstimator(model_type="DPT_Hybrid") # Dùng Hybrid cho cân bằng tốc độ/chất lượng
    depth_map = depth_estimator.get_depth_map(img_for_depth)

    # 3. GREENNESS SCORE
    score = compute_green_score(tree_img, depth_map, mask)

    print(f"Pipeline complete — Score: {score}")
    return {
        "mask": mask,
        "tree": tree_img,
        "depth": depth_map,
        "score": score
    }