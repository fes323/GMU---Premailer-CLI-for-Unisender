import os
import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cairosvg
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PIL import Image
from premailer import transform
from rich.console import Console
from rich.progress import track
from termcolor import colored
from utils.logger import gmu_logger

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


def get_sender_email(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    sender_email_tag = soup.find("meta", attrs={"name": "sender-email"})
    if sender_email_tag:
        sender_email = sender_email_tag.get("content", "Unknown Email")
    else:
        gmu_logger.critical('Sender email not fount in HTML meta tags')
        raise ValueError("Sender email not found in HTML")
    return sender_email


def get_sender_name(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    sender_name_tag = soup.find("meta", attrs={"name": "sender-name"})
    if sender_name_tag:
        sender_name = sender_name_tag.get("content", "Unknown Sender")
    else:
        gmu_logger.critical('Sender name not fount in HTML meta tags')
        raise ValueError("Sender name not found in HTML")
    return sender_name


def get_subject(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    subject = soup.title.string if soup.title else "No Subject"
    return subject


def get_preheader(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    # Найти все скрытые <div>
    hidden_divs = soup.find_all(
        lambda tag: tag.name == 'div' and 'display: none' in tag.get(
            'style', '')
    )
    for div in hidden_divs:
        text = div.get_text(separator=' ', strip=True)

        if text and not re.fullmatch(r'[\s\u200b\xa0&zwnj; ]+', text):
            return text
    return ""


def get_lang(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    html_tag = soup.find('html')
    if html_tag and html_tag.has_attr('lang'):
        return html_tag['lang']
    # В некоторых письмах lang бывает также у body/div — fallback
    body_tag = soup.find('body')
    if body_tag and body_tag.has_attr('lang'):
        return body_tag['lang']
    # Вариант: первый div с lang
    div_lang = soup.find(lambda tag: tag.name ==
                         'div' and tag.has_attr('lang'))
    if div_lang:
        return div_lang['lang']
    return ""


def find_images_in_html(html_text: str, replace_src: bool) -> Tuple[List[Tuple[str, Optional[int]]], BeautifulSoup]:
    """
    Находит изображения в HTML и сохраняет (src, data-width).
    Возвращает список файлов и modifed soup.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    found_images = []
    console.print("\n📃 Finding images in HTML")
    for tag in track(soup.find_all("img"), description=""):
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

    console.print("🖼️ Processing images")
    for fname, width in track(images_info, description=""):
        img_file = images_path / fname
        if not img_file.exists():
            gmu_logger.warning(f'Image {fname} not found in {images_folder}/')
            console.print(
                f"[bold yellow]WARNING:[/bold yellow] Изображение {fname} не найдено в {images_folder}/"
            )
            continue
        file_bytes = img_file.read_bytes()
        if fname.lower().endswith('.svg'):
            try:
                png_bytes = svg_to_png(file_bytes)
                png_name = fname.rsplit('.', 1)[0] + '.png'
                attachs[png_name] = png_bytes
                svg_names.append(fname)
            except Exception as e:
                gmu_logger.critical(f'{fname} not converted to png: {e}')
                console.print(
                    f"[bold red]ERROR:[/bold red] SVG to PNG конвертация не удалась для {fname}: {e}"
                )
            continue
        if fname.lower().endswith('.gif'):
            max_gif_size = 500 * 1024  # 500 KB
            if len(file_bytes) > max_gif_size:
                gmu_logger.warning(
                    f'GIF {fname} is larger than 500 kb')
                console.print(
                    f"[bold red]EXCEPTION:[/bold red] GIF-изображение '{fname}' слишком большое: {len(file_bytes)//1024} КБ"
                )
                raise Exception(
                    f"[EXCEPTION] GIF-изображение '{fname}' слишком большое: {len(file_bytes)//1024} КБ"
                )
            gmu_logger.info(
                f'GIF images do not resize. data-width does not work. {fname} skip')
            console.print(
                f"[bold yellow]WARNING:[/bold yellow] GIF-изображения не ресайзятся. Изображение '{fname}' будет пропущено."
            )
            attachs[fname] = file_bytes
            continue
        # Ресайз, если указан data-width
        if width:
            try:
                resized_bytes = resize_image(file_bytes, width)
                attachs[fname] = resized_bytes
                gmu_logger.info(f'Image {fname} successfully resized')

            except Exception as e:
                gmu_logger.critical(f'Error while resizing image {fname}: {e}')
                console.print(
                    f"[bold red]ERROR:[/bold red] Ошибка при ресайзе изображения {fname}: {e}"
                )
                attachs[fname] = file_bytes
        else:
            attachs[fname] = file_bytes

    return attachs, svg_names


def replace_svg_references_in_html(soup: BeautifulSoup, svg_names: List[str]) -> BeautifulSoup:
    """
    В HTML (soup) меняет src для svg-файлов на png-версии.
    """
    console.print("🔁 Replase .svg to .png in HTML")
    for tag in track(soup.find_all("img"), description=""):
        src = tag.get("src")
        filename = os.path.basename(src)
        if filename in svg_names:
            tag['src'] = src.rsplit('.', 1)[0] + '.png'

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


def get_html_and_attachments(
    html_filename: str,
    images_folder: str = "images",
    replace_src: bool = True
) -> Dict:
    """
    Главная функция.
    Возвращает словарь:
    {
        'sender_name': str,
        'sender_email': str,
        'subject': str,
        'preheader': str,
        'lang': str,
        'attachments': dict[str:binary],
        'inlined_html': str
    }
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

    sender_name = get_sender_name(html_text)
    sender_email = get_sender_email(html_text)
    subject = get_subject(html_text)
    preheader = get_preheader(html_text)
    lang = get_lang(html_text)

    # 2. Поиск изображений (src и data-width), нормализация путей
    images_info, soup = find_images_in_html(
        html_text, replace_src)

    # 3. Работа с файлами: загрузка, ресайз, svg→png
    attachments, svg_names = process_images(
        images_info, images_folder=images_folder)

    # 4. Подмена .svg-на .png в soup согласно тому, что реально конвертировалось
    soup = replace_svg_references_in_html(soup, svg_names)

    # 5. Инлайнинг стилей
    inlined_html = inline_css_styles(str(soup))

    # Возврат
    return {
        'sender_name': sender_name,
        'sender_email': sender_email,
        'subject': subject,
        'preheader': preheader,
        'lang': lang,
        'attachments': attachments,
        'inlined_html': inlined_html
    }
