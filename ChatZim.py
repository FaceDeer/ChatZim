import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QVBoxLayout, QWidget, QToolBar, QPushButton, QLabel, QScrollArea
from PyQt6.QtGui import QAction
import json

from ChatZimFilesDialog import ChatZimFilesDialog

import sys
"""
Handle exceptions by displaying the traceback on sys.stderr.

Args:
    exc_type (type): The type of the exception being handled.
    exc_value (BaseException): The exception instance being handled.
    exc_tb (TracebackType): The traceback object associated with the exception.

Raises:
    None.
"""
def excepthook(exc_type, exc_value, exc_tb):
    # Format the traceback and the exception information
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    # Print the caught exception and the traceback
    print("caught:", tb)

    # Call the original excepthook function
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = excepthook

def get_context(prefs, notebook_root):
    context_list = []
    if notebook_root in prefs["notebook"]:
        for page in prefs["notebook"][notebook_root].items():
            if page[1]["selected"]:
                file_path = os.path.join(notebook_root, page[1]["relative_path"])
                with open(file_path, 'r', encoding="utf-8") as file:
                    lines = file.readlines()
                    lines = lines[3:]
                    context_list.append(''.join(lines))
    return context_list

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat with Zim")
        self.resize(800, 600)

        try:
            with open("ChatZim.json", 'r') as f:
                self.prefs = json.load(f)
        except:
            self.prefs = {"notebook":{}, "selected_notebook":None, "selected_name":None}

        # Main layout
        layout = QVBoxLayout()

        # Toolbar
        toolbar = QToolBar("Configuration")
        self.addToolBar(toolbar)

        # DocumentSets action
        docsets_action = QAction("Select Pages", self)
        docsets_action.triggered.connect(self.open_docsets_dialog)
        toolbar.addAction(docsets_action)

        self.header_label = QLabel()
        layout.addWidget(self.header_label)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Text input
        self.text_input = QLineEdit()
        self.text_input.returnPressed.connect(self.handle_return_pressed)
        layout.addWidget(self.text_input)

        # Central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_header_label()

    def closeEvent(self, event):
        with open("ChatZim.json", "w") as writefile:
            json.dump(self.prefs, writefile, indent=4, sort_keys=True)
        event.accept()

    def handle_return_pressed(self):
        user_message = self.text_input.text()
        self.text_input.clear()

        # Display user message
        self.chat_display.append(f"User: {user_message}")

        # Placeholder for LLM response
        llm_response = self.get_llm_response(user_message)

        # Display LLM response
        self.chat_display.append(f"LLM: {llm_response}")

    def get_llm_response(self, message):
        # Placeholder for the function that interacts with the LLM
        return "This is a response from the LLM."

    def open_docsets_dialog(self):
        self.docsets_dialog = ChatZimFilesDialog(self)
        self.docsets_dialog.finished.connect(self.update_header_label)
        self.docsets_dialog.exec()

    def update_header_label(self):
        enabled = 0
        total = 0
        if self.prefs["selected_notebook"] and self.prefs["selected_notebook"] in self.prefs["notebook"]:
            notebook = self.prefs["notebook"][self.prefs["selected_notebook"]]
            for pages in notebook.items():
                if pages[1]["selected"]:
                    enabled = enabled + 1
                total = total + 1
        self.header_label.setText(f'{self.prefs["selected_name"]} ({enabled}/{total} pages selected)')
        self.context = get_context(self.prefs, self.prefs["selected_notebook"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
