import typer

from gmu.utils.utils import archive_email, get_html_and_attachments

app = typer.Typer()


@app.command(name="archive")
def archive(
    html_filename: str = typer.Option(
        None, help="Имя HTML файла (по умолчанию первый .html в папке)"),
    images_folder: str = typer.Option("images", help="Папка с картинками"),
):
    sender_name, sender_email, subject, html, attachments = get_html_and_attachments(
        html_filename, images_folder, True
    )

    archive_email(html_filename, html, attachments)
