import os
import cv2
import numpy as np
from ultralytics import YOLO
from utils import load_image_from_url  # your existing function

class TreeSegmenter:
    def __init__(self, model_name="best.pt"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, model_name)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")

        print(f"Loading Segmentation Model from: {model_path}")
        self.model = YOLO(model_path)

    def process_image(self, url: str):
        """
        URL-only segmentation.
        Loads RGB float32 from URL → Convert to uint8 BGR → YOLO → Mask.
        """

        # 1. Load RGB float32 in [0,1] using your function
        img_rgb = load_image_from_url(url)

        # 2. Convert to uint8 BGR for YOLO
        img_bgr = (img_rgb * 255).astype(np.uint8)
        img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_RGB2BGR)

        h, w = img_bgr.shape[:2]

        # 3. YOLO segmentation
        results = self.model.predict(
            img_bgr, 
            retina_masks=True, 
            conf=0.1, 
            verbose=False
        )[0]

        # 4. Combine masks
        combined_mask = np.zeros((h, w), dtype=np.uint8)

        if results.masks is not None:
            raw_masks = results.masks.data.cpu().numpy()
            for m in raw_masks:
                m_resized = cv2.resize(m, (w, h))
                combined_mask = np.maximum(
                    combined_mask,
                    (m_resized * 255).astype(np.uint8)
                )

        # 5. masked image (optional)
        masked_img = cv2.bitwise_and(img_bgr, img_bgr, mask=combined_mask)

        return combined_mask, masked_img
