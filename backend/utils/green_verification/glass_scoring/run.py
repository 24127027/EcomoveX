from ultralytics import YOLO
import cv2
from typing import Optional, Dict, List
import numpy as np
import os
import torch  # added for device detection


class CupDetectorScorer:
    """
    Detect cup materials in images using a YOLO model that outputs material classes.
    Processes batches of images efficiently. Glass is weighted as most reliable.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: float = 0.25,
        category_weights: Optional[Dict[str, float]] = None,
        device: Optional[str] = None,  # new optional device param
    ):
        """
        Args:
            model_path: path to YOLO model. Defaults to ../models/glass_classification_model.pt
            conf_threshold: minimum confidence to keep a detection.
            category_weights: per-material weight (higher -> more reliable).
                Example: {"glass": 1.0, "plastic": 0.6, "paper": 0.6}
            device: torch device string, e.g. "cuda:0" or "cpu". If None, auto-selects.
        """
        self.conf_threshold = conf_threshold
        self._model: Optional[YOLO] = None
        # sensible defaults: glass most reliable
        default_weights = {"glass": 1.0, "plastic": 0.6, "paper": 0.6}
        self.category_weights = {k.lower(): float(v) for k, v in (category_weights or default_weights).items()}
        
        # device selection: explicit arg -> CUDA if available -> CPU
        if device:
            self.device = device
        else:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"CupDetectorScorer using device: {self.device}")
        
        # compute default model path if not provided (sibling ../models/)
        if model_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.model_path = os.path.abspath(os.path.join(script_dir, "..", "models", "glass_classification_model.pt"))
        else:
            self.model_path = model_path

        self._load_model()

    def _load_model(self):
        if self._model is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            self._model = YOLO(self.model_path)
            try:
                # ultralytics may accept .to; ignore if not supported
                self._model.to(self.device)
            except Exception:
                pass

    def score_images(self, image_paths: List[str]) -> float:
        """
        Process batch of images and return final normalized score (-10..10).
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            float: Normalized score in range [-10, 10]. 
                   Returns -10 if no cups detected.
                   10 represents all glass cups with high confidence.
                   -10 represents low-quality non-glass cups or no detections.
        """
        # Load and resize images
        images: List[np.ndarray] = []
        for p in image_paths:
            img = cv2.imread(p)
            if img is None:
                raise FileNotFoundError(f"Image not found: {p}")
            images.append(cv2.resize(img, (640, 640)))
        
        if not images:
            return -10.0

        # Detect
        self._load_model()
        imgs_rgb = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB) for img in images]
        # pass device to inference
        results = self._model(imgs_rgb, imgsz=640, conf=self.conf_threshold, device=self.device)

        # Score all detections
        all_scores: List[float] = []
        for res in results:
            for box in res.boxes:
                # Fix deprecation warnings by extracting scalar properly
                conf = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
                cls = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
                class_name = str(self._model.names[cls]) if hasattr(self._model, "names") and cls in self._model.names else str(cls)
                material = class_name.lower()
                
                weight = float(self.category_weights.get(material, 0.5))
                score = min(1.0, conf * weight)  # score in 0..1
                all_scores.append(score)
        
        if not all_scores:
            return -10.0
        
        # Average score 0..1, normalize to -10..10
        avg_score = float(np.mean(all_scores))
        # Map [0, 1] -> [-10, 10]
        normalized = (avg_score * 20.0) - 10.0
        return float(normalized)


# Example usage:
if __name__ == "__main__":
    
    detector = CupDetectorScorer(
        conf_threshold=0.25,
        category_weights={"glass": 1.0, "plastic": -0.4, "paper": 0.6},
    )

    test_image_paths = ["D:/MyML/cup/weights/paper.jpg", "D:/MyML/cup/weights/unnamed.jpg"]
    final_score = detector.score_images(test_image_paths)
    
    print(f"Final Score: {final_score:.2f} (range: -10 to 10)")