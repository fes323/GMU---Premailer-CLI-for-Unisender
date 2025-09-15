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
        self.html_file = Path(html_filename)
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
        self.svg_names = {}
        self.result_html = None

        self._load_html(html_filename)

    def _load_html(self):
        if not self.html_file:
            html_files = list(Path(".").glob("*.html"))
            if not html_files:
                raise FileNotFoundError(
                    "HTML file not found in this directory")
            html_file = html_files[0]
        else:
            html_file = Path(html_file)
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
                    src).name if self.replace_src else f"images/{Path(src).name}"
                found_images.append(
                    (Path(src).name, width))

        self.images_info = found_images

    def _process_attachments(self):

        console.print("🖼️ Processing images")

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

        for fname, width in track(self.images_info, description=""):
            img_file = self.images_folder / fname
            if not img_file.exists():
                gmu_logger.warning(
                    f'Image {fname} not found in {self.images_folder}/')
                console.print(
                    f"[bold yellow]WARNING:[/bold yellow] Изображение {fname} не найдено в {self.images_folder}/"
                )
                continue
            file_bytes = img_file.read_bytes()
            if fname.lower().endswith('.svg'):
                try:
                    png_bytes = cairosvg.svg2png(bytestring=file_bytes)
                    png_name = fname.rsplit('.', 1)[0] + '.png'
                    self.attachments[png_name] = png_bytes
                    self.svg_names.append(fname)
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
                self.attachments[fname] = file_bytes
                continue
            # Ресайз, если указан data-width
            if width:
                try:
                    resized_bytes = resize_image(file_bytes, width)
                    self.attachments[fname] = resized_bytes
                    gmu_logger.info(f'Image {fname} successfully resized')

                except Exception as e:
                    gmu_logger.critical(
                        f'Error while resizing image {fname}: {e}')
                    console.print(
                        f"[bold red]ERROR:[/bold red] Ошибка при ресайзе изображения {fname}: {e}"
                    )
                    self.attachments[fname] = file_bytes
            else:
                self.attachments[fname] = file_bytes

    def _replace_svg_to_png(self):
        console.print("🔁 Replase .svg to .png in HTML")
        for tag in track(self.soup.find_all("img"), description=""):
            src = tag.get("src")
            filename = os.path.basename(src)
            if filename in self.svg_names:
                tag['src'] = src.rsplit('.', 1)[0] + '.png'

    def _inline_css(self):

        def __extract_conditional_comments(html: str) -> Tuple[str, Dict[str, str]]:
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
            modified_html = pattern.sub(replacer, html)
            return modified_html, comments

        def __restore_conditional_comments(html: str, comments: Dict[str, str]) -> str:
            """
            Восстанавливает условные комментарии по placeholders.
            """
            for placeholder, comment in comments.items():
                html = html.replace(placeholder, comment)
            return html

        # 1. Временно прячем условные комментарии
        modified_html, comments = __extract_conditional_comments(
            self.html_file)
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

        self._extract_sender_name()
        self._extract_sender_mail()
        self._extract_subject()
        self._extract_preheader()
        self._extract_language()

        self._find_images()
        self._process_attachments()
        self._replace_svg_to_png()
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
