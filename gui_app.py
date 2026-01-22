import sys
import os
import signal
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QTabWidget, 
                             QSystemTrayIcon, QMenu, QMessageBox, QLabel, QStyle)
from PySide6.QtCore import QProcess, QUrl, Qt, QSize
from PySide6.QtGui import QIcon, QAction, QTextCursor
from PySide6.QtWebEngineWidgets import QWebEngineView
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SERVER_PORT = os.getenv('SERVER_PORT', '5000')

class ServerThread(QProcess):
    """
    Manages the Flask server process.
    """
    def __init__(self):
        super().__init__()
        self.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
    def start_server(self):
        # Set environment variables for the subprocess
        env = os.environ.copy()
        env['FLASK_DEBUG'] = '0' # Disable debug mode for production-like behavior
        
        # PySide6 QProcess.setEnvironment takes a list of strings "KEY=VALUE"
        # unlike PyQt6 which might take a dict or list depending on version.
        # But QProcess.setEnvironment in Qt6 takes QProcessEnvironment usually.
        # Using setProcessEnvironment is safer if available, but setEnvironment is deprecated.
        # Let's use simple list of strings for compatibility if needed, 
        # or better, simply let it inherit environment and only modify what we need.
        
        # Actually, QProcess in PySide6 inherits env by default.
        # If we want to set env, we should use setProcessEnvironment.
        from PySide6.QtCore import QProcessEnvironment
        q_env = QProcessEnvironment.systemEnvironment()
        q_env.insert('FLASK_DEBUG', '0')
        self.setProcessEnvironment(q_env)
        
        # Determine python executable
        python_exe = sys.executable
        
        # Start the server process (app.py)
        # -u: Unbuffered binary stdout and stderr
        self.start(python_exe, ['-u', 'app.py'])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Remote Chat Server Manager")
        self.resize(1024, 768)
        
        # --- UI Components ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Tab 1: Web Interface
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(f"http://minces.iptime.org:9000"))
        self.tabs.addTab(self.web_view, "Web Interface")
        
        # Tab 2: Log Console
        self.log_widget = QWidget()
        self.log_layout = QVBoxLayout(self.log_widget)
        
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc; font-family: Consolas, monospace;")
        self.log_layout.addWidget(self.log_console)
        
        # Log Controls
        self.log_controls_layout = QHBoxLayout()
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.log_console.clear)
        self.log_controls_layout.addWidget(self.clear_log_btn)
        self.log_controls_layout.addStretch()
        self.log_layout.addLayout(self.log_controls_layout)
        
        self.tabs.addTab(self.log_widget, "Server Log")
        
        # Bottom Control Panel
        self.bottom_panel = QHBoxLayout()
        self.status_label = QLabel("Server Status: Starting...")
        self.status_label.setStyleSheet("font-weight: bold; color: orange;")
        self.bottom_panel.addWidget(self.status_label)
        
        self.bottom_panel.addStretch()
        
        self.refresh_btn = QPushButton("Refresh Web View")
        self.refresh_btn.clicked.connect(self.web_view.reload)
        self.bottom_panel.addWidget(self.refresh_btn)
        
        self.quit_btn = QPushButton("Quit Application")
        self.quit_btn.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
        self.quit_btn.clicked.connect(self.quit_application)
        self.bottom_panel.addWidget(self.quit_btn)
        
        self.main_layout.addLayout(self.bottom_panel)
        
        # --- System Tray ---
        self.setup_tray_icon()
        
        # --- Server Process ---
        self.server_process = ServerThread()
        self.server_process.readyReadStandardOutput.connect(self.handle_stdout)
        self.server_process.readyReadStandardError.connect(self.handle_stderr) # Though merged, kept for safety
        self.server_process.started.connect(self.server_started)
        self.server_process.finished.connect(self.server_finished)
        self.server_process.start_server()

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use a standard system icon
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        # Tray Menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Minimize to Tray", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show_window()

    def show_window(self):
        self.show()
        self.setWindowState(Qt.WindowState.WindowActive)
        self.activateWindow()

    def closeEvent(self, event):
        # Override close event to minimize instead of quitting
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Remote Chat Manager",
            "Application minimized to tray.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def handle_stdout(self):
        data = self.server_process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")
        self.append_log(text)

    def handle_stderr(self):
        data = self.server_process.readAllStandardError()
        text = bytes(data).decode("utf-8", errors="replace")
        self.append_log(text)
        
    def append_log(self, text):
        cursor = self.log_console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_console.setTextCursor(cursor)
        self.log_console.insertPlainText(text)
        self.log_console.ensureCursorVisible()

    def server_started(self):
        self.status_label.setText("Server Status: Running")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        self.append_log(f"--- Server Process Started on Port {SERVER_PORT} ---\n")

    def server_finished(self):
        self.status_label.setText("Server Status: Stopped")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        self.append_log("\n--- Server Process Stopped ---\n")

    def quit_application(self):
        reply = QMessageBox.question(self, 'Confirm Quit',
                                     "Are you sure you want to completely stop the server and exit?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.status_label.setText("Stopping Server...")
            # Kill the server process
            if self.server_process.state() == QProcess.ProcessState.Running:
                self.server_process.kill() 
                self.server_process.waitForFinished(3000)
            
            QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())