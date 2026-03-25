from ultralytics import YOLO
import cv2

# Load YOLO model (use pretrained or your trained one)
model = YOLO("yolov8n.pt")  

def detect_weeds(image_path):
    image = cv2.imread(image_path)

    results = model(image)

    weed_count = 0
    total_conf = 0

    for r in results:
        boxes = r.boxes

        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Assume class 0 = weed (you can adjust later)
            if cls == 0:
                weed_count += 1
                total_conf += conf

                # Draw bounding box
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(image, f"Weed {conf:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 0, 255), 2)

    avg_conf = (total_conf / weed_count * 100) if weed_count > 0 else 0

    return image, weed_count, round(avg_conf, 2)