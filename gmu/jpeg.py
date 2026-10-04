from pathlib import Path
from typing import Optional

import typer

from gmu.utils.helpers import table_print
from gmu.utils.letter_screenshot import screenshot_letter

app = typer.Typer()


@app.command(name="pdf", hidden=True)
@app.command(name="screenshot", hidden=True)
@app.command(name="jpg", hidden=True)
@app.command(name="jpeg")
def create_jpeg(
    html_filename: Optional[Path] = typer.Option(None, help="HTML письма; по умолчанию единственный .html в папке"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Путь к JPEG; по умолчанию имя HTML с расширением .jpg"),
    width: int = typer.Option(1280, min=1, max=16384, help="Ширина окна браузера в пикселях; высота — всё письмо"),
    quality: int = typer.Option(95, min=1, max=100, help="Качество JPEG"),
    browser: str = typer.Option("auto", help="Браузер: auto, chromium, msedge или chrome"),
):
    """Сохранить всё письмо одним JPEG-снимком без разбиения на страницы."""
    try:
        target = screenshot_letter(html_filename, output, width, quality, browser)
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
        table_print("ERROR", str(exc))
        raise typer.Exit(1) from exc
    table_print("SUCCESS", f"JPEG всего письма сохранён: {target}")
