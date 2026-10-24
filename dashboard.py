import sys
import os
import time
import cv2
import subprocess
import threading

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)

from ultralytics import YOLO
import yagmail


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "best.pt"
CAMERA_INDEX = 0

# YOLO confidence threshold
CONFIDENCE = 0.20

# Cooldown between alerts/photos
COOLDOWN = 5

# Evidence folder
PHOTO_DIR = "evidence"

# ------------------------------------------------------------
# EMAIL CONFIGURATION
# ------------------------------------------------------------
# Use an APP PASSWORD, not your normal Gmail password.

EMAIL_SENDER = "rslkarora123@outlook.com"
EMAIL_PASSWORD = "xlms dmzn qvlk yknm"
EMAIL_RECEIVER = "rslkarora123@outlook.com"


# ============================================================
# COLORS
# ============================================================

BG = "#0b0d10"
PANEL = "#111419"
BORDER = "#20242b"

TEXT = "#f1f3f5"
MUTED = "#8b929d"

GREEN = "#35d07f"
RED = "#ff4d5a"
YELLOW = "#f5c451"


# ============================================================
# SETUP
# ============================================================

os.makedirs(PHOTO_DIR, exist_ok=True)

print("Loading YOLO model...")
model = YOLO(MODEL_PATH)
print("Model loaded.")


# ============================================================
# EMAIL
# ============================================================

email_client = None

if (
    EMAIL_SENDER != "YOUR_EMAIL@gmail.com"
    and EMAIL_PASSWORD != "YOUR_APP_PASSWORD"
    and EMAIL_RECEIVER != "RECEIVER_EMAIL@gmail.com"
):
    try:
        email_client = yagmail.SMTP(
            EMAIL_SENDER,
            EMAIL_PASSWORD
        )

        print("Email system ready.")

    except Exception as e:
        print("Email initialization failed:", e)


# ============================================================
# DASHBOARD
# ============================================================

class SecurityDashboard(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Sentinel")
        self.resize(1200, 720)

        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        self.cap = cv2.VideoCapture(CAMERA_INDEX)

        if not self.cap.isOpened():
            print("ERROR: Could not open camera.")

        # ----------------------------------------------------
        # COOLDOWN
        # ----------------------------------------------------

        self.last_person_photo = 0
        self.last_weapon_alert = 0

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        self.setup_ui()

        # ----------------------------------------------------
        # TIMER
        # ----------------------------------------------------

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.timer.start(30)

    # ========================================================
    # UI SETUP
    # ========================================================

    def setup_ui(self):

        central = QWidget()

        central.setStyleSheet(f"""
            QWidget {{
                background: {BG};
                color: {TEXT};
                font-family: Arial;
            }}
        """)

        self.setCentralWidget(central)

        main = QVBoxLayout(central)

        main.setContentsMargins(
            28,
            24,
            28,
            24
        )

        main.setSpacing(18)

        # ====================================================
        # HEADER
        # ====================================================

        header = QHBoxLayout()

        title = QLabel("SENTINEL")

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 2px;
        """)

        subtitle = QLabel(
            "AI SECURITY MONITOR"
        )

        subtitle.setStyleSheet(f"""
            font-size: 10px;
            color: {MUTED};
            letter-spacing: 1px;
        """)

        title_box = QVBoxLayout()

        title_box.setSpacing(2)

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.system_status = QLabel(
            "●  SYSTEM ONLINE"
        )

        self.system_status.setStyleSheet(f"""
            color: {GREEN};
            font-size: 12px;
            font-weight: 600;
        """)

        header.addWidget(
            self.system_status
        )

        main.addLayout(header)

        # ====================================================
        # CONTENT
        # ====================================================

        content = QHBoxLayout()

        content.setSpacing(16)

        # ====================================================
        # CAMERA PANEL
        # ====================================================

        camera_frame = QFrame()

        camera_frame.setStyleSheet(f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        camera_layout = QVBoxLayout(
            camera_frame
        )

        camera_layout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        self.camera = QLabel()

        self.camera.setAlignment(
            Qt.AlignCenter
        )

        self.camera.setMinimumSize(
            700,
            500
        )

        self.camera.setStyleSheet("""
            background: black;
            border-radius: 8px;
        """)

        camera_layout.addWidget(
            self.camera
        )

        content.addWidget(
            camera_frame,
            4
        )

        # ====================================================
        # SIDE PANEL
        # ====================================================

        side = QVBoxLayout()

        side.setSpacing(12)

        # Person

        self.person_card = self.create_card(
            "PERSON",
            "0"
        )

        self.person_value = (
            self.person_card.findChild(
                QLabel,
                "value"
            )
        )

        side.addWidget(
            self.person_card
        )

        # Weapon

        self.weapon_card = self.create_card(
            "WEAPON",
            "0"
        )

        self.weapon_value = (
            self.weapon_card.findChild(
                QLabel,
                "value"
            )
        )

        side.addWidget(
            self.weapon_card
        )

        # Confidence

        self.conf_card = self.create_card(
            "CONFIDENCE",
            "0%"
        )

        self.conf_value = (
            self.conf_card.findChild(
                QLabel,
                "value"
            )
        )

        side.addWidget(
            self.conf_card
        )

        # ====================================================
        # STATUS
        # ====================================================

        status_frame = QFrame()

        status_frame.setStyleSheet(f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        status_layout = QVBoxLayout(
            status_frame
        )

        status_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        status_title = QLabel(
            "STATUS"
        )

        status_title.setStyleSheet(f"""
            color: {MUTED};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1px;
        """)

        self.status = QLabel(
            "●  CLEAR"
        )

        self.status.setStyleSheet(f"""
            color: {GREEN};
            font-size: 18px;
            font-weight: 700;
        """)

        status_layout.addWidget(
            status_title
        )

        status_layout.addSpacing(8)

        status_layout.addWidget(
            self.status
        )

        side.addWidget(
            status_frame
        )

        side.addStretch()

        content.addLayout(
            side,
            1
        )

        main.addLayout(
            content
        )

        # ====================================================
        # FOOTER
        # ====================================================

        self.footer = QLabel(
            "Monitoring camera 01"
        )

        self.footer.setStyleSheet(f"""
            color: {MUTED};
            font-size: 11px;
        """)

        main.addWidget(
            self.footer
        )

    # ========================================================
    # CARD
    # ========================================================

    def create_card(
        self,
        title,
        value
    ):

        frame = QFrame()

        frame.setStyleSheet(f"""
            QFrame {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            18,
            15,
            18,
            15
        )

        label = QLabel(title)

        label.setStyleSheet(f"""
            color: {MUTED};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1px;
        """)

        value_label = QLabel(value)

        value_label.setObjectName(
            "value"
        )

        value_label.setStyleSheet("""
            font-size: 30px;
            font-weight: 700;
        """)

        layout.addWidget(
            label
        )

        layout.addSpacing(4)

        layout.addWidget(
            value_label
        )

        return frame

    # ========================================================
    # SAVE PHOTO
    # ========================================================

    def save_photo(
        self,
        frame,
        event_type
    ):

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = os.path.join(
            PHOTO_DIR,
            f"{event_type}_{timestamp}.jpg"
        )

        cv2.imwrite(
            filename,
            frame
        )

        print(
            f"Photo saved: {filename}"
        )

        return filename

    # ========================================================
    # ALARM
    # ========================================================

    def play_alarm(self):

        sound = (
            "/usr/share/sounds/"
            "freedesktop/stereo/"
            "alarm-clock-elapsed.oga"
        )

        if os.path.exists(sound):

            subprocess.Popen([
                "paplay",
                sound
            ])

        else:

            # Fallback system beep
            print("\a", end="")

    # ========================================================
    # SEND EMAIL
    # ========================================================

    def send_warning_email(
        self,
        filename,
        confidence
    ):

        if email_client is None:

            print(
                "Email not configured. "
                "Skipping email."
            )

            return

        try:

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            email_client.send(
                to=EMAIL_RECEIVER,

                subject=(
                    "Security Alert: "
                    "Possible Weapon Detected"
                ),

                contents=(
                    "Security monitoring system "
                    "detected a possible weapon.\n\n"
                    f"Time: {timestamp}\n"
                    f"Confidence: {confidence:.1%}\n\n"
                    "Please verify the camera feed "
                    "and follow your site's security "
                    "procedures."
                ),

                attachments=[
                    filename
                ]
            )

            print(
                "WARNING EMAIL SENT"
            )

        except Exception as e:

            print(
                "EMAIL ERROR:",
                e
            )

    # ========================================================
    # PROCESS FRAME
    # ========================================================

    def update_frame(self):

        ret, frame = self.cap.read()

        if not ret:
            return

        # ----------------------------------------------------
        # YOLO
        # ----------------------------------------------------

        results = model(
            frame,
            conf=CONFIDENCE,
            verbose=False
        )

        person_count = 0
        weapon_count = 0

        highest_weapon_conf = 0.0

        # ----------------------------------------------------
        # DETECTIONS
        # ----------------------------------------------------

        for result in results:

            for box in result.boxes:

                cls = int(
                    box.cls[0]
                )

                conf = float(
                    box.conf[0]
                )

                name = model.names[cls]

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                # ============================================
                # PERSON
                # ============================================

                if name == "person":

                    person_count += 1

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (255, 200, 50),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"person {conf:.0%}",
                        (
                            x1,
                            max(
                                y1 - 8,
                                20
                            )
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 200, 50),
                        2
                    )

                # ============================================
                # WEAPON
                # ============================================

                elif name == "weapon":

                    weapon_count += 1

                    highest_weapon_conf = max(
                        highest_weapon_conf,
                        conf
                    )

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (60, 80, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        f"weapon {conf:.0%}",
                        (
                            x1,
                            max(
                                y1 - 8,
                                20
                            )
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (60, 80, 255),
                        2
                    )

        # ====================================================
        # EVENT HANDLING
        # ====================================================

        now = time.time()

        # ----------------------------------------------------
        # PERSON PHOTO
        # ----------------------------------------------------

        if person_count > 0:

            if (
                now - self.last_person_photo
                >= COOLDOWN
            ):

                self.save_photo(
                    frame,
                    "person"
                )

                self.last_person_photo = now

        # ----------------------------------------------------
        # WEAPON ALERT
        # ----------------------------------------------------

        if weapon_count > 0:

            if (
                now - self.last_weapon_alert
                >= COOLDOWN
            ):

                # Save evidence
                filename = self.save_photo(
                    frame,
                    "weapon"
                )

                # Sound alarm
                self.play_alarm()

                # Email in background
                email_thread = threading.Thread(
                    target=self.send_warning_email,
                    args=(
                        filename,
                        highest_weapon_conf
                    ),
                    daemon=True
                )

                email_thread.start()

                self.last_weapon_alert = now

        # ====================================================
        # UPDATE DASHBOARD
        # ====================================================

        self.person_value.setText(
            str(person_count)
        )

        self.weapon_value.setText(
            str(weapon_count)
        )

        self.conf_value.setText(
            f"{highest_weapon_conf:.0%}"
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if weapon_count > 0:

            self.status.setText(
                "●  WEAPON DETECTED"
            )

            self.status.setStyleSheet(f"""
                color: {RED};
                font-size: 18px;
                font-weight: 700;
            """)

            self.system_status.setStyleSheet(f"""
                color: {RED};
                font-size: 12px;
                font-weight: 600;
            """)

            self.system_status.setText(
                "●  SECURITY ALERT"
            )

        else:

            self.status.setText(
                "●  CLEAR"
            )

            self.status.setStyleSheet(f"""
                color: {GREEN};
                font-size: 18px;
                font-weight: 700;
            """)

            self.system_status.setStyleSheet(f"""
                color: {GREEN};
                font-size: 12px;
                font-weight: 600;
            """)

            self.system_status.setText(
                "●  SYSTEM ONLINE"
            )

        # ====================================================
        # DISPLAY FRAME
        # ====================================================

        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        h, w, ch = frame_rgb.shape

        image = QImage(
            frame_rgb.data,
            w,
            h,
            ch * w,
            QImage.Format_RGB888
        )

        pixmap = QPixmap.fromImage(
            image
        )

        self.camera.setPixmap(
            pixmap.scaled(
                self.camera.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(self, event):

        self.timer.stop()

        if self.cap:
            self.cap.release()

        event.accept()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = SecurityDashboard()

    window.show()

    sys.exit(
        app.exec()
    )
