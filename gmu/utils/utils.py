import os
import zipfile
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track
from termcolor import colored

from gmu.utils.logger import gmu_logger

load_dotenv()
console = Console()


def table_print(status: str, message: str):
    colors = {
        "INFO": "cyan",
        "WARNING": "yellow",
        "SUCCESS": "green",
        "ERROR": "red",
        "INPUT": "white"
    }
    status_width = 10  # можно увеличить если статус длинный
    status_str = f"{status:<{status_width}}"
    if status == "INPUT":
        return input(f"{colored(status_str, colors.get(status, 'white'))}  {message}")
    else:
        return print(
            f"{colored(status_str, colors.get(status, 'white'))}  {message}"
        )


def archive_email(html_filename: str, html_content: str, attachments: dict, archive_name: str = None):
    """
    Создает zip-архив из итогового HTML и обработанных изображений.
    Внутри архива сохраняет:
        - index.html (финальный, обработанный html)
        - images/ (папка с файлами из attachments)
    :param html_filename: исходное имя html-файла (для имени архива/индекса)
    :param html_content: финальный html-код после обработки
    :param attachments: dict {filename: bytes} с вложениями (обработанные картинки)
    :param archive_name: если не задан — формируется на основе html_filename
    :return: путь к архиву
    """
    if not archive_name:
        html_files = list(Path(".").glob("*.html"))
        if not html_files:
            raise FileNotFoundError(
                "HTML не найден в рабочей директории. Проверьте, что вы в корректной директории.")
        name = html_files[0].stem
        archive_name = f"{name}.zip"
    images_folder = "images"

    with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Пишем финальный index.html (в корень архива)
        zipf.writestr("index.html", html_content)

        console.print("📦 Archiving a letter")
        # Создаем папку images в архиве и пишем туда все вложения
        for img_name, img_bytes in track(attachments.items(), description=""):
            arcname = f"{images_folder}/{img_name}"
            zipf.writestr(arcname, img_bytes)
    table_print("SUCCESS", f"Архив письма сохранен: {archive_name}")
    return os.path.abspath(archive_name)
