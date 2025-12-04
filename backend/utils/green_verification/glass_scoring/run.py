### cupdetection.py
import os
from typing import Dict, List, Optional, Any
import numpy as np
import torch
from ultralytics import YOLO

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

        # Trọng số các loại (nếu cần tính điểm sau này)
        default_weights = {"glass": 1.0, "plastic": 0.6, "paper": 0.6}
        self.category_weights = {
            k.lower(): float(v) for k, v in (category_weights or default_weights).items()
        }

        if device:
            self.device = device
        else:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        print(f"[CupDetector] Using device: {self.device}")

        # Xử lý đường dẫn model
        if model_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Giả định model nằm ở thư mục cha/models, hoặc bạn có thể trỏ thẳng file
            self.model_path = os.path.join(script_dir, "glass_classification_model.pt") 
            if not os.path.exists(self.model_path):
                 # Fallback: tìm ngay tại thư mục hiện tại
                 self.model_path = os.path.join(script_dir, "best.pt") # Ví dụ tên model
        else:
            self.model_path = model_path

        self._load_model()

    def _load_model(self):
        if self._model is None:
            if not os.path.exists(self.model_path):
                # Chỉ cảnh báo, để orchestrator không bị crash nếu thiếu model
                print(f"[CupDetector] Warning: Model file not found at {self.model_path}")
                return
            
            print(f"[CupDetector] Loading model from {self.model_path}")
            self._model = YOLO(self.model_path)
            try:
                self._model.to(self.device)
            except Exception as e:
                print(f"[CupDetector] Error moving to device: {e}")

    def detect(self, img_rgb: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect cups/glasses and return normalized coordinates.
        img_rgb: Numpy array (H, W, 3) - uint8 or float.
        """
        # Chạy inference
        self._load_model()
        if self._model is None:
            return []

        H, W = img_rgb.shape[:2]
        
        # --- DEBUG: In ra thông tin ảnh đầu vào ---
        print(f"[CupDetector] Input shape: {img_rgb.shape}, Max Val: {img_rgb.max()}, Min Val: {img_rgb.min()}")

        # --- THAY ĐỔI Ở ĐÂY ---
        # 1. Giảm conf xuống 0.05 hoặc 0.1 để bắt nhạy hơn
        # 2. Bật verbose=True để xem log của YOLO
        results = self._model(
            img_rgb, 
            imgsz=640, 
            conf=0.25,    # <--- Giảm xuống 0.1 (10%)
            device=self.device, 
            verbose=False # <--- Bật lên để xem log
        )

        detections = []

        for res in results:
            boxes = res.boxes
            for box in boxes:
                # Lấy thông tin cơ bản
                conf = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
                cls_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
                
                class_name = (
                    str(self._model.names[cls_id])
                    if hasattr(self._model, "names") and cls_id in self._model.names
                    else str(cls_id)
                )

                # Lấy tọa độ xyxy (pixel)
                xyxy = box.xyxy.cpu().numpy()[0] # [x1, y1, x2, y2]
                x1, y1, x2, y2 = xyxy

                # Tính tâm (centroid)
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                # --- NORMALIZE POINTS (Yêu cầu quan trọng) ---
                # Giá trị từ 0.0 đến 1.0
                norm_x = center_x / W
                norm_y = center_y / H
                
                # Normalize bounding box (nếu cần dùng xywh normalized)
                norm_w = (x2 - x1) / W
                norm_h = (y2 - y1) / H

                detection_info = {
                    "label": class_name,
                    "confidence": conf,
                    "bbox_pixel": [float(x1), float(y1), float(x2), float(y2)],
                    "centroid_pixel": [float(center_x), float(center_y)],
                    "normalized_point": [float(norm_x), float(norm_y)], # ĐÂY LÀ ĐIỂM BẠN CẦN
                    "normalized_bbox": [float(norm_x), float(norm_y), float(norm_w), float(norm_h)] # xywh format
                }
                detections.append(detection_info)

        return detections