# Спецификация требований: ConvertorPDF (FileFlow Converter)

Восстановлена по коду коммита `2ba4388` 2026-11-18. Описывает то, что реализовано;
обещания README без кода вынесены в раздел 3.8. Обзор проекта:
[`docs/README.md`](docs/README.md).

<!-- jira-sync:start -->
Jira: KAN-124

## Tasks

This list is one ticket in Jira project KAN, [KAN-124](https://igorsvolohovs.atlassian.net/browse/KAN-124). Each line is a checkbox there: tick it in Jira and the sync ticks it here; add a checkbox there and it is appended here. Done items are the features described in section 3; open items are what the project declares but the code does not do yet.

- [x] Запуск (section 3.1) <!-- spec-c001fc7717 -->
- [x] Список файлов (section 3.2) <!-- spec-287849888b -->
- [x] Запуск конвертации (section 3.3) <!-- spec-1b9e52dacf -->
- [x] Обработка файлов (section 3.4) <!-- spec-2698b19194 -->
- [x] Завершение (section 3.5) <!-- spec-be19888666 -->
- [x] Конвертер (section 3.6) <!-- spec-30d9c5795b -->
- [x] Журнал (section 3.7) <!-- spec-67ade741ae -->
- [ ] `OfficeConverter` через COM для Microsoft Office на Windows (declared, not implemented) <!-- spec-officeconverter-com-microsoft-office-windows -->
- [ ] «Фабричная функция определяет ОС» (declared, not implemented) <!-- spec-1e47602022 -->
- [ ] Приложение «drives Microsoft Office» (declared, not implemented) <!-- spec-drives-microsoft-office -->
- [ ] Форматы `.docx`, `.pptx`, `.doc`, `.ppt` (declared, not implemented) <!-- spec-docx-pptx-doc-ppt -->
- [ ] Настройки логирования из `config/settings.yaml` (declared, not implemented) <!-- spec-config-settings-yaml -->
- [ ] «Сохраняет настройки интерфейса» (declared, not implemented) <!-- spec-68552bab05 -->
- [ ] Статус документа (declared, not implemented) <!-- spec-4d2ba1ad73 -->
- [ ] Признак успеха `convert() -> bool` (declared, not implemented) <!-- spec-convert-bool -->
- [ ] Зависимости `PyYAML`, `pywin32-ctypes`, `pytest-mock` (declared, not implemented) <!-- spec-pyyaml-pywin32-ctypes-pytest-mock -->

<!-- jira-sync:end -->

## 1. Назначение и границы

Настольное GUI-приложение, которое переводит выбранные пользователем файлы в PDF
с помощью LibreOffice и складывает результаты в новый каталог с меткой времени.

В границах:

- выбор файлов диалогом и перетаскиванием (`ui.py`);
- последовательная конвертация в фоновом потоке (`application.py`);
- вызов `unoconv` или `soffice --headless`, копирование готовых PDF
  (`infrastructure.py`);
- журнал в stderr, в окно и в файлы (`logger.py`).

Вне границ (в коде нет): конвертация через Microsoft Office, обратное
преобразование из PDF, слияние или редактирование PDF, сетевые функции, работа
без GUI.

## 2. Контекст

| Элемент | Описание | Источник |
| --- | --- | --- |
| Пользователь | человек за настольным компьютером; кто именно — не сказано | `ui.py` |
| LibreOffice | внешняя программа, `unoconv` или `soffice` в PATH | `infrastructure.py:20-33` |
| Файловая система | входные файлы; каталоги результатов и `logs/` в текущем рабочем каталоге | `application.py:58-60`, `logger.py:15` |
| Буфер обмена ОС | получает путь каталога результатов | `application.py:69` |
| Хранилище `QSettings` | ключ `last_path` | `ui.py:37`, `ui.py:80-82` |
| Файловый менеджер ОС | открывается через `QDesktopServices.openUrl` | `ui.py:108` |
| Среда выполнения | CPython с PyQt6 и loguru; в CI — Windows, Python 3.13 | `requirements.txt`, `.github/workflows/python-ci.yml` |

## 3. Функциональные требования

### 3.1 Запуск

**FR-1.** Система должна при запуске настроить логгер, получить конвертер из
`get_converter()`, создать `Controller` и `MainWindow`, направить сообщения
логгера в панель «Logs» и показать окно размером 800×600.
Источник: `main.py:9-19`, `ui.py:36`. Проверка: нет теста.

### 3.2 Список файлов

**FR-2.** Система должна по кнопке «Выбрать файлы» открывать диалог выбора
нескольких файлов без фильтра типов с начальным путём из `last_path`
(по умолчанию `.`) и сохранять в `last_path` путь первого выбранного файла.
Источник: `ui.py:79-82`. Проверка: нет теста.

**FR-3.** Система должна принимать перетаскиваемые в окно объекты с URL, добавлять
их локальные пути в список и на время перетаскивания закрывать центральную область
полупрозрачным оверлеем цвета `#50a0f0`.
Источник: `ui.py:7-15`, `ui.py:109-116`. Проверка: нет теста.

**FR-4.** Система должна показывать список только при наличии элементов, иначе
надпись «Перетащите файлы сюда», и включать кнопки «Конвертировать» и «Очистить»
только при непустом списке.
Источник: `ui.py:74-77`. Проверка: нет теста.

**FR-5.** Система должна по кнопке «Очистить» очищать список и скрывать кнопку
«Открыть папку».
Источник: `ui.py:87-89`. Проверка: нет теста.

**FR-6.** Система должна в `Controller.add_files` создавать `Document` на каждый
путь, а в `Controller.clear_files` очищать список.
Источник: `application.py:48-53`. Проверка: `test_controller_add_and_clear_files`.

### 3.3 Запуск конвертации

**FR-7.** Система должна при пустом списке завершать `run_conversion` без
каких-либо действий и без сигнала `conversion_started`.
Источник: `application.py:56`. Проверка: `test_run_conversion_on_empty_list_does_nothing`.

**FR-8.** Система должна при непустом списке испускать `conversion_started`,
создавать (если нет) каталог с именем `%Y-%m-%d_%H-%M-%S` в текущем рабочем
каталоге и запускать `Worker` с копией списка в глобальном `QThreadPool`.
Источник: `application.py:57-65`. Проверка: нет теста (`test_benchmark_conversion_speed`
вызывает метод, но ничего не утверждает).

**FR-9.** Система должна на время конвертации показывать индикатор прогресса с 0,
скрывать «Открыть папку» и блокировать кнопки «Выбрать файлы», «Очистить»,
«Конвертировать» и список.
Источник: `ui.py:95-97`, `ui.py:104-106`. Проверка: нет теста.

### 3.4 Обработка файлов

**FR-10.** Система должна обрабатывать файлы по очереди, для каждого записывать в
лог «Файл i из N: <имя> (<размер> МБ)» с размером до двух знаков и вызывать
`convert(<путь>, <каталог результатов>)`.
Источник: `application.py:17-25`. Проверка: `test_worker_emits_correct_signals`
(только вызов `convert`).

**FR-11.** Система должна перехватывать любое исключение при обработке файла,
писать в лог ошибку с именем файла и переходить к следующему.
Источник: `application.py:26-27`. Проверка: нет теста.

**FR-12.** Система должна после каждого файла, удачного или нет, испускать
прогресс `int((i + 1) / N * 100)`, а после последнего — сигнал `finished`.
Источник: `application.py:28-31`, `ui.py:71`. Проверка: нет теста.

### 3.5 Завершение

**FR-13.** Система должна по завершении копировать абсолютный путь каталога
результатов в буфер обмена, писать в лог сообщение уровня SUCCESS, испускать
`conversion_finished(<путь>)` и очищать список контроллера.
Источник: `application.py:67-72`. Проверка: нет теста.

**FR-14.** Система должна по `conversion_finished` скрывать прогресс, очищать
список, снимать блокировку и показывать кнопку «Открыть папку», открывающую
каталог результатов в файловом менеджере ОС.
Источник: `ui.py:99-102`, `ui.py:108`. Проверка: нет теста.

### 3.6 Конвертер

**FR-15.** Система должна копировать файл с расширением `.pdf` (без учёта
регистра) в каталог результатов без конвертации и возвращать `True`.
Источник: `infrastructure.py:14-17`. Проверка: нет теста.

**FR-16.** Система должна при отсутствии в PATH и `unoconv`, и `soffice` писать
ошибку в лог и бросать `FileNotFoundError`.
Источник: `infrastructure.py:20-22`. Проверка: нет теста.

**FR-17.** Система должна при наличии `unoconv` выполнять
`unoconv -f pdf -o <каталог>/<stem>.pdf <файл>`, иначе
`soffice --headless --convert-to pdf --outdir <каталог> <файл>`.
Источник: `infrastructure.py:24-33`. Проверка: нет теста.

**FR-18.** Система должна после нулевого кода возврата писать stdout в лог уровня
DEBUG и возвращать `True`, только если существует `<каталог>/<stem>.pdf`; при
ненулевом коде — писать stderr в лог и возвращать `False`; при ненайденной
команде — писать ошибку и возвращать `False`.
Источник: `infrastructure.py:35-47`. Проверка: нет теста.

**FR-19.** Система должна в `get_converter()` возвращать `UnoconvConverter` на
любой ОС и писать в лог, что выбрана стратегия LibreOffice.
Источник: `infrastructure.py:50-53`. Проверка: нет теста.

### 3.7 Журнал

**FR-20.** Система должна писать журнал в stderr (INFO, формат
`{time:HH:mm:ss} | {level: <7} | {message}`), в панель «Logs» (INFO, только текст)
и в файл `logs/app_{time:YYYY-DD-MM}.log` в JSON с ротацией 100 MB, хранением
10 дней и очередью записи.
Источник: `logger.py:10-23`. Проверка: нет теста.

### 3.8 Заявлено, но не реализовано

| Заявление | Где | Что в коде |
| --- | --- | --- |
| `OfficeConverter` через COM для Microsoft Office на Windows | `README.md:10`, `README.md:43`, `README.md:91` | класса нет; `get_converter()` всегда LibreOffice (`infrastructure.py:50-53`) |
| «Фабричная функция определяет ОС» | раздел «Архитектура» README | ОС не определяется |
| Приложение «drives Microsoft Office» | `.github/workflows/python-ci.yml:4` | то же |
| Форматы `.docx`, `.pptx`, `.doc`, `.ppt` | README, «Основные возможности»; `supported_formats` в `config/settings.yaml` | фильтра нет; файл настроек не читается |
| Настройки логирования из `config/settings.yaml` | `config/settings.yaml` | значения заданы в `logger.py:12-20` |
| «Сохраняет настройки интерфейса» | README, «Умные функции» | сохраняется только `last_path` (`ui.py:82`) |
| Статус документа | `domain.py:8` (`status = "pending"`) | не меняется нигде |
| Признак успеха `convert() -> bool` | `domain.py:11` | `Worker` его не использует (`application.py:25`) |
| Зависимости `PyYAML`, `pywin32-ctypes`, `pytest-mock` | `requirements.txt` | не импортируются |

## 4. Интерфейсы

Элементы окна (`ui.py:40-63`):

| Элемент | Тип | Действие |
| --- | --- | --- |
| «Перетащите файлы сюда … или» | `QLabel` | видна при пустом списке |
| список файлов | `QListWidget` | полные пути |
| «Выбрать файлы» | `QPushButton` | FR-2 |
| «Очистить» | `QPushButton` | FR-5 |
| «Конвертировать» | `QPushButton` | FR-8 |
| индикатор прогресса | `QProgressBar` | FR-12 |
| «Открыть папку» | `QPushButton` | FR-14 |
| «Logs» | `QDockWidget` с `QTextEdit` только для чтения, справа | FR-1, FR-20 |

Сигналы Qt:

| Объект | Сигнал | Источник |
| --- | --- | --- |
| `Controller` | `conversion_started()`, `conversion_progress(int)`, `conversion_finished(str)` | `application.py:38-40` |
| `WorkerSignals` | `progress(int)`, `finished()` | `application.py:33-35` |
| `QtSignalHandler` | `message_written(str)` | `logger.py:5-8` |

Программный интерфейс конвертера: `IConverter.convert(doc_path: Path,
output_dir: Path) -> bool` (`domain.py:10-11`).

Командная строка:

| Команда | Аргументы | Источник |
| --- | --- | --- |
| `python main.py` | собственных нет | README, `main.py` |
| `python scripts/check_before_push.py` | `--install-hook`, `--quiet` | `scripts/check_before_push.py:320-326` |

Внешние команды: таблица FR-17.

## 5. Данные

| Сущность / файл | Формат | Источник |
| --- | --- | --- |
| `Document` | dataclass: `path: Path`, `status: str = "pending"` | `domain.py:5-8` |
| Каталог результатов | `ГГГГ-ММ-ДД_ЧЧ-ММ-СС/` в текущем рабочем каталоге, внутри `<stem>.pdf` и скопированные PDF | `application.py:58-60`, `infrastructure.py:15`, `infrastructure.py:24` |
| Журнал | `logs/app_<ГГГГ-ДД-ММ>.log`, записи JSON (`serialize=True`) | `logger.py:14-20` |
| Настройка `last_path` | `QSettings`, организация `MySoft`, приложение `FileConverter` | `ui.py:37` |
| `config/settings.yaml` | YAML: `logging.{level, rotation, retention, enqueue, serialize}`, `supported_formats` | `config/settings.yaml`; кодом не читается |

Базы данных нет.

## 6. Нефункциональные требования

**NFR-1.** Конвертация должна выполняться вне потока GUI, в `QThreadPool`.
Источник: `application.py:46`, `application.py:65`.

**NFR-2.** Файл журнала должен ротироваться при 100 MB, храниться 10 дней и
писаться через очередь (`enqueue=True`). Источник: `logger.py:16-19`.

**NFR-3.** Тесты должны выполняться в CI на каждый push и pull request на
`windows-latest` с Python 3.13, с правами `contents: read`.
Источник: `.github/workflows/python-ci.yml`.

**NFR-4.** Перед push разработчик может повторить шаги CI локально скриптом
`scripts/check_before_push.py` из стандарта
[repo-quality-template](https://github.com/IGORSVOLOHOVS/repo-quality-template);
остальной инструментарий стандарта в репозитории отсутствует.
Источник: `scripts/check_before_push.py:1-20`.

**NFR-5.** Тексты интерфейса и сообщения журнала — на русском (кроме заголовков
окна «FileFlow Converter» и панели «Logs»), оформление — тёмная таблица стилей. Источник: `ui.py:22-31`, `ui.py:43-52`, `application.py:21-27`.

**NFR-6.** Распространение по лицензии MIT. Источник: `LICENSE`.

Требований к скорости, объёму файлов и числу файлов в пакете в коде нет;
`test_benchmark_conversion_speed` измеряет время, но порога не задаёт.

## 7. Ограничения и зависимости

| Зависимость | Версия | Источник |
| --- | --- | --- |
| Python | не закреплена; 3.13 в CI | `.github/workflows/python-ci.yml` |
| PyQt6 | не закреплена | `requirements.txt` |
| loguru | не закреплена | `requirements.txt` |
| PyYAML | не закреплена; не используется | `requirements.txt` |
| pywin32-ctypes | не закреплена, только `win32`; не используется | `requirements.txt` |
| pytest, pytest-benchmark, pytest-mock | не закреплены; pytest-mock не используется | `requirements.txt` |
| LibreOffice (`unoconv` или `soffice`) | не указана | `infrastructure.py:20-33` |
| `actions/checkout`, `actions/setup-python` | `v4`, `v5` | `.github/workflows/python-ci.yml` |

Lock-файла нет. Вывод: аннотации `list[Document]` в сигнатурах вычисляются при
определении функций (`application.py:10`), поэтому нужен Python не ниже 3.9.

## 8. Приёмка

1. Установить зависимости (`uv pip install -r requirements.txt`, README) и
   выполнить `pytest -q`: все 4 теста должны пройти (FR-6, FR-7, частично FR-8 и
   FR-10). При написании этой спецификации тесты локально не запускались; CI-прогон
   31205491406 на `2ba4388` (2026-08-07) завершился success, число прошедших
   тестов из него не видно — логи недоступны (HTTP 410).
2. Вручную, с LibreOffice в PATH: `python main.py`, перетащить `.docx` и `.pdf`,
   нажать «Конвертировать». Ожидается: каталог `ГГГГ-ММ-ДД_ЧЧ-ММ-СС` в рабочем
   каталоге с двумя PDF, путь в буфере обмена, кнопка «Открыть папку» открывает
   его, в панели «Logs» строки «Файл 1 из 2 …» (FR-1, FR-3, FR-4, FR-8 … FR-15,
   FR-17, FR-18). Затем «Выбрать файлы» и «Очистить» (FR-2, FR-5).
3. Вручную, без `unoconv` и `soffice` в PATH: тот же сценарий с `.docx` даёт в
   журнале «Сбой при обработке …» (FR-11, FR-16).
4. Проверить появление `logs/app_*.log` с JSON-записями (FR-20).

FR-19 проверяется чтением `infrastructure.py:50-53`.

## 9. Открытые вопросы

- Кто пользователи и где приложение используется; поддерживается ли оно после
  `v1.0.0`.
- Планируется ли `OfficeConverter` для Windows или README и комментарий CI надо
  исправить.
- С какими параметрами собираются `main.dist/main.dll` и `FileFlowConverter.exe`
  и зачем DLL закоммичена; публикуется ли исполняемый файл. Частично известно:
  DLL собрана Nuitka под Python 3.13 (в ней строки `Nuitka`,
  `NUITKA_ONEFILE_DIRECTORY` и ссылка на `python313.dll`).
- Должен ли `config/settings.yaml` управлять журналом и фильтром форматов.
- Должно ли имя журнала быть `YYYY-MM-DD` вместо `YYYY-DD-MM`.
- Где должны появляться каталоги результатов: в рабочем каталоге, рядом с
  исходниками или в выбранной папке.
- Как сообщать о частично или полностью неудачной конвертации (сейчас итог
  всегда SUCCESS).
- Нужен ли таймаут вызова LibreOffice; на каких версиях LibreOffice, `unoconv` и
  ОС (в том числе macOS) приложение проверялось.
- Отвечено: CI проходит — прогон 31205491406 на `2ba4388` (2026-08-07, шаг
  `pytest -q`) завершился success. Открыто: `on_worker_finish` вызывает
  `QApplication.clipboard()` (`application.py:69`), а тесты `QApplication` не
  создают; вызывается ли он в `test_benchmark_conversion_speed`, из прогона не
  видно — логи недоступны (HTTP 410).
- Значение `MySoft` в `QSettings` — заглушка или настоящее имя организации.
