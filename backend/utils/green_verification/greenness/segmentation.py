import cv2
import numpy as np
import requests
from ultralytics import YOLO


class TreeSegmenter:
    def __init__(self, model_name="best.pt", target_min=512):
        print(f"Loading Segmentation Model: {model_name}")
        self.model = YOLO(model_name)
        self.target_min = target_min

    # --------------------------
    # 1. LOAD IMAGE (BGR uint8)
    # --------------------------
    def load_image_from_url(self, url: str):
        resp = requests.get(url)
        data = np.frombuffer(resp.content, np.uint8)
        img_bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)

        if img_bgr is None:
            raise Exception(f"Failed to decode image: {url}")

        return img_bgr  # BGR uint8

    # --------------------------
    # 2. UPSCALE
    # --------------------------
    def upscale(self, img):
        h, w = img.shape[:2]
        scale = max(self.target_min / h, self.target_min / w)
        new_w = int(w * scale)
        new_h = int(h * scale)

        img_up = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        return img_up

    # --------------------------
    # 3. PROCESS
    # --------------------------
    def process_image(self, url: str):
        """
        Input:
            - url: image URL

        Output:
            - masks_list: list of mask np.ndarray (uint8)
            - combined_mask: union of all masks
        """

        # Load and upscale
        img = self.load_image_from_url(url)
        img_up = self.upscale(img)

        H, W = img_up.shape[:2]

        # YOLO segmentation
        result = self.model(
            img_up,
            conf=0.1,
            retina_masks=True,
            verbose=False
        )[0]

        # Prepare outputs
        masks_list = []
        combined_mask = np.zeros((H, W), dtype=np.uint8)

        # If no masks
        if result.masks is None:
            return masks_list, combined_mask

        # Convert raw masks (N, h_small, w_small)
        raw_masks = result.masks.data.cpu().numpy()

        for m in raw_masks:
            # Resize mask to match original upscale size
            m_resized = cv2.resize(
                m.astype(np.float32),
                (W, H),
                interpolation=cv2.INTER_NEAREST
            )

            # Convert boolean mask → uint8 (0 or 255)
            m_resized = (m_resized > 0.5).astype(np.uint8) * 255

            masks_list.append(m_resized)
            combined_mask = np.maximum(combined_mask, m_resized)

        return masks_list, combined_mask


# --------------------------
# TEST
# --------------------------
if __name__ == "__main__":
    url = "https://lh3.googleusercontent.com/p/AF1QipPS3uWXNBReKwqeqmC4fAyAejox0cemlEHA5YYQ=w203-h135-k-no"

    segmenter = TreeSegmenter("best.pt")
    masks_list, combined_mask = segmenter.process_image(url)

    print(f"Detected {len(masks_list)} objects")
    print("Combined mask shape:", combined_mask.shape)

    cv2.imwrite("combined_mask.png", combined_mask)
