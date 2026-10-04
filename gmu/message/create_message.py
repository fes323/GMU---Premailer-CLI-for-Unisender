import typer

from gmu.utils.message_upload import upload_message

app = typer.Typer()


@app.command(name="c", hidden=True)
@app.command(name="create")
def create_message(
    list_id: int = typer.Option(20547119, help="ID списка рассылки"),
    html_filename: str = typer.Option(None, help="Имя HTML-файла"),
    images_folder: str = typer.Option("images", help="Папка с картинками"),
    force: bool = typer.Option(False, help="Пересоздать письмо с удалением старого"),
):
    """Создать или заменить письмо; перед заменой проверяется HTML."""
    upload_message(list_id, html_filename, images_folder, mode="create", force=force)
