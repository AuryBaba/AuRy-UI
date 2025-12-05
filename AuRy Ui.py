import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette, QMouseEvent
from PyQt5.QtCore import Qt, QProcess, QPoint

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class AuRyTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)  
        self.resize(1200, 700)
        self.setMouseTracking(True)

       
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(35, 35, 35))  
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self.dragPos = QPoint()
        self.current_path = os.getcwd()
        self.command_history = []
        self.history_index = -1
        self.current_command = ""
        self.admin_mode = is_admin()
        self.process_running = False

        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.process_finished)

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2,2,2,2)
        main_layout.setSpacing(0)

        
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("background-color: #2E2E2E;")  
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(10,0,10,0)

        self.title_label = QLabel("AuRy-UI")
        self.title_label.setStyleSheet("color: #AAAAAA; font-weight:bold;")  
        self.title_label.setFont(QFont("Consolas", 12))
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(25,25)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E2E2E;
                color: #AAAAAA;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        title_bar.setLayout(title_layout)
        main_layout.addWidget(title_bar)

        # Terminal alanı
        self.terminal = QTextEdit()
        self.terminal.setFont(QFont("Consolas", 12))
        self.terminal.setStyleSheet("""
            QTextEdit {
                background-color: black;
                color: #00c8ff;
                border: none;
            }
        """)
        self.terminal.installEventFilter(self)
        self.terminal.setUndoRedoEnabled(False)
        main_layout.addWidget(self.terminal)

        self.setLayout(main_layout)
        self.print_prompt()

   
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.dragPos)
            event.accept()

    def print_prompt(self):
        try:
            username = os.getlogin()
        except:
            username = "Unknown"

        if self.admin_mode:
            prompt = f"┌──(root㉿{username})-[{self.current_path}]\n└─# "
        else:
            prompt = f"┌──(user㉿{username})-[{self.current_path}]\n└─$ "

        self.prompt = prompt
        self.terminal.moveCursor(QTextCursor.End)
        self.terminal.insertPlainText(prompt)
        self.terminal.moveCursor(QTextCursor.End)

    def eventFilter(self, obj, event):
        if obj is self.terminal and event.type() == event.KeyPress:
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
                if self.process_running:
                    self.process.kill()
                    self.process_running = False
                    self.terminal.insertPlainText("^C\n")
                    self.print_prompt()
                else:
                    self.terminal.copy()
                return True
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
                paste_text = QApplication.clipboard().text()
                self.current_command += paste_text
                self.terminal.insertPlainText(paste_text)
                return True
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_L:
                self.terminal.clear()
                self.current_command = ""
                self.print_prompt()
                return True
            if event.key() == Qt.Key_Return:
                self.run_command()
                return True
            if event.key() == Qt.Key_Up:
                if self.command_history:
                    self.history_index = max(0, self.history_index - 1)
                    self.replace_current(self.command_history[self.history_index])
                return True
            if event.key() == Qt.Key_Down:
                if self.command_history:
                    self.history_index = min(len(self.command_history)-1, self.history_index+1)
                    self.replace_current(self.command_history[self.history_index])
                return True
            if event.key() == Qt.Key_Backspace:
                if len(self.current_command) > 0:
                    self.current_command = self.current_command[:-1]
                    cursor = self.terminal.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    cursor.deletePreviousChar()
                return True
            if event.text():
                self.current_command += event.text()
                self.terminal.insertPlainText(event.text())
                return True
        return False

    def replace_current(self, text):
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.End)
        for _ in range(len(self.current_command)):
            cursor.deletePreviousChar()
        self.current_command = text
        self.terminal.insertPlainText(text)

    def run_command(self):
        if self.process_running:
            self.terminal.insertPlainText("Hata: Önce mevcut işlemi bitirin veya Ctrl+C ile iptal edin.\n")
            self.print_prompt()
            return

        cmd = self.current_command.strip()
        self.terminal.insertPlainText("\n")

        if cmd:
            self.command_history.append(cmd)
        self.history_index = len(self.command_history)

        if cmd.startswith("cd "):
            try:
                os.chdir(cmd[3:].strip())
                self.current_path = os.getcwd()
            except Exception as e:
                self.terminal.insertPlainText(f"Hata: {e}\n")
        else:
            self.process_running = True
            self.process.setWorkingDirectory(self.current_path)
            self.process.start("cmd.exe", ["/c", cmd])

        self.current_command = ""
        self.terminal.insertPlainText("\n")

        if not self.process_running:
            self.print_prompt()

    def handle_output(self):
        data = self.process.readAllStandardOutput().data()
        text = data.decode("cp850", errors="ignore")
        self.terminal.moveCursor(QTextCursor.End)
        self.terminal.insertPlainText(text)
        self.terminal.moveCursor(QTextCursor.End)

    def process_finished(self):
        self.process_running = False
        self.print_prompt()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AuRyTerminal()
    win.show()
    sys.exit(app.exec_())
