import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QPushButton, QMessageBox
)
from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression

class ChatZimConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = parent.config

        self.setWindowTitle("Configuration Settings")

        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.response_limit = QLineEdit()
        self.response_limit.setValidator(QIntValidator(1, 2147483647, self))
        form_layout.addRow("Response limit:", self.response_limit)

        self.api_url = QLineEdit()
        url_regex = QRegularExpression(r"(https?|ftp)://[^\s/$.?#].[^\s]*")
        self.api_url.setValidator(QRegularExpressionValidator(url_regex, self))
        form_layout.addRow("API URL:", self.api_url)

        self.api_key = QLineEdit()
        form_layout.addRow("API Key:", self.api_key)

        self.organization_id = QLineEdit()
        form_layout.addRow("Organization ID:", self.organization_id)

        self.project_id = QLineEdit()
        form_layout.addRow("Project ID:", self.project_id)

        self.model = QLineEdit()
        form_layout.addRow("Model:", self.model)

        self.system_prompt = QTextEdit()
        form_layout.addRow("System Prompt:", self.system_prompt)

        layout.addLayout(form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_config)
        layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

        self.load_config()

    def load_config(self):
        self.response_limit.setText(str(self.config.get("response_limit", "")))
        self.api_url.setText(self.config.get("api_url", ""))
        self.api_key.setText(self.config.get("api_key", ""))
        self.organization_id.setText(self.config.get("organization_id", ""))
        self.project_id.setText(self.config.get("project_id", ""))
        self.model.setText(self.config.get("model", ""))
        self.system_prompt.setPlainText(self.config.get("system_prompt", ""))

    def save_config(self):
        try:
            if not self.response_limit.text().isdigit() or int(self.response_limit.text()) <= 0:
                raise ValueError("Response limit must be a positive integer.")
            self.config["response_limit"] = int(self.response_limit.text())
            self.config["api_url"] = self.api_url.text()
            self.config["api_key"] = self.api_key.text()
            self.config["organization_id"] = self.organization_id.text()
            self.config["project_id"] = self.project_id.text()
            self.config["model"] = self.model.text()
            self.config["system_prompt"] = self.system_prompt.toPlainText()
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))