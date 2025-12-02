import torch
import cv2
import numpy as np

class DepthEstimator:
    def __init__(self, model_type="DPT_Large"):
        """
        model_type: "DPT_Large" (chính xác nhất), "DPT_Hybrid", hoặc "MiDaS_small" (nhanh nhất)
        """
        print(f"Loading MiDaS model: {model_type}...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load từ torch hub để không cần file phụ thuộc cục bộ
        self.midas = torch.hub.load("intel-isl/MiDaS", model_type)
        self.midas.to(self.device)
        self.midas.eval()

        # Load transform chuẩn của MiDaS
        midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
        if model_type == "DPT_Large" or model_type == "DPT_Hybrid":
            self.transform = midas_transforms.dpt_transform
        else:
            self.transform = midas_transforms.small_transform

    def get_depth_map(self, image_bgr):
        # Chuyển BGR sang RGB
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        
        input_batch = self.transform(img_rgb).to(self.device)

        with torch.no_grad():
            prediction = self.midas(input_batch)
            
            # Resize về kích thước gốc
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img_rgb.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()

        depth_map = prediction.cpu().numpy()
        return depth_map