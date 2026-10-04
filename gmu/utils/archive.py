import os
import zipfile
from pathlib import Path

from rich.console import Console
from rich.progress import track

from gmu.utils.helpers import table_print

console = Console()


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
        if html_filename:
            name = Path(html_filename).stem
        else:
            html_files = sorted(Path(".").glob("*.html"))
            if len(html_files) != 1:
                raise ValueError("Укажите HTML-файл для архива: найдено не ровно одно письмо.")
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
