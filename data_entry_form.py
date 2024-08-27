import sys
import os
import sqlite3
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
                             QMessageBox, QFileDialog, QFormLayout, QHBoxLayout)
from PyQt5.QtGui import QIcon, QPixmap

def add_or_update_data_in_database(database_file, table_name, data, is_update=False):
    try:
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        if is_update:
            cursor.executemany(f"UPDATE {table_name} SET name = ?, url = ? WHERE face_id = ?;", data)
        else:
            cursor.executemany(f"INSERT INTO {table_name} (face_id, name, url) VALUES (?, ?, ?);", data)
        conn.commit()
        print("Data saved successfully.")
        return True
    except sqlite3.Error as e:
        print("SQLite error:", e)
        return False
    finally:
        if conn:
            conn.close()

def get_data_by_id(database_file, table_name, face_id):
    try:
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        cursor.execute(f"SELECT face_id, name, url FROM {table_name} WHERE face_id = ?;", (face_id,))
        result = cursor.fetchone()
        return result
    except sqlite3.Error as e:
        print("SQLite error:", e)
        return None
    finally:
        if conn:
            conn.close()

def get_next_id(database_file, table_name):
    try:
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        cursor.execute(f"SELECT MAX(face_id) FROM {table_name}")
        max_id = cursor.fetchone()[0]
        if max_id is None:
            return 1
        else:
            return max_id + 1
    except sqlite3.Error as e:
        print("SQLite error:", e)
        return None
    finally:
        if conn:
            conn.close()

class DataEntryForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Add/Edit Data in Database')
        self.setGeometry(100, 100, 500, 500)

        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        search_layout = QHBoxLayout()

        self.search_id_label = QLabel('Search ID:')
        self.search_id_input = QLineEdit()
        self.search_button = QPushButton('Search')
        self.search_button.setIcon(QIcon('icons/search.png'))
        self.search_button.clicked.connect(self.search_data)

        search_layout.addWidget(self.search_id_label)
        search_layout.addWidget(self.search_id_input)
        search_layout.addWidget(self.search_button)

        self.mode_label = QLabel('Mode: Add New Data')
        self.name_label = QLabel('Name:')
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('Enter name')

        self.url_label = QLabel('URL:')
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('Enter URL')

        self.image_label = QLabel('Image:')
        self.image_input = QLineEdit()
        self.image_input.setReadOnly(True)
        self.image_button = QPushButton('Select Image')
        self.image_button.setIcon(QIcon('icons/image.png'))
        self.image_button.clicked.connect(self.select_image)

        self.image_display_label = QLabel()
        self.image_display_label.setFixedSize(200, 200)
        self.image_display_label.setStyleSheet("border: 1px solid black")

        self.submit_button = QPushButton('Submit')
        self.submit_button.setIcon(QIcon('icons/submit.png'))
        self.submit_button.clicked.connect(self.submit_data)

        form_layout.addRow(self.mode_label)
        form_layout.addRow('Name:', self.name_input)
        form_layout.addRow('URL:', self.url_input)
        form_layout.addRow('Image:', self.image_input)
        form_layout.addRow('', self.image_button)
        form_layout.addRow('Current Image:', self.image_display_label)

        main_layout.addLayout(search_layout)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.submit_button)

        self.setLayout(main_layout)

        self.image_folder = 'faces'
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
        self.editing_id = None

    def select_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Image', '', 'Images (*.png *.xpm *.jpg *.jpeg *.bmp)', options=options)
        if file_path:
            self.image_input.setText(file_path)
            self.display_image(file_path)

    def search_data(self):
        face_id = self.search_id_input.text()
        if not face_id.isdigit():
            QMessageBox.warning(self, 'Input Error', 'Please enter a valid ID.')
            return
        data = get_data_by_id('face_info.db', 'info', int(face_id))
        if data:
            self.editing_id = int(face_id)
            self.name_input.setText(data[1])
            self.url_input.setText(data[2])
            image_path = os.path.join(self.image_folder, f"{face_id}.jpg")
            if os.path.exists(image_path):
                self.display_image(image_path)
            self.mode_label.setText('Mode: Update Existing Data')
            QMessageBox.information(self, 'Data Found', 'Record found and loaded for editing.')
        else:
            self.mode_label.setText('Mode: Add New Data')
            QMessageBox.warning(self, 'Not Found', 'No record found with the given ID.')

    def submit_data(self):
        name_value = self.name_input.text()
        url_value = self.url_input.text()
        image_path = self.image_input.text()
        if not name_value or not url_value:
            QMessageBox.warning(self, 'Input Error', 'Please enter valid data.')
            return
        if self.editing_id is not None:
            data = [(name_value, url_value, self.editing_id)]
            is_update = True
            if image_path:
                old_image_path = os.path.join(self.image_folder, f"{self.editing_id}.jpg")
                if os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                    except IOError as e:
                        QMessageBox.critical(self, 'File Error', f"Failed to delete the old image: {e}")
                        return
        else:
            new_id = get_next_id('face_info.db', 'info')
            if new_id is None:
                QMessageBox.critical(self, 'Database Error', 'Failed to generate a new ID.')
                return
            data = [(new_id, name_value, url_value)]
            is_update = False

        if image_path:
            image_filename = os.path.join(self.image_folder, f"{self.editing_id if is_update else new_id}.jpg")
            try:
                with open(image_path, 'rb') as file:
                    with open(image_filename, 'wb') as output_file:
                        output_file.write(file.read())
            except IOError as e:
                QMessageBox.critical(self, 'File Error', f"Failed to save the new image: {e}")
                return

        if add_or_update_data_in_database('face_info.db', 'info', data, is_update):
            QMessageBox.information(self, 'Success', 'Data saved successfully.')
        else:
            QMessageBox.critical(self, 'Error', 'Failed to save data to the database.')

        self.name_input.clear()
        self.url_input.clear()
        self.image_input.clear()
        self.image_display_label.clear()
        self.search_id_input.clear()
        self.editing_id = None
        self.mode_label.setText('Mode: Add New Data')

    def display_image(self, image_path):
        pixmap = QPixmap(image_path)
        self.image_display_label.setPixmap(pixmap.scaled(self.image_display_label.size(), aspectRatioMode=True))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(open('style.qss', 'r').read())
    window = DataEntryForm()
    window.show()
    sys.exit(app.exec_())
