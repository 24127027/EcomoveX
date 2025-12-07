import os
import cv2
from backend.utils.green_verification.orchestrator import run_green_verification_pipeline

if __name__ == "__main__":
    MY_MODEL_NAME = "yolov11x-seg.pt"
    model_check_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), MY_MODEL_NAME
    )
    if not os.path.exists(model_check_path):
        print(
            f"❌ CẢNH BÁO: Không tìm thấy file model '{MY_MODEL_NAME}' trong thư mục greenness!"
        )
    # --- SỬA ĐOẠN NÀY ---
    # 1. Lấy đường dẫn thư mục chứa file code này (thư mục greenness)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Nối với tên ảnh để ra đường dẫn đầy đủ
    img_path = os.path.join(current_dir, "image_2.jpg")
    # --------------------

    print(f"Đang tìm ảnh tại: {img_path}")  # In ra để kiểm tra

    if not os.path.exists(img_path):
        print(f"❌ Không tìm thấy ảnh tại: {img_path}")
    else:
        # 2. TRUYỀN TÊN MODEL VÀO HÀM
        result = run_green_verification_pipeline(img_path, model_path=MY_MODEL_NAME)

        if result:
            print(f"Score: {result['score']}")

            # Lưu ảnh kết quả (Cũng nên lưu vào cùng thư mục script cho gọn)
            cv2.imwrite(os.path.join(current_dir, "output_mask.png"), result["mask"])
            cv2.imwrite(
                os.path.join(current_dir, "output_tree.png"), result["tree_img"]
            )

            # Xử lý depth map
            depth_map = result["depth_map"]
            depth_normalized = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX)
            depth_uint8 = depth_normalized.astype("uint8")
            depth_colored = cv2.applyColorMap(depth_uint8, cv2.COLORMAP_MAGMA)

            cv2.imwrite(os.path.join(current_dir, "output_depth.png"), depth_colored)
            print("✅ Đã lưu các file output.")
