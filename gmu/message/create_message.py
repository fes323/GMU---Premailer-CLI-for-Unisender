import typer
from termcolor import colored

from gmu.message.update_message import update_message
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.Unisender import UnisenderClient
from gmu.utils.utils import archive_email, get_html_and_attachments, log

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="create")
def create_message(
    list_id: str = typer.Option(20547119, help="ID списка рассылки"),
    html_filename: str = typer.Option(
        None, help="Имя HTML файла (по умолчанию первый .html в папке)"),
    images_folder: str = typer.Option("images", help="Папка с картинками"),
):
    """
    Создает E-mail письмо в Unisender. В буфер обмена помещает ID созданного письма.
    Если файл конфигурации существует, предлагает обновить или пересоздать.
    """

    gmu_cfg = GmuConfig(path="gmu.json")

    if gmu_cfg.exists() and gmu_cfg.data.get("message_id", None) is not None:
        return log("WARNING", f"Письмо уже создано. Используется ID из gmu.json. ID: {gmu_cfg.data.get('message_id', '')}")

    sender_name, sender_email, subject, html, attachments = get_html_and_attachments(
        html_filename, images_folder, True
    )

    archive_email(html_filename, html, attachments)

    result = uClient.create_email_message(
        sender_name, sender_email, subject, html, int(
            list_id), attachments
    )
    data = {
        "message_id": result.get('message_id', ''),
        "sender_name": sender_name or "",
        "sender_email": sender_email or "",
        "subject": subject or "",
    }

    gmu_cfg.create()
    gmu_cfg.update(data)
    log("SUCCESS",
        f"Письмо загружено в Unisender. Message ID: {result.get('message_id', '')}")
