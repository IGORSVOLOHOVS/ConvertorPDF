import sys
from PyQt6.QtWidgets import QApplication
from ui import MainWindow
from application import Controller
from infrastructure import get_converter
from logger import setup_logger, qt_handler

if __name__ == "__main__":
    logger = setup_logger()
    app = QApplication(sys.argv)
    
    converter = get_converter()
    controller = Controller(converter)
    window = MainWindow(controller)
    
    qt_handler.message_written.connect(window.log_view.append)
    
    window.showNormal()
    logger.info("Приложение успешно запущено.")
    sys.exit(app.exec())