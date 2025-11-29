import os
import cv2
import numpy as np
from ultralytics import YOLO

class TreeSegmenter:
    def __init__(self, model_name="best.pt"):
        # 1. Xác định đường dẫn file model
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Ưu tiên tìm model ngay trong thư mục này (greenness)
        path_in_here = os.path.join(current_dir, model_name)
        
        # Hoặc tìm ở thư mục cha (green_verification)
        project_root = os.path.dirname(current_dir)
        path_in_root = os.path.join(project_root, model_name)

        if os.path.exists(path_in_here):
            self.model_path = path_in_here
        elif os.path.exists(path_in_root):
            self.model_path = path_in_root
        else:
            # Nếu không tìm thấy file nào, báo lỗi rõ ràng thay vì cố tải lung tung
            print(f"❌ ERROR: Không tìm thấy file model '{model_name}' tại:")
            print(f"   - {path_in_here}")
            print(f"   - {path_in_root}")
            raise FileNotFoundError(f"Vui lòng copy file {model_name} vào thư mục {current_dir}")

        print(f"✅ Loading Segmentation Model from: {self.model_path}")
        self.model = YOLO(self.model_path)

    def process_image(self, image_input):
        if isinstance(image_input, str):
            if not os.path.exists(image_input):
                print(f"Error: Image path not found {image_input}")
                return None, None
            img = cv2.imread(image_input)
        elif isinstance(image_input, np.ndarray):
            img = image_input
        else:
            raise ValueError("Input must be a file path or a numpy array.")

        if img is None: return None, None

        h, w = img.shape[:2]
        
        # 2. Chạy dự đoán
        # conf=0.1: Để thấp để dễ bắt cây hơn (model tự train thường cần conf thấp lúc test)
        results = self.model.predict(img, retina_masks=True, conf=0.1, verbose=False)[0]
        
        combined_mask = np.zeros((h, w), dtype=np.uint8)
        
        if results.masks is not None:
            raw_masks = results.masks.data.cpu().numpy()
            for m in raw_masks:
                m_resized = cv2.resize(m, (w, h))
                combined_mask = np.maximum(combined_mask, (m_resized * 255).astype(np.uint8))
        else:
            print("⚠️ Cảnh báo: Model chạy thành công nhưng không tìm thấy đối tượng nào trong ảnh.")

        masked_img = cv2.bitwise_and(img, img, mask=combined_mask)
        return combined_mask, masked_img

# --- PHẦN CHẠY TEST TRỰC TIẾP ---
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    img_filename = "image.jpg"
    img_path = os.path.join(current_dir, img_filename)
    
    # ==========================================
    # 👇 SỬA TÊN FILE MODEL CỦA BẠN Ở ĐÂY 👇
    # Ví dụ: "best.pt", "tree_model.pt"...
    MY_MODEL_NAME = "best.pt"  
    # ==========================================

    print(f"--- Bắt đầu test ---")
    print(f"Ảnh input: {img_path}")
    print(f"Model dùng: {MY_MODEL_NAME}")

    # Kiểm tra file ảnh có tồn tại không
    if not os.path.exists(img_path):
        print(f"❌ LỖI: Không tìm thấy file ảnh '{img_filename}' trong thư mục {current_dir}")
        exit()

    # Kiểm tra file model có tồn tại không trước khi chạy
    model_path_check = os.path.join(current_dir, MY_MODEL_NAME)
    if not os.path.exists(model_path_check):
        print(f"❌ LỖI: Không tìm thấy file model '{MY_MODEL_NAME}' trong thư mục {current_dir}")
        print("👉 Hãy copy file model bạn đã train vào đây rồi chạy lại.")
        exit()

    try:
        # Khởi tạo và chạy
        segmenter = TreeSegmenter(model_name=MY_MODEL_NAME)
        mask, result = segmenter.process_image(img_path)

        if result is not None and np.sum(mask) > 0:
            # Resize ảnh để hiển thị vừa màn hình
            display_h = 600
            scale = display_h / result.shape[0]
            display_w = int(result.shape[1] * scale)
            
            show_mask = cv2.resize(mask, (display_w, display_h))
            show_result = cv2.resize(result, (display_w, display_h))

            cv2.imshow("Mask", show_mask)
            cv2.imshow("Tree Result", show_result)
            
            print("✅ Thành công! Đã hiện cửa sổ kết quả.")
            
            # Lưu file để kiểm tra
            cv2.imwrite(os.path.join(current_dir, "test_mask.png"), mask)
            cv2.imwrite(os.path.join(current_dir, "test_result.png"), result)
            print("💾 Đã lưu ảnh: test_mask.png và test_result.png")

            print("Bấm phím bất kỳ vào cửa sổ ảnh để thoát...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("⚠️ Kết quả: Không tìm thấy cây nào trong ảnh (Mask đen thui).")
            print("Gợi ý: Kiểm tra lại model hoặc thử ảnh khác rõ hơn.")

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")