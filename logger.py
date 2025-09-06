import sys
from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal

class QtSignalHandler(QObject):
    message_written = pyqtSignal(str)
    def write(self, message):
        self.message_written.emit(message.strip())

def setup_logger():
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level: <7} | {message}")
    logger.add(qt_handler, level="INFO", format="{message}")
    logger.add(
        "logs/app_{time:YYYY-DD-MM}.log",
        rotation="100 MB",
        retention="10 days",
        serialize=True,
        enqueue=True,
    )
    return logger

qt_handler = QtSignalHandler()