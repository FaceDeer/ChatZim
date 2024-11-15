import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QVBoxLayout, QWidget, QToolBar, QPushButton, QLabel, QScrollArea
from PyQt6.QtGui import QAction

from ChatZimFilesDialog import ChatZimFilesDialog
from OpenAIInterface import queryLLM

import sys
import traceback
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

def get_context(prefs):
    context_list = []
    for page in prefs["pages"].items():
        if page[1]["selected"]:
            file_path = os.path.join(prefs["root_path"], page[1]["relative_path"])
            with open(file_path, 'r', encoding="utf-8") as file:
                lines = file.readlines()
                lines = lines[3:]
                context_list.append(''.join(lines))
    return context_list


from PyQt6.QtCore import QThread, pyqtSignal, QObject
class Worker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    def run(self):
        try:
            llm_response = queryLLM(self.messages)
            if llm_response:
                self.finished.emit(llm_response)
            else:
                self.error.emit("Error getting LLM response")
        except Exception as e:
            self.error.emit(str(e))


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat with Zim")
        self.resize(800, 600)

        self.prefs = {"pages":{}, "root_path":None, "name":None}

        self.system_message = {
            "role": "system",
            "content": "You are a helpful assistant."
        }
        self.messages = [self.system_message]

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

        self.update_documents()

#    def closeEvent(self, event):
#        with open("ChatZim.json", "w") as writefile:
#            json.dump(self.prefs, writefile, indent=4, sort_keys=True)
#        event.accept()

    def add_message(self, role, text, colour):
        text = text.replace("\n", "<br>")
        formatted_message = f'<b><span style="color:{colour};">{role}:</span></b> {text}<br>'
        self.chat_display.append(formatted_message)

    def handle_return_pressed(self):
        user_text = self.text_input.text()
        self.text_input.clear()
        self.add_message("User", user_text, "#ff0000")

        user_message = {"role": "user", "content": user_text}
        self.messages.append(user_message)

        self.text_input.setDisabled(True)  # Disable the input field
        self.text_input.setText("(Working...)")

        self.thread = QThread()
        self.worker = Worker(self.messages)
        self.worker.moveToThread(self.thread)
        
        self.worker.finished.connect(self.on_llm_response)
        self.worker.error.connect(self.on_llm_error)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def on_llm_response(self, response):
        self.messages.append(response)
        self.add_message("LLM", response['content'], "#0000ff")
        self.text_input.setDisabled(False)  # Re-enable the input field
        self.text_input.setText("")
        self.thread.quit()
        self.thread.wait()
        self.thread = None

    def on_llm_error(self, error_message):
        self.chat_display.append(f"\n{error_message}")
        self.text_input.setDisabled(False)  # Re-enable the input field
        self.text_input.setText("")
        self.thread.quit()
        self.thread.wait()
        self.thread = None

    def get_llm_response(self, message):
        # Placeholder for the function that interacts with the LLM
        return "This is a response from the LLM."

    def open_docsets_dialog(self):
        self.docsets_dialog = ChatZimFilesDialog(self)
        self.docsets_dialog.finished.connect(self.update_documents)
        self.docsets_dialog.exec()

    def update_documents(self):
        enabled = 0
        total = 0
        for pages in self.prefs["pages"].items():
            if pages[1]["selected"]:
                enabled = enabled + 1
            total = total + 1
        self.header_label.setText(f'Zim wiki: {self.prefs["name"]} ({enabled}/{total} pages selected)')
        context = get_context(self.prefs)

        self.system_message["content"] = (
            "You are a helpful assistant."
            " You will be answering questions regarding"
            " the following source material:\n") + "\n\n".join(context)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
