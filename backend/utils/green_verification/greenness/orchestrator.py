"""
orchestrator.py
---------------

Combines segmentation (TreeSegmenter) and depth (MiDaS via run.process) into a
robust pipeline for computing green coverage and a depth-weighted green score.

Assumptions / notes:
- segmentation.py exposes TreeSegmenter and its method:
    masks_list, combined_mask = TreeSegmenter.process_image(url)
  (masks_list: list of uint8 masks; combined_mask: uint8 mask same HxW)
- run.py exposes function `process(device, model, model_type, image, input_size, target_size, optimize, use_camera)`
  and model_loader provides load_model/default_models.
- utils.load_image_from_url (used here) is the one intended for the depth pipeline.
- We do NOT modify segmentation.py or run.py.
"""

import os
from typing import List, Dict, Any, Optional

import numpy as np
import torch
import cv2

from segmentation import TreeSegmenter
from model_loader import default_models, load_model
import utils
from run import process  # the MiDaS runner function in run.py


class GreenCoverageOrchestrator:
    def __init__(
        self,
        segmentation_model: str = "best.pt",
        depth_model_type: str = "midas_v21_small_256",
        depth_model_path: Optional[str] = None,
        green_threshold: float = 0.3,
        optimize: bool = False,
        height: Optional[int] = None,
        square: bool = False,
    ):
        """
        Initialize orchestrator.

        Args:
            segmentation_model: path to YOLO segmentation weights (used by segmentation.TreeSegmenter)
            depth_model_type: key for default_models (or model name)
            depth_model_path: optional explicit path to depth model file (.pt)
            green_threshold: threshold on final green_score to mark verified
            optimize: pass to load_model/processing for MiDaS optimization
            height, square: passed to load_model (MiDaS loader options)
        """
        self.green_threshold = float(green_threshold)

        # Segmentation (YOLO)
        print(f"[orchestrator] Loading segmentation model: {segmentation_model}")
        self.tree_segmenter = TreeSegmenter(segmentation_model)

        # Depth model path resolution
        if depth_model_path is None:
            depth_model_path = self._find_model_path(depth_model_type)

        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[orchestrator] Using device: {self.device}")

        # Load depth model (MiDaS style). load_model returns (model, transform, net_w, net_h)
        self.depth_model, self.depth_transform, self.net_w, self.net_h = load_model(
            self.device, depth_model_path, depth_model_type, optimize, height, square
        )
        self.depth_model_type = depth_model_type
        self.optimize = optimize

        print("[orchestrator] Initialization complete.")

    def _find_model_path(self, model_type: str) -> str:
        """
        Find an existing depth model path using several fallbacks.

        Returns:
            path to .pt model

        Raises:
            FileNotFoundError if cannot find.
        """
        # possible fallbacks
        cwd = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            default_models.get(
                model_type, ""
            ),  # official default from model_loader (may be "")
            os.path.join(cwd, f"{model_type}.pt"),
            os.path.join(cwd, "midas_v21_small_256.pt"),
            os.path.join(cwd, "best.pt"),
            os.path.join(cwd, "weights", f"{model_type}.pt"),
            os.path.join(os.path.dirname(cwd), "weights", f"{model_type}.pt"),
        ]

        # filter empties and check
        for p in candidates:
            if not p:
                continue
            if os.path.exists(p):
                print(f"[orchestrator] Found depth model: {p}")
                return p

        # print useful help
        print(
            f"[orchestrator] Could not locate a depth model for '{model_type}'. Checked:"
        )
        for p in candidates:
            if p:
                print(f"  - {p}")
        # list .pt files in cwd for debugging
        try:
            files = [f for f in os.listdir(cwd) if f.endswith(".pt")]
            if files:
                print(f"[orchestrator] .pt files in {cwd}: {files}")
        except Exception:
            pass

        raise FileNotFoundError(
            f"Depth model for '{model_type}' not found. Please provide depth_model_path or place model in checked locations."
        )

    def _get_depth_map(self, image_rgb: np.ndarray) -> np.ndarray:
        """
        Compute depth map for a single RGB image (image_rgb expected in format used by run.py's transform).
        Returns a 2D np.float32 array with same HxW as the original image (before any normalization).
        """
        # Transform image using MiDaS transform (this transform is expected by run.process)
        # NOTE: transform returns dict e.g. {"image": transformed_tensor_or_np}
        transformed = self.depth_transform({"image": image_rgb})["image"]

        with torch.no_grad():
            prediction = process(
                self.device,
                self.depth_model,
                self.depth_model_type,
                transformed,
                (self.net_w, self.net_h),
                image_rgb.shape[1::-1],  # target_size as (width, height)
                self.optimize,
                False,
            )

        # ensure float32 numpy
        return prediction.astype(np.float32)

    @staticmethod
    def _normalize_depth_map(depth: np.ndarray) -> np.ndarray:
        """
        Normalize depth map to [0,1]. If depth is constant, returns zeros.
        """
        d_min = float(np.nanmin(depth))
        d_max = float(np.nanmax(depth))
        if np.isfinite(d_min) and np.isfinite(d_max) and (d_max - d_min) > 1e-8:
            return (depth - d_min) / (d_max - d_min)
        else:
            return np.zeros_like(depth, dtype=np.float32)

    def process_single_image(self, url: str) -> Dict[str, Any]:
        """
        Process one image URL:
            - get segmentation (masks_list, combined_mask) from TreeSegmenter
            - get depth map from MiDaS (via run.process)
            - resize depth map to mask size (if needed)
            - compute green proportion and depth-weighted score
        Returns a dict with keys:
            url, combined_mask (uint8 HxW), individual_masks (list of uint8), depth (float32 HxW),
            green_proportion, depth_weighted, green_score, verified, (optional) error
        """
        try:
            # 1) Depth: load image using utils.load_image_from_url (this is the run.py-compatible loader)
            original_image_rgb = utils.load_image_from_url(
                url
            )  # expected RGB float32 in [0,1] as run.py expects

            # 2) Segmentation: call TreeSegmenter.process_image(url) ONCE (TreeSegmenter will fetch its own image)
            #    returns: masks_list, combined_mask
            masks_list, combined_mask = self.tree_segmenter.process_image(url)
            individual_masks = masks_list  # rename for clarity

            # Validate combined_mask
            if combined_mask is None or combined_mask.size == 0:
                # No vegetation detected: return zeroed stats (but keep depth map if possible)
                depth_map = self._get_depth_map(original_image_rgb)
                # Resize depth to a small default if mask is empty? Keep original depth shape.
                return {
                    "url": url,
                    "combined_mask": (
                        combined_mask
                        if combined_mask is not None
                        else np.array([], dtype=np.uint8)
                    ),
                    "individual_masks": individual_masks,
                    "depth": depth_map,
                    "green_proportion": 0.0,
                    "depth_weighted": 0.0,
                    "green_score": 0.0,
                    "verified": False,
                }

            # 3) Depth map (MiDaS)
            depth_map = self._get_depth_map(
                original_image_rgb
            )  # float32 HxW (target: original_image_rgb.shape[:2])

            # 4) Ensure shapes match: resize depth_map to mask shape if needed
            mask_h, mask_w = combined_mask.shape[:2]
            if depth_map.shape[:2] != (mask_h, mask_w):
                # resize depth to mask size (depth is float32)
                depth_map_resized = cv2.resize(
                    depth_map, (mask_w, mask_h), interpolation=cv2.INTER_CUBIC
                )
            else:
                depth_map_resized = depth_map

            # 5) Compute green proportion
            total_pixels = combined_mask.size
            green_pixels = int(np.count_nonzero(combined_mask > 0))
            green_proportion = (
                float(green_pixels) / float(total_pixels) if total_pixels > 0 else 0.0
            )

            # 6) Compute depth-weighted value:
            if green_pixels > 0:
                mask_bool = combined_mask > 0
                veg_depth_values = depth_map_resized[mask_bool]

                # Normalize depth to [0,1] over the full map (consistent scale)
                depth_norm_full = self._normalize_depth_map(depth_map_resized)

                # get the normalized depths where vegetation is present
                veg_depth_norm = depth_norm_full[mask_bool]

                # Interpretation choice:
                #   - depth_norm ~ 0 -> closest (smallest depth value)
                #   - depth_norm ~ 1 -> farthest (largest depth value)
                # We want green closer to camera to be scored higher (common for green verification from photos),
                # so compute depth_weighted = 1 - mean(veg_depth_norm)
                # If you want to prefer farther vegetation, flip this behavior.
                depth_weighted = float(1.0 - np.clip(np.mean(veg_depth_norm), 0.0, 1.0))
            else:
                depth_weighted = 0.0

            # 7) Final green score
            green_score = float(green_proportion * depth_weighted)
            verified = bool(green_score >= self.green_threshold)

            return {
                "url": url,
                "combined_mask": combined_mask,
                "individual_masks": individual_masks,
                "depth": depth_map_resized,
                "green_proportion": float(green_proportion),
                "depth_weighted": float(depth_weighted),
                "green_score": float(green_score),
                "verified": verified,
            }

        except Exception as exc:
            # Return an error payload instead of raising so a batch run can continue.
            print(f"[orchestrator] Error processing {url}: {exc}")
            return {
                "url": url,
                "combined_mask": np.array([], dtype=np.uint8),
                "individual_masks": [],
                "depth": np.array([], dtype=np.float32),
                "green_proportion": 0.0,
                "depth_weighted": 0.0,
                "green_score": 0.0,
                "verified": False,
                "error": str(exc),
            }

    def process_image_list(self, image_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Process a list of image URLs (serially). Returns list of result dicts.
        """
        results: List[Dict[str, Any]] = []
        print(f"[orchestrator] Processing {len(image_urls)} images...")
        for i, url in enumerate(image_urls, start=1):
            print(f"[orchestrator] ({i}/{len(image_urls)}) -> {url}")
            res = self.process_single_image(url)
            results.append(res)
        print("[orchestrator] Done.")
        return results

    def get_summary_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute aggregate statistics for a list of results.
        """
        valid_results = [r for r in results if "error" not in r]
        total_images = len(results)
        valid_images = len(valid_results)
        if valid_images == 0:
            return {
                "total_images": total_images,
                "valid_images": 0,
                "verified_images": 0,
                "average_green_proportion": 0.0,
                "average_green_score": 0.0,
                "verification_rate": 0.0,
            }

        avg_green_prop = float(np.mean([r["green_proportion"] for r in valid_results]))
        avg_green_score = float(np.mean([r["green_score"] for r in valid_results]))
        verified_count = sum(1 for r in valid_results if r.get("verified", False))
        verification_rate = (
            float(verified_count) / float(valid_images) if valid_images > 0 else 0.0
        )

        return {
            "total_images": total_images,
            "valid_images": valid_images,
            "verified_images": verified_count,
            "average_green_proportion": avg_green_prop,
            "average_green_score": avg_green_score,
            "verification_rate": verification_rate,
        }


if __name__ == "__main__":
    # Simple demo usage. Edit URLs and model names as needed.
    demo_urls = [
        # put your test image URLs here
        "https://lh3.googleusercontent.com/gps-cs-s/AG0ilSzMja-cKxl1dNoPaSKLzLLTvNrCsLblTsd3mVZgwZEdxO7gi5CSU0yp6MDc6hG8OiFTB9U_XRM-72uZSNj5leBO-ulnbiwIFP5MQP3SqeyYo7RD6ygj06WYZoFyrsHnXDo_zmruDw=w203-h270-k-no"
    ]

    try:
        orchestrator = GreenCoverageOrchestrator(
            segmentation_model="best.pt",
            depth_model_type="midas_v21_small_256",
            depth_model_path=None,
            green_threshold=0.3,
            optimize=True,
        )

        results = orchestrator.process_image_list(demo_urls)
        for r in results:
            print(f"\nResult for {r['url']}:")
            if "error" in r:
                print("  Error:", r["error"])
                continue
            print(f"  Green proportion: {r['green_proportion']:.4f}")
            print(f"  Depth weighted: {r['depth_weighted']:.4f}")
            print(f"  Green score: {r['green_score']:.4f}")
            print(f"  Verified: {r['verified']}")

        summary = orchestrator.get_summary_stats(results)
        print("\nSummary:", summary)

    except Exception as e:
        print("[orchestrator] Fatal error initializing orchestrator:", str(e))
        print("Make sure depth model files exist or pass depth_model_path explicitly.")
