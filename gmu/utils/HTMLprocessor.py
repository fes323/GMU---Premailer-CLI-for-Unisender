import os
import re
from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple

import cairosvg
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from PIL import Image
from premailer import transform
from rich.console import Console
from rich.progress import track

from gmu.utils.logger import gmu_logger

load_dotenv()
console = Console()


class HTMLProcessor:
    def __init__(self, html_filename: str, images_folder: str = "images", replace_src: bool = True):
        self.html_filename = html_filename
        self.images_folder = images_folder
        self.replace_src = replace_src

        self.original_html = None
        self.soup = None
        self.sender_name = None
        self.sender_email = None
        self.subject = None
        self.preheader = None
        self.language = None
        self.images_info = []
        self.attachments = {}
        self.svg_names = []
        self.result_html = None

        self._load_html()

    def _load_html(self):
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
        self.soup = BeautifulSoup(self.original_html, "html.parser")

    def _extract_sender_name(self):
        sender_name_tag = self.soup.find(
            "meta", attrs={"name": "sender-name"})
        if sender_name_tag:
            self.sender_name = sender_name_tag.get("content", "Unknown Sender")
        else:
            gmu_logger.critical('Sender name not fount in HTML meta tags')

    def _extract_sender_mail(self):
        sender_email_tag = self.soup.find(
            "meta", attrs={"name": "sender-email"})
        if sender_email_tag:
            self.sender_email = sender_email_tag.get(
                "content", "Unknown Email")
        else:
            gmu_logger.critical('Sender email not fount in HTML meta tags')

    def _extract_subject(self):
        self.subject = self.soup.title.string if self.soup.title else "No Subject"

    def _extract_preheader(self):
        hidden_divs = self.soup.find_all(
            lambda tag: tag.name == 'div' and 'display: none' in tag.get(
                'style', '')
        )
        for div in hidden_divs:
            text = div.get_text(separator=' ', strip=True)

            if text and not re.fullmatch(r'[\s\u200b\xa0&zwnj; ]+', text):
                self.preheader = text
            else:
                self.preheader = None

            break

    def _extract_language(self):
        html_tag = self.soup.find('html')

        if html_tag and html_tag.has_attr('lang'):
            self.language = html_tag['lang']

        # В некоторых письмах lang бывает также у body/div — fallback
        body_tag = self.soup.find('body')
        if body_tag and body_tag.has_attr('lang') and self.language == None:
            self.language = body_tag['lang']

        # Вариант: первый div с lang
        div_lang = self.soup.find(lambda tag: tag.name ==
                                  'div' and tag.has_attr('lang'))
        if div_lang and self.language == None:
            self.language = div_lang['lang']

    def _find_images(self):
        console.print("\n📃 Finding images in HTML")

        found_images = []
        for tag in track(self.soup.find_all("img"), description=""):
            src = tag.get("src")
            data_width = tag.get("data-width")
            width = int(
                data_width) if data_width and data_width.isdigit() else None
            if src:
                tag['src'] = Path(
                    src).name if self.replace_src == True else f"images/{Path(src).name}"
                found_images.append(
                    (Path(src).name, width))
        self.images_info = found_images

    def _process_attachments(self):
        console.print("🖼️ Processing images")

        def __resize_and_compress_image(image_bytes: bytes, target_width: int = None, output_format: str = None, output_bits: int = 8) -> bytes:
            """
            Изменяет размер изображения до заданной ширины с сохранением пропорций и сжимает при сохранении.
            """
            with Image.open(BytesIO(image_bytes)) as img:
                # Приведем все изображения к RGB (или PNG-моду), если требуется
                img_format = output_format if output_format else (
                    img.format if img.format else 'PNG')
                save_params = {}

                # Приводим изображение к нужной битности
                if output_bits == 8:
                    # Для цветных фото — 'RGB', для ч/б — 'L'
                    img = img.convert('RGB')
                elif output_bits == 16:
                    try:
                        # Только для PNG/TIFF и Pillow>=9.1 (16-битные каналы). Для цветных понадобится numpy.
                        import numpy as np
                        arr = np.array(img)
                        if arr.ndim == 2:
                            # grayscale
                            mode = 'I;16'
                        elif arr.ndim == 3 and arr.shape[2] == 3:
                            # RGB
                            mode = 'I;16'
                        elif arr.ndim == 3 and arr.shape[2] == 4:
                            # RGBA
                            mode = 'I;16'
                        else:
                            raise ValueError(
                                'Неподдерживаемый формат для 16 бит')

                        # Нормализация к 16 битам
                        if arr.dtype != np.uint16:
                            arr = (arr.astype(np.float32) /
                                   255.0 * 65535).astype(np.uint16)
                        img = Image.fromarray(arr, 'I;16')
                    except ImportError:
                        raise RuntimeError(
                            "Для 16-битной обработки требуется numpy")

                # Сжатие
                if img_format.upper() == "JPEG":
                    save_params['quality'] = 75
                    save_params['optimize'] = True
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                elif img_format.upper() == "PNG":
                    save_params['optimize'] = True
                    save_params['compress_level'] = 9
                    if output_bits == 16:
                        save_params['bits'] = 16

                # Изменение размера
                if target_width and img.width > target_width:
                    w_percent = (target_width / float(img.width))
                    target_height = int((float(img.height) * float(w_percent)))
                    img = img.resize(
                        (target_width, target_height), Image.Resampling.LANCZOS)

                output = BytesIO()
                img.save(output, format=img_format, **save_params)
                return output.getvalue()

        for fname, width in track(self.images_info, description=""):
            img_file = Path(self.images_folder + "/" + fname)
            if not img_file.exists():
                gmu_logger.warning(
                    f'Image {fname} not found in {self.images_folder}/')
                console.print(
                    f"[bold yellow]WARNING:[/bold yellow] Изображение {fname} не найдено в {self.images_folder}/")
                continue

            file_bytes = img_file.read_bytes()

            # 1. SVG: конвертируем → ресайзим → сжимаем
            if fname.lower().endswith('.svg'):
                try:
                    png_bytes = cairosvg.svg2png(bytestring=file_bytes)
                    png_name = fname.rsplit('.', 1)[0] + '.png'
                    # делаем ресайз+сжатие PNG
                    if width:
                        png_bytes = __resize_and_compress_image(
                            png_bytes, target_width=width, output_format='PNG')
                    else:
                        png_bytes = __resize_and_compress_image(
                            png_bytes, output_format='PNG')

                    self.attachments[png_name] = png_bytes
                    self.svg_names.append(fname)
                except Exception as e:
                    gmu_logger.critical(f'{fname} not converted to png: {e}')
                    console.print(
                        f"[bold red]ERROR:[/bold red] SVG to PNG конвертация не удалась для {fname}: {e}")
                continue

            # 2. GIF: проверяем размер, компрессию не делаем (Pillow плохо оптимизирует gif)
            if fname.lower().endswith('.gif'):
                max_gif_size = 500 * 1024  # 500 KB
                if len(file_bytes) > max_gif_size:
                    gmu_logger.warning(f'GIF {fname} is larger than 500 kb')
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
                self.attachments[fname] = file_bytes
                continue

            # 3. Остальные: ресайз + компрессия
            try:
                # Определим формат по расширению
                ext = fname.split('.')[-1].lower()
                if ext in ('jpg', 'jpeg'):
                    img_format = 'JPEG'
                elif ext == 'png':
                    img_format = 'PNG'
                else:
                    img_format = None  # для Pillow auto-select

                # Ресайз, если есть width, иначе только сжатие
                processed_bytes = __resize_and_compress_image(
                    file_bytes,
                    target_width=width if width else None,
                    output_format=img_format
                )
                self.attachments[fname] = processed_bytes
                gmu_logger.info(
                    f'Image {fname} successfully resized and compressed')
            except Exception as e:
                gmu_logger.critical(
                    f'Error while processing image {fname}: {e}')
                console.print(
                    f"[bold red]ERROR:[/bold red] Ошибка при обработке изображения {fname}: {e}")
                self.attachments[fname] = file_bytes

    def _replace_svg_to_png(self):
        console.print("🔁 Replase .svg to .png in HTML")
        for tag in track(self.soup.find_all("img"), description=""):
            src = tag.get("src")
            filename = os.path.basename(src)
            if filename in self.svg_names:
                tag['src'] = src.rsplit('.', 1)[0] + '.png'
        self.soup = self.soup

    def _remove_spaces_from_style(self):
        def __optimize_style(style_string):
            """Оптимизирует CSS стили, удаляя лишние пробелы"""
            # Удаляем пробелы вокруг двоеточий
            style_string = re.sub(r'\s*:\s*', ':', style_string)
            # Удаляем пробелы вокруг точек с запятой
            style_string = re.sub(r'\s*;\s*', ';', style_string)
            # Удаляем пробелы в начале и конце
            style_string = style_string.strip()
            # Можно не убирать ; в конце!
            return style_string
        all_tags_with_style = self.soup.find_all(style=True)
        for tag in all_tags_with_style:
            tag['style'] = __optimize_style(tag['style'])

    def _inline_css(self):

        def __extract_conditional_comments() -> Tuple[str, Dict[str, str]]:
            """
            Ищет условные комментарии и заменяет их на уникальные placeholders.
            """
            pattern = re.compile(
                r'<!--\[(if.*?endif)\]-->', re.DOTALL | re.IGNORECASE)
            comments = {}

            def replacer(match):
                key = f"<!--COND_COMMENT_{len(comments)}-->"
                comments[key] = match.group(0)
                return key
            modified_html = pattern.sub(replacer, str(self.soup))
            return modified_html, comments

        def __restore_conditional_comments(html: str, comments: Dict[str, str]) -> str:
            """
            Восстанавливает условные комментарии по placeholders.
            """
            for placeholder, comment in comments.items():
                html = html.replace(placeholder, comment)
            return html

        # 1. Временно прячем условные комментарии
        modified_html, comments = __extract_conditional_comments()
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
        self.result_html = __restore_conditional_comments(
            inlined_html, comments)

    def process(self):
        """Основной метод, запускающий весь пайплайн обработки."""
        self._get_soup()
        self._extract_sender_name()
        self._extract_sender_mail()
        self._extract_subject()
        self._extract_preheader()
        self._extract_language()

        self._find_images()
        self._process_attachments()
        self._replace_svg_to_png()
        self._remove_spaces_from_style()
        self._inline_css()

        return {
            'sender_name': self.sender_name,
            'sender_email': self.sender_email,
            'subject': self.subject,
            'preheader': self.preheader,
            'language': self.language,
            'attachments': self.attachments,
            'inlined_html': self.result_html
        }
