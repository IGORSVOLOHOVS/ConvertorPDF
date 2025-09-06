import subprocess
import shutil
from pathlib import Path
from loguru import logger
from domain import IConverter

class UnoconvConverter(IConverter):
    """
    Конвертер, использующий LibreOffice/OpenOffice.
    Работает на Windows, Linux и macOS.
    """
    def convert(self, doc_path: Path, output_dir: Path) -> bool:
        # Если файл уже в формате PDF, просто копируем его
        if doc_path.suffix.lower() == '.pdf':
            shutil.copy(doc_path, output_dir)
            logger.info(f"Файл '{doc_path.name}' уже в PDF, скопирован.")
            return True

        # Проверяем, доступна ли команда unoconv (или soffice)
        if not (shutil.which("unoconv") or shutil.which("soffice")):
            logger.error("Не найден LibreOffice. Установите его и убедитесь, что он добавлен в PATH.")
            raise FileNotFoundError("LibreOffice не найден в системе.")

        output_file = output_dir / f"{doc_path.stem}.pdf"
        
        # Используем unoconv, если он есть, иначе пробуем прямой вызов LibreOffice
        if shutil.which("unoconv"):
            command = ["unoconv", "-f", "pdf", "-o", str(output_file), str(doc_path)]
        else:
            command = [
                "soffice", "--headless", "--convert-to", "pdf",
                "--outdir", str(output_dir), str(doc_path)
            ]

        try:
            # Запускаем процесс конвертации
            result = subprocess.run(
                command, capture_output=True, text=True, check=True, encoding='utf-8'
            )
            logger.debug(f"Вывод LibreOffice: {result.stdout}")
            return output_file.exists()
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка конвертации '{doc_path.name}': {e.stderr}")
            return False
        except FileNotFoundError:
             logger.error("Команда 'soffice' не найдена. Установите LibreOffice.")
             return False


def get_converter() -> IConverter:
    """Фабричная функция, которая возвращает конвертер."""
    logger.info("Выбрана универсальная стратегия конвертации (LibreOffice).")
    return UnoconvConverter()