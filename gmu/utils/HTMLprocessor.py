import datetime
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple

import cairosvg
from bs4 import BeautifulSoup, Comment
from dotenv import load_dotenv
from PIL import Image
from rich.console import Console
from rich.progress import track

from gmu.utils.custom_css_inliner import inline_css_custom
from gmu.utils.logger import gmu_logger


# Безопасная функция логирования
def safe_log(level, message):
    """Безопасное логирование с проверкой на None."""
    if gmu_logger:
        if level == 'critical':
            gmu_logger.critical(message)
        elif level == 'warning':
            gmu_logger.warning(message)
        elif level == 'info':
            gmu_logger.info(message)
    else:
        print(f"[{level.upper()}] {message}")


load_dotenv()
console = Console()


class HTMLProcessor:
    def __init__(self, html_filename: str, images_folder: str = "images", replace_src: bool = True, rename_images: bool = True):
        """
        html_filename  : имя исходного HTML-файла.
        images_folder : папка, где лежат изображения.
        replace_src   : заменять ли src на короткие пути внутри HTML (True/False).
        rename_images : переименовывать ли картинки (True/False).
        """

        self.html_filename = html_filename
        self.images_folder = images_folder
        self.replace_src = replace_src
        self.rename_images = rename_images

        self.original_html = None
        self.soup = None
        self.sender_name = None
        self.sender_email = None
        self.subject = None
        self.preheader = None
        self.language = None
        # Список (старое_имя, нужная_ширина)
        self.images_info = []
        # Словарь "новое_имя → bytes"
        self.attachments = {}
        # Словарь "старое_имя → новое_имя"
        self.image_renames = {}
        self.size = None
        self.result_html = None

        self._load_html()

    def _load_html(self):
        """Загружает HTML-файл и записывает содержимое в self.original_html."""
        if not self.html_filename:
            html_files = list(Path(".").glob("*.html"))
            if not html_files:
                raise FileNotFoundError(
                    "HTML file not found in this directory")
            html_file = html_files[0]
        else:
            html_file = Path(self.html_filename)
            if not html_file.exists():
                raise FileNotFoundError(f"File {html_file} not found")

        self.original_html = html_file.read_text(encoding="utf-8")

    def _get_soup(self):
        """Создаёт объект BeautifulSoup из загруженного HTML."""
        self.soup = BeautifulSoup(self.original_html, "html.parser")

    def _extract_sender_name(self):
        """Извлекает имя отправителя из meta-тега name='sender-name'."""
        sender_name_tag = self.soup.find("meta", attrs={"name": "sender-name"})
        if sender_name_tag:
            self.sender_name = sender_name_tag.get("content", "Unknown Sender")
        else:
            safe_log('critical', "Sender name not found in HTML meta tags")

    def _extract_sender_mail(self):
        """Извлекает email отправителя из meta-тега name='sender-email'."""
        sender_email_tag = self.soup.find(
            "meta", attrs={"name": "sender-email"})
        if sender_email_tag:
            self.sender_email = sender_email_tag.get(
                "content", "Unknown Email")
        else:
            safe_log('critical', "Sender email not found in HTML meta tags")

    def _extract_subject(self):
        """Извлекает текст <title> как тему письма (subject)."""
        self.subject = self.soup.title.string if self.soup.title else "No Subject"

    def _extract_preheader(self):
        """
        Извлекает «прехедер» (preheader) из первого <div style="display: none">,
        если там содержится не пустой текст.
        """
        hidden_divs = self.soup.find_all(
            lambda tag: tag.name == 'div' and 'display: none' in tag.get(
                'style', '')
        )
        for div in hidden_divs:
            text = div.get_text(separator=' ', strip=True)
            # Проверка, чтобы текст не состоял только из пробелов/непечатаемых символов.
            if text and not re.fullmatch(r'[\s\u200b\xa0&zwnj; ]+', text):
                self.preheader = text
            else:
                self.preheader = None
            break

    def _extract_language(self):
        """
        Извлекает язык (lang) из <html> или, при отсутствии, из <body> / первого <div> с атрибутом lang.
        """
        html_tag = self.soup.find('html')
        if html_tag and html_tag.has_attr('lang'):
            self.language = html_tag['lang']

        body_tag = self.soup.find('body')
        if body_tag and body_tag.has_attr('lang') and self.language is None:
            self.language = body_tag['lang']

        div_lang = self.soup.find(
            lambda tag: tag.name == 'div' and tag.has_attr('lang'))
        if div_lang and self.language is None:
            self.language = div_lang['lang']

    def _find_images(self):
        """Находит тэги <img> в HTML, собирает информацию (имена, требуемую ширину)."""
        console.print("\n[Finding images in HTML]")
        found_images = []
        for tag in track(self.soup.find_all("img"), description=""):
            src = tag.get("src")
            data_width = tag.get("data-width")
            width = int(
                data_width) if data_width and data_width.isdigit() else None
            if src:
                # Если replace_src=True, то в HTML подставляем только имя файла,
                # иначе сохраняем относительный путь images/filename.
                tag['src'] = Path(
                    src).name if self.replace_src else f"images/{Path(src).name}"
                found_images.append((Path(src).name, width))
        self.images_info = found_images

    def _process_attachments(self):
        """
        Обрабатывает найденные изображения: конвертация svg → png, ресайз и сжатие,
        избегая повторной обработки файла и генерируя новые имена по дате/времени и счётчику.
        """
        console.print("[Processing images]")
        # Генерируем префикс-метку для всех картинок (одна дата/время на единицу обработки)
        time_prefix = datetime.datetime.now().strftime("%d%m%Y%H%M")
        # Ведём счётчик для новых имён
        image_counter = 1

        def _resize_and_compress_image(
            image_bytes: bytes,
            target_width: int = None,
            output_format: str = None
        ) -> bytes:
            """
            Изменяет размер изображения до заданной ширины (с сохранением пропорций)
            и сжимает при сохранении, сохраняя правильные цветовые профили.
            """
            with Image.open(BytesIO(image_bytes)) as img:
                # Сохраняем ICC профиль если он есть
                icc_profile = img.info.get('icc_profile')

                # Если output_format не задан, берём формат из самого изображения или PNG
                img_format = output_format if output_format else (
                    img.format if img.format else 'PNG')
                save_params = {}

                # Улучшенная конвертация цветовых пространств
                if img_format and img_format.upper() == 'JPEG':
                    # JPEG требует RGB режим
                    if img.mode not in ('RGB', 'L'):
                        if img.mode == 'RGBA':
                            # Создаем белый фон для прозрачности
                            background = Image.new(
                                'RGB', img.size, (255, 255, 255))
                            # Используем альфа-канал как маску
                            background.paste(img, mask=img.split()[-1])
                            img = background
                        elif img.mode == 'LA':
                            # Конвертируем L+A в RGB
                            img = img.convert('RGB')
                        else:
                            img = img.convert('RGB')
                elif img_format and img_format.upper() == 'PNG':
                    # PNG поддерживает RGBA, LA, RGB, L
                    if img.mode == 'CMYK':
                        img = img.convert('RGBA')  # CMYK → RGBA
                    elif img.mode == 'P':
                        img = img.convert(
                            'RGBA') if 'transparency' in img.info else img.convert('RGB')
                    elif img.mode not in ('RGBA', 'LA', 'RGB', 'L'):
                        img = img.convert('RGBA')

                # Улучшенные параметры сжатия для лучшего качества
                if img_format and img_format.upper() == "JPEG":
                    save_params['quality'] = 85  # Увеличиваем качество
                    save_params['optimize'] = True
                    save_params['progressive'] = True
                    # Отключаем субсэмплинг для лучшего качества
                    save_params['subsampling'] = 0
                elif img_format and img_format.upper() == "PNG":
                    save_params['optimize'] = True
                    # Уменьшаем сжатие для лучшего качества
                    save_params['compress_level'] = 6

                # Ресайз, если target_width задан и изображение больше
                if target_width and img.width > target_width:
                    w_percent = target_width / float(img.width)
                    target_height = int(img.height * w_percent)
                    img = img.resize(
                        (target_width, target_height), Image.Resampling.LANCZOS)

                # Восстанавливаем ICC профиль если он был
                if icc_profile and img_format and img_format.upper() == 'PNG':
                    save_params['icc_profile'] = icc_profile

                output = BytesIO()
                img.save(output, format=img_format, **save_params)
                return output.getvalue()

        # Проходимся по списку (fname, width)
        for fname, width in track(self.images_info, description=""):
            # Если уже обрабатывали этот файл, переходим к следующему (не создаём дубль прикрепления)
            if fname in self.image_renames:
                continue

            img_file = Path(self.images_folder) / fname
            if not img_file.exists():
                safe_log(
                    'warning', f"Image {fname} not found in {self.images_folder}/")
                console.print(
                    f"[bold yellow]WARNING:[/bold yellow] Изображение {fname} не найдено в {self.images_folder}/"
                )
                continue

            file_bytes = img_file.read_bytes()
            ext = fname.split('.')[-1].lower()

            # Генерация нового имени (в случае rename_images) одна для данного файла
            # и фиксируется до конца обработки
            if self.rename_images:
                # Формат: DDMMYYYYHHMM_счётчик
                # (final_ext добавляется после обработки)
                tentative_name = f"{time_prefix}_{image_counter}"
                image_counter += 1
            else:
                # Если не переименовываем - используем исходное имя (позже добавим .png для svg)
                # без расширения, чтобы svg → png корректно дописался
                tentative_name = fname.rsplit('.', 1)[0]

            # 1. SVG → PNG с улучшенными параметрами
            if ext == 'svg':
                try:
                    # Улучшенная конвертация SVG в PNG с лучшими параметрами
                    png_bytes = cairosvg.svg2png(
                        bytestring=file_bytes,
                        output_width=width if width else None,  # Задаем ширину сразу если нужна
                        unsafe=False,  # Безопасный режим
                        output_height=None,  # Автоматический расчет высоты
                        background_color='white'  # Белый фон для лучшей совместимости
                    )
                    final_ext = '.png'

                    # Дополнительная обработка если нужен ресайз (когда width задана в SVG но не в атрибуте data-width)
                    if not width:
                        with Image.open(BytesIO(png_bytes)) as img_check:
                            if img_check.width > 1200:  # Если изображение слишком широкое для email
                                png_bytes = _resize_and_compress_image(
                                    png_bytes, target_width=1200, output_format='PNG')
                            else:
                                png_bytes = _resize_and_compress_image(
                                    png_bytes, output_format='PNG')
                    else:
                        # Если ширина уже задана, используем стандартную обработку
                        png_bytes = _resize_and_compress_image(
                            png_bytes, target_width=width, output_format='PNG')

                    if self.rename_images:
                        new_name = f"{tentative_name}{final_ext}"
                    else:
                        # старое имя, но расширение → .png
                        # tentative_name уже без исходного расширения
                        new_name = f"{tentative_name}{final_ext}"

                    self.attachments[new_name] = png_bytes
                    self.image_renames[fname] = new_name
                    safe_log(
                        'info', f"SVG {fname} successfully converted to PNG")
                except Exception as e:
                    safe_log('critical', f"{fname} not converted to png: {e}")
                    console.print(
                        f"[bold red]ERROR:[/bold red] SVG to PNG конвертация не удалась для {fname}: {e}"
                    )
                continue

            # 2. GIF: не ресайзим, но проверяем размер
            if ext == 'gif':
                max_gif_size = 500 * 1024  # 500 KB
                if len(file_bytes) > max_gif_size:
                    safe_log('warning', f"GIF {fname} is larger than 500 kb")
                    console.print(
                        f"[bold red]EXCEPTION:[/bold red] GIF-изображение '{fname}' "
                        f"слишком большое: {len(file_bytes)//1024} КБ"
                    )
                    raise Exception(
                        f"[EXCEPTION] GIF-изображение '{fname}' слишком большое: {len(file_bytes)//1024} КБ"
                    )
                safe_log(
                    'info', f"GIF images do not resize. data-width ignored. {fname} skip.")
                console.print(
                    f"[bold yellow]WARNING:[/bold yellow] GIF-изображения не ресайзятся. '{fname}' будет пропущено."
                )

                if self.rename_images:
                    # .gif → добавляем расширение
                    new_name = f"{tentative_name}.gif"
                else:
                    new_name = fname

                self.attachments[new_name] = file_bytes
                self.image_renames[fname] = new_name
                continue

            # 3. Остальные форматы (jpg / jpeg / png / webp / bmp / tiff / ...)
            try:
                if ext in ('jpg', 'jpeg'):
                    img_format = 'JPEG'
                    final_ext = '.jpg'
                elif ext == 'png':
                    img_format = 'PNG'
                    final_ext = '.png'
                elif ext == 'webp':
                    img_format = 'WEBP'
                    final_ext = '.webp'
                elif ext == 'bmp':
                    img_format = 'BMP'
                    final_ext = '.bmp'
                elif ext in ('tiff', 'tif'):
                    img_format = 'TIFF'
                    final_ext = '.tiff'
                else:
                    img_format = None
                    final_ext = f".{ext}"

                processed_bytes = _resize_and_compress_image(
                    file_bytes,
                    target_width=width if width else None,
                    output_format=img_format
                )

                if self.rename_images:
                    new_name = f"{tentative_name}{final_ext}"
                else:
                    # Если не переименовываем, оставляем исходное имя
                    new_name = fname

                self.attachments[new_name] = processed_bytes
                self.image_renames[fname] = new_name
                safe_log(
                    'info', f"Image {fname} ({ext.upper()}) successfully processed.")
            except Exception as e:
                safe_log(
                    'critical', f"Error while processing image {fname}: {e}")
                console.print(
                    f"[bold red]ERROR:[/bold red] Ошибка при обработке изображения {fname}: {e}"
                )
                # Ошибка — всё равно добавим файл во вложения, чтобы письмо сформировалось
                if self.rename_images:
                    new_name = f"{tentative_name}{final_ext}"
                else:
                    new_name = fname

                self.attachments[new_name] = file_bytes
                self.image_renames[fname] = new_name

    def _update_image_sources(self):
        """
        После того, как все картинки обработаны и переименованы (при необходимости),
        пройдёмся по <img> и обновим атрибуты src на конечные имена.
        """
        console.print("[Updating <img> src in HTML]")
        for tag in track(self.soup.find_all("img"), description=""):
            old_src = tag.get("src")
            old_basename = os.path.basename(old_src)
            # Если при обработке есть новое имя
            if old_basename in self.image_renames:
                new_fname = self.image_renames[old_basename]
                if self.replace_src:
                    tag['src'] = Path(new_fname).name
                else:
                    tag['src'] = f"{self.images_folder}/{Path(new_fname).name}"

    def _preserve_existing_dimensions(self):
        """
        Устанавливает атрибуты width и height для изображений ТОЛЬКО если они не заданы явно.
        data-width и data-height используются только для обработки изображений, а не для управления отображением.
        Приоритет: существующий атрибут width/height > CSS стили > data-width/data-height (только если ничего не задано).
        После обработки удаляет data-width и data-height атрибуты, чтобы они не влияли на отображение.
        """
        console.print(
            "[Preserving existing width/height attributes and CSS styles]")
        for tag in track(self.soup.find_all("img"), description=""):
            data_width = tag.get("data-width")
            data_height = tag.get("data-height")

            # Проверяем, есть ли уже заданные атрибуты или стили
            existing_width = tag.get('width')
            existing_height = tag.get('height')
            current_style = tag.get('style', '')

            # Проверяем наличие width в CSS стилях
            has_width_in_css = 'width' in current_style if current_style else False
            has_height_in_css = 'height' in current_style if current_style else False

            # Устанавливаем width только если НЕТ существующего атрибута И НЕТ CSS стиля
            if data_width and data_width.isdigit() and not existing_width and not has_width_in_css:
                tag['width'] = data_width
                safe_log(
                    'info', f"Set width={data_width}px from data-width for image {tag.get('src', 'unknown')} (no existing width found)")

            # Устанавливаем height только если НЕТ существующего атрибута И НЕТ CSS стиля
            if data_height and data_height.isdigit() and not existing_height and not has_height_in_css:
                tag['height'] = data_height
                safe_log(
                    'info', f"Set height={data_height}px from data-height for image {tag.get('src', 'unknown')} (no existing height found)")

            # Логируем случаи, когда data-width/data-height игнорируются
            if data_width and data_width.isdigit() and (existing_width or has_width_in_css):
                reason = "existing width attribute" if existing_width else "existing CSS width style"
                safe_log(
                    'info', f"Ignored data-width={data_width}px for image {tag.get('src', 'unknown')} due to {reason}")

            if data_height and data_height.isdigit() and (existing_height or has_height_in_css):
                reason = "existing height attribute" if existing_height else "existing CSS height style"
                safe_log(
                    'info', f"Ignored data-height={data_height}px for image {tag.get('src', 'unknown')} due to {reason}")

            # Удаляем data-width и data-height атрибуты после обработки, чтобы они не влияли на отображение
            if data_width:
                del tag['data-width']
                safe_log(
                    'info', f"Removed data-width attribute from image {tag.get('src', 'unknown')}")
            if data_height:
                del tag['data-height']
                safe_log(
                    'info', f"Removed data-height attribute from image {tag.get('src', 'unknown')}")

    def _remove_spaces_from_style(self):
        """Удаляет лишние пробелы из атрибутов style во всех тегах."""
        def _optimize_style(style_string):
            style_string = re.sub(r'\s*:\s*', ':', style_string)
            style_string = re.sub(r'\s*;\s*', ';', style_string)
            return style_string.strip()

        all_tags_with_style = self.soup.find_all(style=True)
        for tag in all_tags_with_style:
            tag['style'] = _optimize_style(tag['style'])

    def _inline_css(self):
        """Инлайнит все стили с помощью собственного решения с сохранением Outlook-комментариев."""

        # Используем собственное решение для инлайн-стилизации
        # Оно автоматически сохраняет Outlook комментарии
        self.result_html = inline_css_custom(str(self.soup))

    def process(self):
        """Основной метод, запускающий весь пайплайн обработки."""

        # 1. Разбор HTML, извлечение базовых мета-данных
        self._get_soup()
        self._extract_sender_name()
        self._extract_sender_mail()
        self._extract_subject()
        self._extract_preheader()
        self._extract_language()

        # 2. Поиск <img>, формирование списка для обработки
        self._find_images()
        # 3. Обработка изображений (конверсия, ресайз, переименование)
        self._process_attachments()
        # 4. Обновляем ссылки в <img src> на конечные имена
        self._update_image_sources()
        # 5. Сохраняем существующие размеры и устанавливаем data-width только как fallback
        self._preserve_existing_dimensions()
        # 6. Убираем пробелы из inline-style
        self._remove_spaces_from_style()
        # 7. Инлайн CSS (premailer)
        self._inline_css()

        return {
            'data': {
                'sender_name': self.sender_name,
                'sender_email': self.sender_email,
                'subject': self.subject,
                'preheader': self.preheader,
                'language': self.language,
            },
            'attachments': self.attachments,
            'inlined_html': self.result_html,
        }
