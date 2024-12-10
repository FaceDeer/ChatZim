import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QVBoxLayout, QWidget, QToolBar, QPushButton, QLabel, QScrollArea, QFileDialog, QDialog, QMenu, QToolButton
from PyQt6.QtGui import QAction, QTextCursor
from PyQt6.QtCore import Qt
import json

from ChatZimFilesDialog import ChatZimFilesDialog
from ChatZimConfigDialog import ChatZimConfigDialog
from OpenAIInterface import queryLLMStreamed

import sys
import traceback

role_info = {"user":{"color":"#ff0000", "name":"User"},
             "assistant":{"color":"#0000ff", "name":"Assistant"}
             }

config_filename = "ChatZim.conf"

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

def get_system_message(context_settings, config):
    file_path_list = []
    for page in context_settings["pages"].items():
        if page[1]["selected"]:
            file_path = os.path.join(context_settings["root_path"], page[1]["relative_path"])
            file_path_list.append(file_path)

    file_path_list.sort()
    context_list = []
    for file_path in file_path_list:
        try:
            with open(file_path, 'r', encoding="utf-8") as file:
                    lines = file.readlines()
                    lines = lines[3:]
                    context_list.append(''.join(lines))
        except:
            print(f"Unable to read file {file_path}")

    message = {
        "role": "system",
        "content": config["system_prompt"] + "\n\n" + "\n\n".join(context_list)
        }
    return message

#Very quick and dirty.
def word_count(context):
    return len(context.split())

# Function to remove the last character from a QTextEdit window
# TODO: improve how the chat window is managed so that hacky things like this
# aren't needed.
def remove_last_character(text_edit):
    cursor = text_edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter, QTextCursor.MoveMode.KeepAnchor)
    cursor.removeSelectedText()
    text_edit.setTextCursor(cursor)

from PyQt6.QtCore import QThread, pyqtSignal, QObject
class WorkerStreamed(QObject):
    new_token = pyqtSignal(dict)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, messages, config):
        super().__init__()
        self.messages = messages
        self.config = config

    def run(self):
        try:
            for llm_response in queryLLMStreamed(self.messages, self.config):
                if llm_response is None:
                    break
                self.new_token.emit(llm_response)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat with Zim")
        self.resize(800, 600)

        try:
            with open(config_filename) as file:
                self.config = json.load(file)
        except IOError as error: 
            self.config = {
                "response_limit": 1024,
                "api_url": "http://localhost:5001/v1/chat/completions",
                "api_key": "",
                "organization_id": "",
                "project_id": "",
                "model": "",
                "system_prompt": ("You are a helpful assistant."
                    " You will be answering questions regarding"
                    " the following source material:")
            }

        try:
            with open(self.config.get("default_pages")) as default_pages:
                self.context_settings = json.load(default_pages)
        except:
            self.context_settings = {"pages":{}, "root_path":None, "name":None}

        self.messages = [get_system_message(self.context_settings, self.config)]

        # Main layout
        layout = QVBoxLayout()

        # Toolbar
        toolbar = QToolBar("Commands")
        self.addToolBar(toolbar)

        # DocumentSets action
        select_pages_action = QAction("Select Pages", self)
        select_pages_action.triggered.connect(self.open_docsets_dialog)
        toolbar.addAction(select_pages_action)

        update_context_action = QAction("Update Context", self)
        update_context_action.triggered.connect(self.update_documents)
        toolbar.addAction(update_context_action)

        export_context_action = QAction("Export Context", self)
        export_context_action.triggered.connect(self.export_context)
        toolbar.addAction(export_context_action)

        conversation_menu = QMenu("Conversation", self)

        save_conversation_action = QAction("Save", self)
        save_conversation_action.triggered.connect(self.save_conversation)
        conversation_menu.addAction(save_conversation_action)
        
        load_conversation_action = QAction("Load", self)
        load_conversation_action.triggered.connect(self.load_conversation)
        conversation_menu.addAction(load_conversation_action)

        new_conversation_action = QAction("New", self)
        new_conversation_action.triggered.connect(self.new_conversation)
        conversation_menu.addAction(new_conversation_action)

        # Create a tool button and set the menu
        conversation_tool_button = QToolButton()
        conversation_tool_button.setText("Conversation")
        conversation_tool_button.setMenu(conversation_menu)
        conversation_tool_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        conversation_tool_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        toolbar.addWidget(conversation_tool_button) 

        back_conversation_action = QAction("Undo Last Response", self)
        back_conversation_action.triggered.connect(self.roll_back)
        toolbar.addAction(back_conversation_action)

        configure_action = QAction("Configure", self)
        configure_action.triggered.connect(self.open_config_dialog)
        toolbar.addAction(configure_action)
        
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

    def add_message(self, message):
        self.messages.append(message)
        self.add_message_to_chat_display(message)

    def add_message_to_chat_display(self, message):
        current_role = role_info[message["role"]]
        content = message["content"].replace("\n", "<br>")
        formatted_message = f'<b><span style="color:{current_role["color"]};">{current_role["name"]}:</span></b> {content}<br>'
        self.chat_display.append(formatted_message)

    def append_token(self, token):
        self.messages[-1]["content"] = self.messages[-1]["content"] + token
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(token)
        self.chat_display.setTextCursor(cursor)

    def handle_return_pressed(self):
        user_text = self.text_input.text()
        self.text_input.clear()
        
        user_message = {"role": "user", "content": user_text}
        self.add_message(user_message)
        assistant_message = {"role": "assistant", "content": ""}
        self.add_message(assistant_message)
        remove_last_character(self.chat_display) # gets rid of the line return that add_message adds

        self.text_input.setDisabled(True)  # Disable the input field
        self.text_input.setText("(Processing prompt...)")

        self.thread = QThread()
        self.worker = WorkerStreamed(self.messages, self.config)
        self.worker.moveToThread(self.thread)

        self.worker.new_token.connect(self.on_llm_response)
        self.worker.finished.connect(self.on_llm_response_complete)
        self.worker.error.connect(self.on_llm_error)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def on_llm_response(self, response):
        self.append_token(response["choices"][0]["delta"]["content"])
        if self.text_input.text() != "(Responding...)":
            self.text_input.setText("(Responding...)")

    def on_llm_response_complete(self):
        self.chat_display.append("") # add a line break after LLM response
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

    def open_docsets_dialog(self):
        self.docsets_dialog = ChatZimFilesDialog(self)
        self.docsets_dialog.finished.connect(self.update_documents)
        self.docsets_dialog.exec()

    def update_documents(self):
        enabled = 0
        total = 0
        for pages in self.context_settings["pages"].items():
            if pages[1]["selected"]:
                enabled = enabled + 1
            total = total + 1
        self.messages[0] = get_system_message(self.context_settings, self.config)
        words = word_count(self.messages[0]["content"])
        self.header_label.setText(f'{self.context_settings["name"]}: {enabled}/{total} pages selected, {words} words in context')

    def export_context(self):
        system_message = get_system_message(self.context_settings, self.config)
        fileName, _ = QFileDialog.getSaveFileName(self, "Export Context", "", "TXT Files (*.txt);;All Files (*)")
        if fileName:
            with open(fileName, 'w', encoding="utf-8") as file:
                file.write(self.messages[0]["content"])

    def open_config_dialog(self):
        self.config_dialog = ChatZimConfigDialog(self)
        if self.config_dialog.exec() == QDialog.DialogCode.Accepted:
            self.update_documents()
            with open(config_filename, "w") as writefile:
                json.dump(self.config, writefile, indent=4, sort_keys=True)

    def save_conversation(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Conversation", "", "CONV Files (*.conv);;All Files (*)")
        if fileName:
            with open(fileName, 'w') as file:
                #omit the system message at the beginning.
                json.dump(self.messages[1:], file, indent=4, sort_keys=True)

    def load_conversation(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Conversation", "", "CONV Files (*.conv);;All Files (*)")
        if fileName:
            with open(fileName, 'r') as file:
                self.chat_display.clear()
                messages = json.load(file)
                self.messages = [get_system_message(self.context_settings, self.config)]
                for message in messages:
                    self.add_message(message)

    def new_conversation(self):
        self.chat_display.clear()
        self.messages = [get_system_message(self.context_settings, self.config)]

    def roll_back(self):
        if len(self.messages) >= 3:
            self.messages.pop() #delete last response
            user_message = self.messages.pop()
            self.text_input.setText(user_message["content"])
            self.chat_display.clear()
            for message in self.messages[1:]:
                self.add_message_to_chat_display(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
