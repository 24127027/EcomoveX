from ultralytics import YOLO
import cv2
from typing import Optional, Dict, List
import numpy as np
import os

class CupDetectorScorer:
    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: float = 0.25,
        category_weights: Optional[Dict[str, float]] = None,
    ):
        self.conf_threshold = conf_threshold
        self._model: Optional[YOLO] = None

        default_weights = {"glass": 1.0, "plastic": 0.6, "paper": 0.6}
        self.category_weights = {k.lower(): float(v) for k, v in (category_weights or default_weights).items()}
        
        if model_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.model_path = os.path.join(script_dir, "glass_classification_model.pt")
        else:
            self.model_path = model_path
        self._load_model()

    def _load_model(self):
        if self._model is None:
            self._model = YOLO(self.model_path)

    def score_images(self, image_paths: List[str]) -> float:
        images: List[np.ndarray] = []
        for p in image_paths:
            img = cv2.imread(p)
            if img is None:
                raise FileNotFoundError(f"Image not found: {p}")
            images.append(cv2.resize(img, (640, 640)))
        
        if not images:
            return -10.0

        self._load_model()
        imgs_rgb = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB) for img in images]
        results = self._model(imgs_rgb, imgsz=640, conf=self.conf_threshold)

        all_scores: List[float] = []
        for res in results:
            for box in res.boxes:

                conf = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
                cls = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
                class_name = str(self._model.names[cls]) if hasattr(self._model, "names") and cls in self._model.names else str(cls)
                material = class_name.lower()
                
                weight = float(self.category_weights.get(material, 0.5))
                score = min(1.0, conf * weight)
                all_scores.append(score)
        
        if not all_scores:
            return -10.0
        
        avg_score = float(np.mean(all_scores))

        normalized = (avg_score * 20.0) - 10.0
        return float(normalized)