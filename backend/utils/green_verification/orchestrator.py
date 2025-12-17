import os
import sys
from typing import List, Dict, Any, Optional

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
# 2. LAZY LOADING - Prevent heavy ML imports at module load time
# ==============================================================================
_modules_loaded = False

def _lazy_load_modules():
    """Load heavy ML dependencies only when needed"""
    global _modules_loaded
    if _modules_loaded:
        return

    try:
        # Import heavy dependencies here
        import numpy  # noqa
        import torch  # noqa
        import cv2  # noqa
        _modules_loaded = True
    except ImportError as e:
        print(f"[Import Error] Core ML libraries: {e}")
        raise

class GreenCoverageOrchestrator:
    _instance = None
    _models_loaded = False

    @classmethod
    def get_instance(cls):
        """Singleton pattern with lazy initialization"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(
        self,
        segmentation_model: str = "best.pt",
        cup_model_name: str = "glass_classification_model.pt",
        green_threshold: float = 0.15,
        optimize: bool = False,
        height: Optional[int] = None,
        square: bool = False,
    ):
        # Store configuration but don't load models yet
        self.green_threshold = float(green_threshold)
        self.segmentation_model = segmentation_model
        self.cup_model_name = cup_model_name
        self.depth_optimize = optimize
        self.depth_height = height
        self.depth_square = square

        # Models will be loaded on first use
        self.tree_segmenter = None
        self.cup_detector = None
        self.device = None

    def _ensure_models_loaded(self):
        """Load models only when actually needed"""
        if self._models_loaded:
            return

        print("[Orchestrator] Loading ML models for the first time...")

        # Lazy load heavy dependencies
        _lazy_load_modules()

        # Import here to avoid loading at module import time
        import torch
        from .greenness.segmentation import TreeSegmenter

        try:
            from glass_scoring.run import CupDetectorScorer
        except ImportError:
            CupDetectorScorer = None

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[Orchestrator] Device: {self.device}")

        # --- 1. Init Tree Segmenter ---
        seg_model_path = os.path.join(models_dir, self.segmentation_model)
        print(f"[Orchestrator] Loading Tree model: {seg_model_path}")
        self.tree_segmenter = TreeSegmenter(seg_model_path)

        # --- 2. Init Cup Detector ---
        if CupDetectorScorer:
            cup_model_path = os.path.join(models_dir, self.cup_model_name)
            print(f"[Orchestrator] Loading Cup model: {cup_model_path}")
            self.cup_detector = CupDetectorScorer(
                model_path=cup_model_path,
                device=str(self.device)
            )
        else:
            self.cup_detector = None

        self._models_loaded = True
        print("[Orchestrator] Models loaded and ready.")

    def _get_depth_map(self, url: str):
        """
        Use depth.run() which handles everything internally.
        Returns depth map for a single image URL.
        """
        from .greenness import depth

        # depth.run() takes a list of URLs and returns list of depth maps
        results = depth.run(
            img_sources=[url],
            optimize=self.depth_optimize,
            height=self.depth_height,
            square=self.depth_square,
            grayscale=False
        )

        # Return the first (and only) result
        return results[0]

    @staticmethod
    def _normalize_depth_map(depth):
        import numpy as np
        d_min = float(np.nanmin(depth))
        d_max = float(np.nanmax(depth))
        if np.isfinite(d_min) and np.isfinite(d_max) and (d_max - d_min) > 1e-8:
            return (depth - d_min) / (d_max - d_min)
        else:
            return np.zeros_like(depth, dtype=np.float32)

    def process_single_image(self, url: str) -> Dict[str, Any]:
        # Ensure models are loaded before processing
        self._ensure_models_loaded()

        try:
            import numpy as np
            import cv2
            from .greenness import utils

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

            # Tính Depth using midas.run()
            depth_map = self._get_depth_map(url)

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

            # Scale green proportion để range đẹp hơn
            gp_norm = min(green_proportion * 3.0, 1.0)

            # Depth weighting mềm hơn
            dw_norm = depth_weighted ** 0.8

            green_score = gp_norm * dw_norm
            #check if plastic appears in the image
            if any(cup.get("material") == "plastic" for cup in cup_detections):
                green_score *= 0.7

            verified = bool(green_score >= self.green_threshold)

            return {
                "url": url,
                "green_score": green_score
            }

        except Exception as e:
            print(f"[Orchestrator] Error on {url}: {e}")
            import traceback
            traceback.print_exc()
            return {"url": url, "error": str(e), "verified": False}

    def process_image_list(self, urls: List[str]) -> Dict[str, Any]:
        # Ensure models are loaded before processing
        self._ensure_models_loaded()

        import numpy as np
        scores = []
        for url in urls:
            res = self.process_single_image(url)
            scores.append(res["green_score"])

        total_score = float(np.mean(scores)) if scores else 0.0

        return {
            "total_score": total_score,
            "verified": total_score >= self.green_threshold
        }

