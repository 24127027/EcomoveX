import os
from ultralytics import YOLO

if __name__ == "__main__":
    # 1. Setup đường dẫn
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "best.pt")  # File model của bạn
    img_path = os.path.join(current_dir, "image.jpg")  # File ảnh bạn vừa gửi

    print(f"--- 🕵️‍♀️ ĐANG SOI MODEL: {model_path} ---")

    if not os.path.exists(model_path):
        print(f"❌ Lỗi: Không thấy file model {model_path}")
        exit()

    # 2. Load Model & In thông tin ruột gan model
    model = YOLO(model_path)
    print("✅ Đã load model!")
    print(f"🧠 Model Task: {model.task}")  # Phải là 'segment'
    print(f"📋 Danh sách Class model học được: {model.names}")
    # ^^^ Dòng trên cực quan trọng: Nó sẽ in ra {0: 'tree', 1: 'car'...}
    # Bạn xem nó có chữ 'tree' hay 'plant' không nhé.

    # 3. Chạy dự đoán với ngưỡng cực thấp (Low Confidence)
    print("\n--- 🚀 ĐANG QUÉT (CONF=0.05) ---")
    if os.path.exists(img_path):
        # conf=0.05: Chỉ cần nghi ngờ 5% là cây cũng bắt lấy
        results = model.predict(
            img_path,
            conf=0.05,
            save=True,
            project=current_dir,
            name="test_result",
            exist_ok=True,
        )

        result = results[0]
        print(f"\n📊 Kết quả tìm thấy: {len(result)} đối tượng")

        if len(result) > 0:
            print("🎉 Model ĐÃ nhìn thấy gì đó!")
            classes = result.boxes.cls.cpu().numpy()
            confs = result.boxes.conf.cpu().numpy()

            for i, (cls, conf) in enumerate(zip(classes, confs)):
                class_name = model.names[int(cls)]
                print(f"   👉 Tìm thấy: '{class_name}' (Độ tin cậy: {conf:.2f})")

            print(
                f"\n📸 Ảnh kết quả đã lưu tại: {os.path.join(current_dir, 'test_result', 'image.jpg')}"
            )
            print("👉 Hãy mở ảnh đó lên xem nó vẽ khung vào đâu!")
        else:
            print("❌ Model vẫn KHÔNG thấy gì cả (ngay cả với conf=0.05).")
            print(
                "👉 KẾT LUẬN: Model 'best.pt' này train không tốt hoặc không phù hợp với ảnh cây cảnh này."
            )
            print(
                "💡 GIẢI PHÁP: Bạn nên thử dùng model chuẩn 'yolov8n-seg.pt' để test xem code có lỗi không."
            )

    else:
        print("❌ Không thấy ảnh image.jpg")
