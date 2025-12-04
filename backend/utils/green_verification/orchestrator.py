import os
import sys
from typing import List, Dict, Any, Optional
import numpy as np
import torch
import cv2

# ==============================================================================
# 1. PATH CONFIGURATION
# ==============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(current_dir, "models")

# Thêm greenness vào sys.path để tránh lỗi ModuleNotFoundError: 'dpt_depth'
greenness_dir = os.path.join(current_dir, "greenness")
if greenness_dir not in sys.path:
    sys.path.append(greenness_dir)

# Thêm glass_scoring vào sys.path
glass_dir = os.path.join(current_dir, "glass_scoring")
if glass_dir not in sys.path:
    sys.path.append(glass_dir)

# ==============================================================================
# 2. IMPORTS
# ==============================================================================
try:
    from greenness import utils
    from greenness.segmentation import TreeSegmenter
    from greenness.model_loader import load_model, default_models
    from greenness.run import process as midas_process 
except ImportError as e:
    print(f"[Import Error] Greenness modules: {e}")
    sys.exit(1)

try:
    from glass_scoring.run import CupDetectorScorer
except ImportError as e:
    print(f"[Import Error] Glass scoring modules: {e}")
    # Cho phép chạy tiếp nếu không có module này (để debug phần khác), hoặc exit
    CupDetectorScorer = None

class GreenCoverageOrchestrator:
    def __init__(
        self,
        segmentation_model: str = "best.pt",
        cup_model_name: str = "glass_classification_model.pt",
        depth_model_type: str = "midas_v21_small_256",
        depth_model_path: Optional[str] = None,
        green_threshold: float = 0.3,
        optimize: bool = False,
        height: Optional[int] = None,
        square: bool = False,
    ):
        self.green_threshold = float(green_threshold)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[Orchestrator] Device: {self.device}")

        # --- 1. Init Tree Segmenter ---
        seg_model_path = os.path.join(models_dir, segmentation_model)
        print(f"[Orchestrator] Loading Tree model: {seg_model_path}")
        self.tree_segmenter = TreeSegmenter(seg_model_path)

        # --- 2. Init Cup Detector ---
        if CupDetectorScorer:
            cup_model_path = os.path.join(models_dir, cup_model_name)
            print(f"[Orchestrator] Loading Cup model: {cup_model_path}")
            self.cup_detector = CupDetectorScorer(
                model_path=cup_model_path,
                device=str(self.device)
            )
        else:
            self.cup_detector = None

        # --- 3. Init Depth Model (MiDaS) ---
        if depth_model_path is None:
            check_path = os.path.join(models_dir, f"{depth_model_type}.pt")
            if os.path.exists(check_path):
                depth_model_path = check_path
            else:
                depth_model_path = self._find_model_path(depth_model_type)

        print(f"[Orchestrator] Loading Depth model: {depth_model_path}")
        self.depth_model, self.depth_transform, self.net_w, self.net_h = load_model(
            self.device, depth_model_path, depth_model_type, optimize, height, square
        )
        self.depth_model_type = depth_model_type
        self.optimize = optimize

        print("[Orchestrator] Ready.")

    def _find_model_path(self, model_type: str) -> str:
        candidates = [
            default_models.get(model_type, ""),
            os.path.join(models_dir, f"{model_type}.pt"),
            os.path.join(current_dir, f"{model_type}.pt"),
        ]
        for p in candidates:
            if p and os.path.exists(p):
                return p
        raise FileNotFoundError(f"Depth model '{model_type}' not found.")

    def _get_depth_map(self, image_rgb: np.ndarray) -> np.ndarray:
        """
        FIXED: Gọi hàm process đúng với chữ ký trong run.py của bạn:
        def process(device, model, image, target_size, optimize, use_camera):
        """
        # Transform image for MiDaS
        transformed = self.depth_transform({"image": image_rgb})["image"]
        
        # Target size (Width, Height)
        target_size = image_rgb.shape[1::-1]

        with torch.no_grad():
            prediction = midas_process(
                self.device,        # 1. device
                self.depth_model,   # 2. model
                transformed,        # 3. image
                target_size,        # 4. target_size
                self.optimize,      # 5. optimize
                False               # 6. use_camera
            )
            
        return prediction.astype(np.float32)

    @staticmethod
    def _normalize_depth_map(depth: np.ndarray) -> np.ndarray:
        d_min = float(np.nanmin(depth))
        d_max = float(np.nanmax(depth))
        if np.isfinite(d_min) and np.isfinite(d_max) and (d_max - d_min) > 1e-8:
            return (depth - d_min) / (d_max - d_min)
        else:
            return np.zeros_like(depth, dtype=np.float32)

    def process_single_image(self, url: str) -> Dict[str, Any]:
        try:
            # 1. Load Image (Float32 RGB [0,1])
            original_image_float = utils.load_image_from_url(url)
            
            # Convert sang Uint8 [0,255] cho Cup Detector
            original_image_uint8 = (original_image_float * 255).astype(np.uint8)

            # 2. Cup Detection
            cup_detections = []
            if self.cup_detector:
                cup_detections = self.cup_detector.detect(original_image_uint8)

            # 3. Tree Segmentation
            masks_list, combined_mask = self.tree_segmenter.process_image(url)

            # 4. Logic Depth & Green Score
            # Nếu không có cây -> Score 0
            if combined_mask is None or combined_mask.size == 0:
                return {
                    "url": url,
                    "combined_mask": [],
                    "green_score": 0.0,
                    "verified": False,
                    "cup_detections": cup_detections
                }

            # Tính Depth (đã fix lỗi argument)
            depth_map = self._get_depth_map(original_image_float)
            
            # Resize depth khớp mask
            mask_h, mask_w = combined_mask.shape[:2]
            if depth_map.shape[:2] != (mask_h, mask_w):
                depth_map_resized = cv2.resize(depth_map, (mask_w, mask_h), interpolation=cv2.INTER_CUBIC)
            else:
                depth_map_resized = depth_map

            # Tính điểm
            total_pixels = combined_mask.size
            green_pixels = int(np.count_nonzero(combined_mask > 0))
            green_proportion = float(green_pixels) / float(total_pixels) if total_pixels > 0 else 0.0

            depth_weighted = 0.0
            if green_pixels > 0:
                mask_bool = combined_mask > 0
                depth_norm_full = self._normalize_depth_map(depth_map_resized)
                veg_depth_norm = depth_norm_full[mask_bool]
                depth_weighted = float(1.0 - np.clip(np.mean(veg_depth_norm), 0.0, 1.0))

            green_score = float(green_proportion * depth_weighted)
            verified = bool(green_score >= self.green_threshold)

            return {
                "url": url,
                "combined_mask": combined_mask,
                "green_proportion": green_proportion,
                "green_score": green_score,
                "verified": verified,
                "cup_detections": cup_detections
            }

        except Exception as e:
            print(f"[Orchestrator] Error on {url}: {e}")
            import traceback
            traceback.print_exc()
            return {"url": url, "error": str(e), "verified": False}

    def process_image_list(self, image_urls: List[str]) -> List[Dict[str, Any]]:
        results = []
        for url in image_urls:
            res = self.process_single_image(url)
            results.append(res)
        return results

# if __name__ == "__main__":
#     # Test
#     test_urls = ["https://lh3.googleusercontent.com/p/AF1QipOPePZD8_itqgm0X-nRoQFKGDlmKnMXtIdGUvzb=w203-h304-k-no"]
    
#     orch = GreenCoverageOrchestrator(
#         segmentation_model="best.pt",
#         cup_model_name="glass_classification_model.pt",
#         depth_model_type="midas_v21_small_256"
#     )
    
#     data = orch.process_image_list(test_urls)
#     for item in data:
#         print(f"\nURL: {item['url']}")
#         if "error" in item:
#             print(f"Error: {item['error']}")
#         else:
#             print(f"Green Score: {item['green_score']:.4f}")
#             print(f"Cup Detections: {item['cup_detections']}")