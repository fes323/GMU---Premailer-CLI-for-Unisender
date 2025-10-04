import typer

from gmu.utils.archive import archive_email
from gmu.utils.HTMLprocessor import HTMLProcessor

app = typer.Typer()


@app.command(name="archive")
def archive(
    html_filename: str = typer.Option(
        None, help="Имя HTML файла (по умолчанию первый .html в папке)"),
    images_folder: str = typer.Option("images", help="Папка с картинками"),
):
    htmlProcessor = HTMLProcessor(
        html_filename, images_folder, True, True)
    process_result = htmlProcessor.process()

    archive_email(html_filename, process_result.get(
        'inlined_html'), process_result.get('attachments'))
