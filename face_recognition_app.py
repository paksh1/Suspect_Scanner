import sys
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon, QDesktopServices, QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QFileDialog
from PyQt5.QtCore import QTimer
import cv2
import os
import sqlite3
from deepface import DeepFace
import numpy as np


class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(QUrl(self.text()))

class FaceRecognitionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face and Weapon Detection App")
        self.setGeometry(100, 100, 900, 600)

        self.matched_filename = None

        layout = QVBoxLayout()

        # Add a title label
        title_label = QLabel("CrimeCatcher")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 20px;")
        layout.addWidget(title_label, alignment=Qt.AlignCenter)

        # Add a horizontal layout for input image and matched image
        self.image_layout = QHBoxLayout()

        self.input_image_label = QLabel()
        self.input_image_label.setFixedSize(300, 300)
        self.input_image_label.setStyleSheet("border: 2px solid #555")
        self.image_layout.addWidget(self.input_image_label, alignment=Qt.AlignCenter)

        self.matched_image_label = QLabel()
        self.matched_image_label.setFixedSize(300, 300)
        self.matched_image_label.setStyleSheet("border: 2px solid #555")
        self.image_layout.addWidget(self.matched_image_label, alignment=Qt.AlignCenter)

        layout.addLayout(self.image_layout)

        self.info_label = ClickableLabel()
        self.info_label.setStyleSheet("font-size: 16px; color: #333; padding: 10px; background-color: #f0f0f0; border: 2px solid #ccc; border-radius: 5px;")
        layout.addWidget(self.info_label, alignment=Qt.AlignCenter)

        # Add a layout for buttons
        self.button_layout = QHBoxLayout()

        self.webcam_button = QPushButton(QIcon("webcam_icon.png"), "Recognize from Webcam")
        self.webcam_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border: none; padding: 10px 20px; font-size: 16px; } QPushButton:hover { background-color: #45a049; }")
        self.webcam_button.clicked.connect(self.recognize_from_webcam)
        self.button_layout.addWidget(self.webcam_button)

        self.photo_button = QPushButton(QIcon("photo_icon.png"), "Recognize from Photo")
        self.photo_button.setStyleSheet("QPushButton { background-color: #008CBA; color: white; border: none; padding: 10px 20px; font-size: 16px; } QPushButton:hover { background-color: #007B9A; }")
        self.photo_button.clicked.connect(self.recognize_from_photo)
        self.button_layout.addWidget(self.photo_button)

        layout.addLayout(self.button_layout)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_webcam_feed)

        self.cap = None
        self.images = []
        self.filenames = []

        # Load YOLO model for weapon detection
        self.net = cv2.dnn.readNet("D:\\Assignments\\python\\python path\\Scripts\\yolov3.weights", "D:\\Assignments\\python\\python path\\Scripts\\yolov3.cfg")
        with open("D:\\Assignments\\python\\python path\\Scripts\\coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        self.layer_names = self.net.getLayerNames()
        self.output_layers = self.net.getUnconnectedOutLayersNames()


    def recognize_from_webcam(self):
        self.clear_gui()
        self.images, self.filenames = self.load_images_from_folder("faces")
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FPS, 120)
        self.timer.start(0)

    def recognize_from_photo(self):
        self.clear_gui()
        image_file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if image_file_path:
            self.images, self.filenames = self.load_images_from_folder("faces")
            self.display_image(image_file_path, self.input_image_label)
            self.recognize_face_from_photo(image_file_path)

    def clear_gui(self):
        self.input_image_label.clear()
        self.matched_image_label.clear()
        self.info_label.clear()

    def load_images_from_folder(self, folder):
        images = []
        filenames = []
        for filename in os.listdir(folder):
            img_path = os.path.join(folder, filename)
            if os.path.isfile(img_path):
                images.append(img_path)
                filenames.append(filename)
        return images, filenames

    def process_frame(self, frame):
        for img_path, filename in zip(self.images, self.filenames):
            results = DeepFace.verify(frame, img_path, enforce_detection=False)
            if results is not None and results.get("verified"):
                self.matched_filename = filename
                return True
        return False

    
    def detect_weapons(self, frame):
        height, width = frame.shape[:2]  # Get the height and width of the frame

        # Create a blob from the frame
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)  # Set the input for the network
        outputs = self.net.forward(self.output_layers)  # Forward pass to get output

        # Loop through the outputs
        for output in outputs:
            for detection in output:
                scores = detection[5:]  # Get the scores for the classes
                class_id = np.argmax(scores)  # Get the class with the highest score
                confidence = scores[class_id]  # Confidence score for the detected class

                # Check if confidence is above threshold and class is either knife or gun
                if confidence > 0.5 and self.classes[class_id] in ["knife", "gun"]:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    # Draw rectangle around the detected weapon
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(frame, f"{self.classes[class_id]}: {confidence:.2f}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                    return True  # Return True if a weapon is detected

        return False  # Return False if no weapon is detected



    def update_webcam_feed(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Detect faces in the frame
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        # Draw rectangles around the faces and check for matches
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            face_roi = frame[y:y+h, x:x+w]

            if self.process_frame(face_roi):
                matched_filename_without_extension = os.path.splitext(self.matched_filename)[0]
                info_text = f"<b>Matched Face:</b> {matched_filename_without_extension}<br>"
                info_text += self.retrieve_data_from_database(matched_filename_without_extension)
                self.info_label.setText(info_text)
                matched_image_path = os.path.join("faces", self.matched_filename)
                self.display_image(matched_image_path, self.matched_image_label)
                self.display_frame(frame, self.input_image_label)
                self.timer.stop()
                self.cap.release()
                return

        # Check for weapons
        if self.detect_weapons(frame):
            self.info_label.setText("⚠️ Weapon detected! Please stay alert!")
        
        self.display_frame(frame, self.input_image_label)

    def retrieve_data_from_database(self, face_id):
        conn = sqlite3.connect('face_info.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM info WHERE face_id=?", (face_id,))
        rows = cursor.fetchall()
        info_text = "<br><b>Details:</b><br>"
        if rows:
            for row in rows:
                info_text += f"<b>Name:</b> {row[1]}<br>"
                info_text += f"<br>More details: <a href='{row[2]}'>Click here</a>"
                if len(row) > 3:
                    info_text += f"<b>Gender:</b> {row[3]}<br>"
        else:
            info_text += "Face does not match with anyone.<br>"
        conn.close()
        return info_text

    def display_frame(self, frame, label):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        convert_to_qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(convert_to_qt_format.rgbSwapped())
        label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def display_image(self, image_path, label):
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def recognize_face_from_photo(self, photo_path):
        photo = cv2.imread(photo_path)
        if self.process_frame(photo):
            matched_image_path = os.path.join("faces", self.matched_filename)
            self.display_image(matched_image_path, self.matched_image_label)
            matched_filename_without_extension = os.path.splitext(self.matched_filename)[0]
            info_text = f"<b>Matched Face:</b> {matched_filename_without_extension}<br>"
            info_text += self.retrieve_data_from_database(matched_filename_without_extension)
            self.info_label.setText(info_text)
        else:
            self.info_label.setText("No match found for the uploaded photo.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceRecognitionApp()
    window.show()
    sys.exit(app.exec_())
