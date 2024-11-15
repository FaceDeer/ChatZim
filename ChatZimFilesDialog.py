import os
from PyQt6.QtWidgets import QLineEdit, QVBoxLayout, QWidget, QPushButton, QDialog, QCheckBox, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout, QFileDialog
import json

import configparser
def extract_name_from_ini(root_path):
    file_path = os.path.join(root_path, "notebook.zim")
    config = configparser.ConfigParser()
    config.read(file_path)
    try:
        name = config['Notebook']['name']
        return name
    except:
        return None

import time
def get_creation_date_in_seconds(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        lines = file.readlines()
        if len(lines) >= 3:
            creation_date_line = lines[2].strip()
            if creation_date_line.startswith("Creation-Date:"):
                creation_date_str = creation_date_line.split(":", 1)[1].strip()
                # Convert the creation date to Unix epoch format in seconds
                creation_date_epoch = str(int(time.mktime(time.strptime(creation_date_str, "%Y-%m-%dT%H:%M:%S%z"))))
                return creation_date_epoch
    return None

def clearLayout(layout):
  while layout.count():
    child = layout.takeAt(0)
    if child.widget():
      child.widget().deleteLater()

class ChatZimFilesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Document Sets")
        self.setMinimumSize(600, 300)
        self.parent = parent

        self.file_list = []

        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.root_path_input = QLineEdit()
        top_layout.addWidget(QLabel("Root Path:"))
        top_layout.addWidget(self.root_path_input)
        load_files_button = QPushButton("Load Notebook")
        load_files_button.clicked.connect(self.load_files)
        top_layout.addWidget(load_files_button)
        main_layout.addLayout(top_layout)

        # Checkbox area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        container_widget = QWidget()
        scroll_area.setWidget(container_widget)
        self.file_checkboxes_layout = QVBoxLayout(container_widget)


        bottom_layout = QHBoxLayout()

        load_button = QPushButton("Load Settings")
        load_button.clicked.connect(self.load_settings)
        bottom_layout.addWidget(load_button)

        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        bottom_layout.addWidget(save_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        bottom_layout.addWidget(close_button)

        main_layout.addLayout(bottom_layout)
        
        selected_notebook = parent.prefs.get("root_path")
        if selected_notebook:
            self.root_path_input.setText(selected_notebook)
            self.load_files()
        else:
            self.root_path_input.setPlaceholderText("Enter root path")

        self.setLayout(main_layout)

    def load_files(self):
        root_path = self.root_path_input.text()
        if not os.path.isdir(root_path):
            return
        name = extract_name_from_ini(root_path)
        if name is None:
            return

        clearLayout(self.file_checkboxes_layout)

        self.parent.prefs["root_path"] = root_path
        self.parent.prefs["name"] = name
        
        old_prefs = self.parent.prefs["pages"]
        new_prefs = {}
        self.parent.prefs["pages"] = new_prefs
        
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, root_path)
                    creation_date = get_creation_date_in_seconds(file_path)
                    if creation_date is None:
                        print(relative_path + " had no creation date")
                        continue
                    if creation_date in new_prefs:
                        print(relative_path + " has an identical creation date to " + new_prefs[creation_date]["relative_path"])
                        continue

                    #TODO simplify
                    if creation_date in old_prefs:
                        new_prefs[creation_date] = {"relative_path":relative_path,
                                                    "selected": old_prefs[creation_date]["selected"]}
                    else:
                        new_prefs[creation_date] = {"relative_path":relative_path,
                                                    "selected": False}

                    checkbox = QCheckBox(relative_path)
                    checkbox.setProperty("creation_date", creation_date)
                    checkbox.setChecked(new_prefs[creation_date]["selected"])
                    checkbox.stateChanged.connect(self.file_toggled)
                    self.file_checkboxes_layout.addWidget(checkbox)

            self.parent.prefs["pages"] = new_prefs

    def file_toggled(self):
        checkbox = self.sender()
        creation_date = checkbox.property("creation_date")
        new_state = checkbox.isChecked()
        self.parent.prefs["pages"][creation_date]["selected"] = new_state

    def load_settings(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Notebook Settings", "", "JSON Files (*.json);;All Files (*)")
        if fileName:
            with open(fileName, 'r') as file:
                self.parent.prefs = json.load(file)
                self.root_path_input.setText(self.parent.prefs["root_path"])
                self.load_files()

    def save_settings(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Notebook Settings", "", "JSON Files (*.json);;All Files (*)")
        if fileName:
            with open(fileName, 'w') as file:
                json.dump(self.parent.prefs, file, indent=4, sort_keys=True)
