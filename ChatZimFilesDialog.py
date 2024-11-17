import os
from PyQt6.QtWidgets import QLineEdit, QVBoxLayout, QWidget, QPushButton, QDialog, QCheckBox, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout, QFileDialog, QSpacerItem, QSizePolicy
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

def count_words_in_file(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        lines = file.readlines()
        lines = lines[3:]
        return len(''.join(lines).split())

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
        self.root_path = QLabel("Load a Zim notebook")
        top_layout.addWidget(self.root_path)
        load_files_button = QPushButton("Load Notebook")
        load_files_button.clicked.connect(self.load_notebook)
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

        load_button = QPushButton("Load Page Selection")
        load_button.clicked.connect(self.load_settings)
        bottom_layout.addWidget(load_button)

        save_button = QPushButton("Save Page Selection")
        save_button.clicked.connect(self.save_settings)
        bottom_layout.addWidget(save_button)

        close_button = QPushButton("Update Context")
        close_button.clicked.connect(self.close)
        bottom_layout.addWidget(close_button)

        main_layout.addLayout(bottom_layout)
        
        selected_notebook = parent.context_settings.get("root_path")
        if selected_notebook:
            self.root_path.setText(f"Notebook Path: {selected_notebook}")
            self.load_files()
        else:
            self.root_path.setText("Load a Zim notebook")

        self.setLayout(main_layout)

    def load_files(self):
        root_path = self.parent.context_settings["root_path"]
        if not os.path.isdir(root_path):
            return
        name = extract_name_from_ini(root_path)
        if name is None:
            return

        clearLayout(self.file_checkboxes_layout)

        self.parent.context_settings["root_path"] = root_path
        self.parent.context_settings["name"] = name
        
        old_context_settings = self.parent.context_settings["pages"]
        new_context_settings = {}
        self.parent.context_settings["pages"] = new_context_settings

        checkboxes = []
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, root_path)
                    creation_date = get_creation_date_in_seconds(file_path)
                    if creation_date is None:
                        print(relative_path + " had no creation date")
                        continue
                    if creation_date in new_context_settings:
                        print(relative_path + " has an identical creation date to " + new_context_settings[creation_date]["relative_path"])
                        continue

                    #TODO simplify
                    if creation_date in old_context_settings:
                        new_context_settings[creation_date] = {"relative_path":relative_path,
                                                    "selected": old_context_settings[creation_date]["selected"]}
                    else:
                        new_context_settings[creation_date] = {"relative_path":relative_path,
                                                    "selected": False}

                    checkbox_container = QWidget()
                    layout = QHBoxLayout(checkbox_container)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.setSpacing(5)
        
                    # Checkbox for the file
                    checkbox = QCheckBox(relative_path)
                    checkbox.setProperty("creation_date", creation_date)
                    checkbox.setChecked(new_context_settings[creation_date]["selected"])
                    checkbox.stateChanged.connect(self.file_toggled)

                    # Spacer item to push the label to the right
                    spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
         
                    # Label for the word count
                    word_count_label = QLabel(f"{count_words_in_file(file_path)} words")
        
                    # Add the checkbox and word count label to the layout
                    layout.addWidget(checkbox)
                    layout.addItem(spacer)
                    layout.addWidget(word_count_label)

                    checkboxes.append(checkbox_container)

        #Sort the files by name
        checkboxes.sort(key=lambda cb:cb.layout().itemAt(0).widget().text())
        for checkbox_container in checkboxes:
            self.file_checkboxes_layout.addWidget(checkbox_container)

        #Add a spacer at the bottom to push the contents to the top.
        self.file_checkboxes_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def file_toggled(self):
        checkbox = self.sender()
        creation_date = checkbox.property("creation_date")
        new_state = checkbox.isChecked()
        self.parent.context_settings["pages"][creation_date]["selected"] = new_state

    def load_notebook(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Notebook", "", "ZIM Files (*.zim);;All Files (*)")
        if fileName:
            root = os.path.split(fileName)[0]
            self.root_path.setText(f"Notebook Path: {root}")
            self.parent.context_settings["root_path"] = root
            self.load_files()
            

    def load_settings(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Load ChatZim Settings", "", "PAGES Files (*.pages);;All Files (*)")
        if fileName:
            with open(fileName, 'r') as file:
                self.parent.context_settings = json.load(file)
                self.root_path.setText(f"Notebook Path: {self.parent.context_settings['root_path']}")
                self.load_files()

    def save_settings(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save ChatZim Settings", "", "PAGES Files (*.pages);;All Files (*)")
        if fileName:
            with open(fileName, 'w') as file:
                json.dump(self.parent.context_settings, file, indent=4, sort_keys=True)
