import os
from typing import Dict, List, Optional
import cv2
import numpy as np
from ultralytics import YOLO
<<<<<<< HEAD
=======
import torch 
import os
import torch  
>>>>>>> 923206a92cf1a4319ea60d3910058a727435bc2e

class CupDetectorScorer:
    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: float = 0.25,
        category_weights: Optional[Dict[str, float]] = None,
        device: Optional[str] = None,
    ):
        self.conf_threshold = conf_threshold
        self._model: Optional[YOLO] = None

        default_weights = {"glass": 1.0, "plastic": 0.6, "paper": 0.6}
        self.category_weights = {k.lower(): float(v) for k, v in (category_weights or default_weights).items()}
        
<<<<<<< HEAD
=======
        if device:
            self.device = device
        else:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"CupDetectorScorer using device: {self.device}")
        
>>>>>>> 923206a92cf1a4319ea60d3910058a727435bc2e
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
                self._model.to(self.device)
            except Exception:
                pass

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

        results = self._model(imgs_rgb, imgsz=640, conf=self.conf_threshold, device=self.device)

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