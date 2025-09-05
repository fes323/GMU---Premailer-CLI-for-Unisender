import os
import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PIL import Image
from premailer import transform
from termcolor import colored

load_dotenv()


def log(status: str, message: str):
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


def extract_email_metadata_from_html(html_text: str) -> Tuple[str, str, str]:
    """
    Извлекает имя отправителя, email отправителя и тему письма из HTML.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    sender_name_tag = soup.find("meta", attrs={"name": "sender-name"})
    sender_email_tag = soup.find("meta", attrs={"name": "sender-email"})

    if sender_name_tag:
        sender_name = sender_name_tag.get("content", "Unknown Sender")
    else:
        raise ValueError("Sender name not found in HTML")

    if sender_email_tag:
        sender_email = sender_email_tag.get("content", "Unknown Email")
    else:
        raise ValueError("Sender email not found in HTML")

    subject = soup.title.string if soup.title else "No Subject"
    return sender_name, sender_email, subject


def find_images_in_html(html_text: str, replace_src: bool) -> Tuple[List[Tuple[str, Optional[int]]], BeautifulSoup]:
    """
    Находит изображения в HTML и сохраняет (src, data-width).
    Возвращает список файлов и modifed soup.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    found_images = []
    for tag in soup.find_all("img"):
        src = tag.get("src")
        data_width = tag.get("data-width")
        width = int(data_width) if data_width and data_width.isdigit() else None
        if src:
            tag['src'] = Path(
                src).name if replace_src else f"images/{Path(src).name}"
            found_images.append(
                (Path(src).name, width))
    return found_images, soup


def resize_image(image_bytes: bytes, target_width: int) -> bytes:
    """
    Изменяет размер изображения до заданной ширины с сохранением пропорций.
    """
    with Image.open(BytesIO(image_bytes)) as img:
        w_percent = (target_width / float(img.width))
        target_height = int((float(img.height) * float(w_percent)))
        img = img.resize((target_width, target_height),
                         Image.Resampling.LANCZOS)
        output = BytesIO()
        img_format = img.format if img.format else 'PNG'
        img.save(output, format=img_format)
        return output.getvalue()


def svg_to_png(svg_bytes: bytes) -> bytes:
    """
    Конвертирует SVG-изображение в PNG.
    """
    import cairosvg
    log("INFO", f"Конвертация SVG в PNG...")
    return cairosvg.svg2png(bytestring=svg_bytes)


def process_images(
    images_info: List[Tuple[str, Optional[int]]],
    images_folder: str = "images"
) -> Tuple[Dict[str, bytes], List[str]]:
    """
    Загружает изображения, конвертирует svg→png, ресайзит при необходимости.
    Возвращает: attachs (dict: имя -> байты), список svg-имен.
    """
    attachs: Dict[str, bytes] = {}
    svg_names: List[str] = []
    images_path = Path(images_folder)

    for fname, width in images_info:
        img_file = images_path / fname
        if not img_file.exists():
            log("WARNING",
                f"image {fname} referenced in HTML but not found in {images_folder}/")
            continue
        file_bytes = img_file.read_bytes()
        if fname.lower().endswith('.svg'):
            try:
                png_bytes = svg_to_png(file_bytes)
                png_name = fname.rsplit('.', 1)[0] + '.png'
                attachs[png_name] = png_bytes
                svg_names.append(fname)
            except Exception as e:
                log("ERROR",
                    f"SVG to PNG конвертация не удалась для {fname}: {e}")
            continue
        if fname.lower().endswith('.gif'):
            max_gif_size = 500 * 1024  # 500 KB
            if len(file_bytes) > max_gif_size:
                raise Exception(
                    f"[EXCEPTION] GIF-изображение '{fname}' слишком большое: {len(file_bytes)//1024} КБ")
            log("WARNING",
                f"GIF-изображения не ресайзятся. Изображение '{fname}' будет пропущено.")
            attachs[fname] = file_bytes
            continue
        # Ресайз, если указан data-width
        if width is not None:
            try:
                resized_bytes = resize_image(file_bytes, width)
                attachs[fname] = resized_bytes
                log("INFO",
                    f"Изображение {fname} успешно ресайзено до {width}px.")
            except Exception as e:
                log("ERROR",
                    f"Ошибка при ресайзе изображения {fname}: {e}")
                attachs[fname] = file_bytes
        else:
            attachs[fname] = file_bytes

    return attachs, svg_names


def replace_svg_references_in_html(soup: BeautifulSoup, svg_names: List[str]) -> BeautifulSoup:
    """
    В HTML (soup) меняет src для svg-файлов на png-версии.
    """
    for tag in soup.find_all("img"):
        src = tag.get("src")
        filename = os.path.basename(src)
        if filename in svg_names:
            tag['src'] = src.rsplit('.', 1)[0] + '.png'
            log("INFO", f"Заменяем {src} на PNG версию.")
        else:
            log("INFO", f"Оставляем {src} без изменений.")
    return soup


def extract_conditional_comments(html: str) -> Tuple[str, Dict[str, str]]:
    """
    Ищет условные комментарии и заменяет их на уникальные placeholders.
    """
    pattern = re.compile(r'<!--\[(if.*?endif)\]-->', re.DOTALL | re.IGNORECASE)
    comments = {}

    def replacer(match):
        key = f"<!--COND_COMMENT_{len(comments)}-->"
        comments[key] = match.group(0)
        return key
    modified_html = pattern.sub(replacer, html)
    return modified_html, comments


def restore_conditional_comments(html: str, comments: Dict[str, str]) -> str:
    """
    Восстанавливает условные комментарии по placeholders.
    """
    for placeholder, comment in comments.items():
        html = html.replace(placeholder, comment)
    return html


def inline_css_styles(html: str) -> str:
    """
    Переводит CSS в инлайн-вид в HTML с сохранением условных комментариев.
    """
    # 1. Временно прячем условные комментарии
    modified_html, comments = extract_conditional_comments(html)
    # 2. Инлайнинг
    inlined_html = transform(
        modified_html,
        keep_style_tags=False,
        remove_classes=False,
        preserve_internal_links=True,
        strip_important=False,
        cssutils_logging_level='CRITICAL',
        cssutils_logging_handler=None
    )
    # 3. Восстанавливаем комментарии
    final_html = restore_conditional_comments(inlined_html, comments)
    return final_html


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
            raise FileNotFoundError("HTML file not found in this directory")
        name = html_files[0].stem
        archive_name = f"{name}.zip"
    images_folder = "images"

    with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Пишем финальный index.html (в корень архива)
        zipf.writestr("index.html", html_content)

        # Создаем папку images в архиве и пишем туда все вложения
        for img_name, img_bytes in attachments.items():
            arcname = f"{images_folder}/{img_name}"
            zipf.writestr(arcname, img_bytes)
    log("SUCCESS", f"Архив письма сохранен: {archive_name}")
    return os.path.abspath(archive_name)


def get_html_and_attachments(
    html_filename: str,
    images_folder: str = "images",
    replace_src: bool = True
) -> Tuple[str, str, str, str, Dict[str, bytes]]:
    """
    Главная функция.
    Возвращает мета-информацию, HTML и словарь вложений.
    """
    if not html_filename:
        html_files = list(Path(".").glob("*.html"))
        if not html_files:
            raise FileNotFoundError("HTML file not found in this directory")
        html_file = html_files[0]
    else:
        html_file = Path(html_filename)
        if not html_file.exists():
            raise FileNotFoundError(f"File {html_file} not found")
    # 1. Чтение исходного HTML
    html_text = html_file.read_text(encoding="utf-8")
    # 2. Извлечение метаданных
    sender_name, sender_email, subject = extract_email_metadata_from_html(
        html_text)
    # 3. Поиск изображений (src и data-width), нормализация путей
    images_info, soup = find_images_in_html(
        html_text, replace_src)
    # 4. Работа с файлами: загрузка, ресайз, svg→png
    attachs, svg_names = process_images(
        images_info, images_folder=images_folder)
    # 5. Подмена .svg-на .png в soup согласно тому, что реально конвертировалось
    soup = replace_svg_references_in_html(soup, svg_names)
    # 6. Инлайнинг стилей
    inlined_html = inline_css_styles(str(soup))
    # Возврат
    return sender_name, sender_email, subject, inlined_html, attachs
