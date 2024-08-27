import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QPushButton
from data_entry_form import DataEntryForm
from face_recognition_app import FaceRecognitionApp

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Face Recognition System')
        self.setGeometry(100, 100, 900, 600)

        layout = QVBoxLayout()

        self.tab_widget = QTabWidget()

        self.data_entry_form = DataEntryForm()
        self.face_recognition_app = FaceRecognitionApp()
        with open('style.qss', 'r') as f:
            style = f.read()
            self.data_entry_form.setStyleSheet(style)

        self.tab_widget.addTab(self.face_recognition_app, 'Face Recognition App')
        self.tab_widget.addTab(self.data_entry_form, 'Data Entry Form')

        layout.addWidget(self.tab_widget)

        self.setLayout(layout)

        self.setStyleSheet(open('style_2.qss').read())  # Apply the style

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
