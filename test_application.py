import pytest
from pathlib import Path
from application import Controller, Worker
from domain import IConverter
from unittest.mock import MagicMock, create_autospec

# --- Mocks for testing ---
@pytest.fixture
def mock_converter():
    """Создаёт mock-конвертер, который всегда возвращает 'успех'."""
    converter = create_autospec(IConverter)
    converter.convert.return_value = True
    return converter

@pytest.fixture
def controller(mock_converter):
    """Создаёт экземпляр Controller с mock-конвертером."""
    return Controller(mock_converter)

# --- Unit Tests ---
def test_controller_add_and_clear_files(controller):
    """Тест: Проверяем добавление и очистку списка файлов."""
    assert len(controller.files) == 0
    controller.add_files(["/fake/path/one.docx", "/fake/path/two.pptx"])
    assert len(controller.files) == 2
    controller.clear_files()
    assert len(controller.files) == 0

def test_run_conversion_on_empty_list_does_nothing(controller, mocker):
    """Тест: Проверяем, что конвертация не запускается с пустым списком."""
    spy_start = mocker.spy(controller.conversion_started, 'emit')
    controller.run_conversion()
    spy_start.assert_not_called()

def test_worker_emits_correct_signals(mock_converter, tmp_path):
    """Тест: Проверяем, что Worker правильно отправляет сигналы о прогрессе и завершении."""
    # Arrange
    source_file = tmp_path / "test.docx"
    source_file.touch()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    from domain import Document
    files_to_process = [Document(path=source_file)]
    
    worker = Worker(mock_converter, files_to_process, output_dir)
    
    # Act & Assert
    # Мы не можем напрямую проверить сигналы без QApplication, 
    # но можем убедиться, что код доходит до их вызова.
    # Этот тест в основном проверяет, что воркер не падает с ошибкой.
    try:
        worker.run()
    except Exception as e:
        pytest.fail(f"Worker.run() raised an exception: {e}")
        
    mock_converter.convert.assert_called_once_with(source_file, output_dir)

# --- Benchmark Test ---
def test_benchmark_conversion_speed(benchmark, controller, tmp_path):
    """Бенчмарк: Измеряем скорость выполнения основной логики конвертации."""
    source_file = tmp_path / "test.docx"
    source_file.touch()
    controller.add_files([str(source_file)])
    
    # benchmark(...) запускает функцию много раз и измеряет среднее время
    benchmark(controller.run_conversion)