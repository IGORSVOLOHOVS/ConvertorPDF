import datetime
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from loguru import logger
from domain import Document, IConverter

class Worker(QRunnable):
    def __init__(self, converter: IConverter, files: list[Document], output_dir: Path):
        super().__init__()
        self.converter = converter
        self.files = files
        self.output_dir = output_dir
        self.signals = WorkerSignals()

    def run(self):
        total_files = len(self.files)
        for i, doc in enumerate(self.files):
            try:
                counter = f"Файл {i + 1} из {total_files}:"
                file_size_mb = os.path.getsize(doc.path) / (1024 * 1024)
                log_message = f"{counter} {doc.path.name} ({file_size_mb:.2f} МБ)"
                logger.info(log_message)
                self.converter.convert(doc.path, self.output_dir)
            except Exception as e:
                logger.error(f"Сбой при обработке {doc.path.name}: {e}")
            finally:
                progress = int((i + 1) / total_files * 100)
                self.signals.progress.emit(progress)
        self.signals.finished.emit()

class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

class Controller(QObject):
    conversion_started = pyqtSignal()
    conversion_progress = pyqtSignal(int)
    conversion_finished = pyqtSignal(str)
    
    def __init__(self, converter: IConverter):
        super().__init__()
        self.converter = converter
        self.files: list[Document] = []
        self.thread_pool = QThreadPool.globalInstance()

    def add_files(self, paths: list[str]):
        for p in paths:
            self.files.append(Document(path=Path(p)))
    
    def clear_files(self):
        self.files.clear()

    def run_conversion(self):
        if not self.files: return
        self.conversion_started.emit()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = Path(timestamp)
        output_dir.mkdir(exist_ok=True)
        
        worker = Worker(self.converter, list(self.files), output_dir)
        worker.signals.progress.connect(self.conversion_progress.emit)
        worker.signals.finished.connect(lambda: self.on_worker_finish(output_dir))
        self.thread_pool.start(worker)

    def on_worker_finish(self, output_dir: Path):
        abs_path = str(output_dir.resolve())
        QApplication.clipboard().setText(abs_path)
        logger.success(f"Конвертация завершена. Путь скопирован.")
        self.conversion_finished.emit(abs_path)
        self.clear_files()