from ultralytics import YOLO
import cv2
from pathlib import Path

MODEL_PATH = "best.pt"
IMAGE_PATH = input("Enter image path: ").strip()

model = YOLO(MODEL_PATH)

image = cv2.imread(IMAGE_PATH)

if image is None:
    raise FileNotFoundError(f"Could not read image: {IMAGE_PATH}")

results = model(image, conf=0.20, verbose=False)

weapon_found = False

for result in results:
    for box in result.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        name = model.names[cls]

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        if name == "weapon":
            weapon_found = True
            color = (0, 0, 255)
            label = f"WEAPON {conf:.1%}"
        else:
            color = (0, 255, 0)
            label = f"{name.upper()} {conf:.1%}"

        cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)

        cv2.putText(
            image,
            label,
            (x1, max(y1 - 10, 30)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2
        )

if weapon_found:
    print("\n🔴 WEAPON DETECTED")
else:
    print("\n🟢 NO WEAPON DETECTED")

output = "test_result.jpg"
cv2.imwrite(output, image)

print(f"Result saved to: {output}")

cv2.imshow("Weapon Detection Test", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
