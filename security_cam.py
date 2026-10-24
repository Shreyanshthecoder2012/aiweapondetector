from ultralytics import YOLO
import cv2
from datetime import datetime
from pathlib import Path

MODEL_PATH = "best.pt"
CONFIDENCE = 0.60

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Could not open webcam")

print("🔴 Security camera started")
print("Press Q to quit")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to read camera")
        break

    results = model(frame, conf=CONFIDENCE, verbose=False)

    weapon_detected = False

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            name = model.names[cls]

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if name == "weapon":
                weapon_detected = True

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    3
                )

                cv2.putText(
                    frame,
                    f"WEAPON {conf:.0%}",
                    (x1, max(y1 - 10, 30)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            elif name == "person":
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"PERSON {conf:.0%}",
                    (x1, max(y1 - 10, 30)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

    # Status
    if weapon_detected:
        status = "!! WEAPON ALERT !!"
        color = (0, 0, 255)
    else:
        status = "SYSTEM NORMAL"
        color = (0, 255, 0)

    cv2.rectangle(frame, (10, 10), (400, 60), (20, 20, 20), -1)

    cv2.putText(
        frame,
        status,
        (20, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        color,
        2
    )

    cv2.imshow("Smart Security Vision", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
