import numpy as np
import cv2
from ultralytics import YOLO
import requests
# class TreeSegmenter:
#     def __init__(self, model_name="best.pt"):
#         print(f"Loading Segmentation Model from: {model_name}")
#         self.model = YOLO(model_name)

#     def process_image(self, url: str):
#         """
#         Predict directly from a URL (manual download).
#         Returns:
#           - masks_list: list of np.ndarray (H, W) for each object
#           - combined_mask: np.ndarray (H, W)
#         """

#         # 1. Load image from URL into numpy array
#         img_rgb = load_image_from_url(url)  # float32 [0,1]
#         img_bgr = (img_rgb * 255).astype(np.uint8)
#         h, w = img_bgr.shape[:2]

#         # 2. YOLO prediction from numpy array
#         results = self.model.predict(
#             img_bgr,
#             retina_masks=True,
#             conf=0.1,
#             verbose=False
#         )[0]

#         # 3. Masks
#         masks_list = []
#         combined_mask = np.zeros((h, w), dtype=np.uint8)
#         if results.masks is not None:
#             raw_masks = results.masks.data.cpu().numpy()
#             for m in raw_masks:
#                 m_resized = np.uint8(np.round(m * 255))
#                 masks_list.append(m_resized)
#                 combined_mask = np.maximum(combined_mask, m_resized)

#         return masks_list, combined_mask

# if __name__ == "__main__":
#     test_url = "https://th.bing.com/th/id/R.31fabb9bfd231e7c123b073977db3207?rik=mr0FiiTUX4ioDg&pid=ImgRaw&r=0"

#     segmenter = TreeSegmenter("best.pt")
#     masks_list, combined_mask = segmenter.process_image(test_url)

#     print(f"Detected {len(masks_list)} objects")
#     print(f"Combined mask shape: {combined_mask.shape}")

#     # Optional: save combined mask
#     import cv2
#     cv2.imwrite("combined_mask.png", combined_mask)

from ultralytics import YOLO
import cv2
import numpy as np
import requests


def load_image_from_url_segmentation(url):
    resp = requests.get(url)
    data = np.frombuffer(resp.content, np.uint8)
    img_bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return img_bgr  # GIỮ BGR uint8

def upscale(img, target_min=512):
    h, w = img.shape[:2]
    scale = max(target_min / h, target_min / w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    img_up = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    return img_up

model = YOLO("best.pt")

url = "https://lh3.googleusercontent.com/p/AF1QipPS3uWXNBReKwqeqmC4fAyAejox0cemlEHA5YYQ=w203-h135-k-no"

img = load_image_from_url_segmentation(url)
print("Original:", img.shape)

img_up = upscale(img)
print("Upscaled:", img_up.shape)

result = model(img_up, conf=0.1, retina_masks=True, save=True)[0]

print("Boxes:", len(result.boxes))
print("Masks:", None if result.masks is None else result.masks.shape)
