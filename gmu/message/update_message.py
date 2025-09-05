
import typer
from termcolor import colored

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.Unisender import UnisenderClient
from gmu.utils.utils import archive_email, get_html_and_attachments, log

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="update")
def update_message(
    html_filename: str = typer.Option(
        None, help="Имя HTML файла (по умолчанию первый .html в папке)"),
    images_folder: str = typer.Option("images", help="Папка с картинками")
):
    """
    Обновляет E-mail письмо по ID в Unisender. Если параметры не заданы, берёт их из gmu.json.
    Также архивирует html и images.
    ВАЖНО: Unisender не поддерживает обновление письма, если картинки были подключены через URL.
    Поэтому данная функция сначала удаляет письмо, а затем создаёт новое с теми же параметрами, но с новым ID!
    """
    gmu_cfg = GmuConfig("gmu.json")

    if gmu_cfg is None or gmu_cfg.data is None or gmu_cfg.data.get("message_id", None) is None:
        log(
            "ERROR", "Файл gmu.json не найден или не содержит message_id.")
        return

    # Удаляем старое письмо
    uClient.delete_message(gmu_cfg.data["message_id"])

    gmu_cfg.create()

    sender_name, sender_email, subject, html, attachments = get_html_and_attachments(
        html_filename, images_folder
    )

    archive_email(html_filename, html, attachments)

    result = uClient.create_email_message(
        sender_name, sender_email, subject, html, 20547119, attachments
    )

    data = {
        "message_id": result.get('message_id', ''),
        "sender_name": sender_name or "",
        "sender_email": sender_email or "",
        "subject": subject or "",
    }
    gmu_cfg.update(data)
