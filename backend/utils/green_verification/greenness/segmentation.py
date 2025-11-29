from ultralytics import YOLO
import numpy as np

class Segmentation:
    def __init__(self, model_name="best.pt"):
        self.model = YOLO(model_name)

    def return_mask(self, image_paths):
        self.results = self.model.predict(source=image_paths, save=False)
        results = self.results
        masks = np.array([])
        for result in results:
            mask = result.masks.data.numpy()
            masks = np.append(masks, mask)
        return masks