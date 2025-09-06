from PyQt6.QtWidgets import (QMainWindow, QDockWidget, QTextEdit, QWidget,
                             QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QFileDialog,
                             QProgressBar, QLabel)
from PyQt6.QtCore import Qt, QUrl, QSettings
from PyQt6.QtGui import QDesktopServices, QPainter, QColor

class DropOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    def paintEvent(self, event):
        painter = QPainter(self)
        color = QColor("#50a0f0"); color.setAlpha(80)
        painter.setBrush(color); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller; self.output_path = ""
        self.setWindowTitle("FileFlow Converter")
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #f0f0f0; font-size: 14px; }
            QPushButton { padding: 10px; background-color: #50a0f0; border: none; 
                          border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #60b0f8; }
            QPushButton:disabled { background-color: #555; color: #888; }
            QListWidget { border: 2px dashed #444; border-radius: 5px; }
            QProgressBar { text-align: center; height: 28px; border-radius: 5px; }
            QProgressBar::chunk { background-color: #50a0f0; border-radius: 5px;}
        """)
        self.setAcceptDrops(True)
        self.setup_ui()
        self.setup_logging_dock()
        self.connect_signals()
        self.resize(800, 600)
        self.settings = QSettings("MySoft", "FileConverter")
        self.update_ui_state()

    def setup_ui(self):
        central_widget = QWidget(); layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15); layout.setSpacing(10)
        self.drop_placeholder = QLabel("\n\nПеретащите файлы сюда\n\nили\n")
        self.drop_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_list = QListWidget(); self.file_list.setVisible(False)
        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("Выбрать файлы")
        self.btn_clear = QPushButton("Очистить")
        btn_layout.addWidget(self.btn_select); btn_layout.addWidget(self.btn_clear)
        self.btn_convert = QPushButton("Конвертировать")
        self.progress_bar = QProgressBar(); self.progress_bar.setVisible(False)
        self.btn_open_folder = QPushButton("Открыть папку")
        self.btn_open_folder.setVisible(False)
        layout.addWidget(self.drop_placeholder); layout.addWidget(self.file_list)
        layout.addLayout(btn_layout); layout.addWidget(self.btn_convert)
        layout.addWidget(self.progress_bar); layout.addWidget(self.btn_open_folder)
        self.setCentralWidget(central_widget)
        self.overlay = DropOverlay(self.centralWidget()); self.overlay.hide()

    def setup_logging_dock(self):
        dock = QDockWidget("Logs", self); self.log_view = QTextEdit()
        self.log_view.setReadOnly(True); dock.setWidget(self.log_view)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def connect_signals(self):
        self.btn_select.clicked.connect(self.select_files)
        self.btn_clear.clicked.connect(self.clear_list)
        self.btn_convert.clicked.connect(self.start_conversion)
        self.btn_open_folder.clicked.connect(self.open_output_folder)
        self.controller.conversion_started.connect(self.on_conversion_start)
        self.controller.conversion_progress.connect(self.progress_bar.setValue)
        self.controller.conversion_finished.connect(self.on_conversion_finish)

    def update_ui_state(self):
        has_items = self.file_list.count() > 0
        self.file_list.setVisible(has_items); self.drop_placeholder.setVisible(not has_items)
        self.btn_convert.setEnabled(has_items); self.btn_clear.setEnabled(has_items)

    def select_files(self):
        last_path = self.settings.value("last_path", ".")
        files, _ = QFileDialog.getOpenFileNames(self, "Выбрать файлы", last_path)
        if files: self.settings.setValue("last_path", files[0]); self.add_files_to_list(files)

    def add_files_to_list(self, paths):
        self.file_list.addItems(paths); self.update_ui_state()

    def clear_list(self):
        self.file_list.clear(); self.btn_open_folder.setVisible(False)
        self.update_ui_state()

    def start_conversion(self):
        paths = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        if paths: self.controller.add_files(paths); self.controller.run_conversion()

    def on_conversion_start(self):
        self.progress_bar.setValue(0); self.progress_bar.setVisible(True)
        self.btn_open_folder.setVisible(False); self.set_controls_enabled(False)

    def on_conversion_finish(self, output_path):
        self.progress_bar.setVisible(False); self.file_list.clear()
        self.update_ui_state(); self.set_controls_enabled(True)
        if output_path: self.output_path = output_path; self.btn_open_folder.setVisible(True)

    def set_controls_enabled(self, enabled):
        for btn in [self.btn_select, self.btn_clear, self.btn_convert, self.file_list]:
            btn.setEnabled(enabled)

    def open_output_folder(self): QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_path))
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction(); self.overlay.show()
    def dragLeaveEvent(self, e): self.overlay.hide()
    def dropEvent(self, e):
        urls = [url.toLocalFile() for url in e.mimeData().urls()]
        self.add_files_to_list(urls); self.overlay.hide()
    def resizeEvent(self, e):
        self.overlay.resize(self.centralWidget().size()); super().resizeEvent(e)