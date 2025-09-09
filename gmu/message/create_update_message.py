import typer
from termcolor import colored

from gmu.message.update_message import update_message
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.Unisender import UnisenderClient
from gmu.utils.utils import archive_email, get_html_and_attachments, log

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="")
def create_or_update_message(
    list_id: str = typer.Option(20547119, help="ID списка рассылки"),
    html_filename: str = typer.Option(
        None, help="Имя HTML файла (по умолчанию первый .html в папке)"),
    images_folder: str = typer.Option("images", help="Папка с картинками"),
):
    """
    Создает E-mail письмо в Unisender. В буфер обмена помещает ID созданного письма.
    Если файл конфигурации существует, предлагает обновить или пересоздать.
    """

    sender_name, sender_email, subject, html, attachments = get_html_and_attachments(
        html_filename, images_folder, True
    )

    archive_email(html_filename, html, attachments)

    data = {
        "sender_name": sender_name or "",
        "sender_email": sender_email or "",
        "subject": subject or "",
    }

    gmu_cfg = GmuConfig(path="gmu.json")

    # Если gmu.json существует, то обновляем
    if gmu_cfg.exists() and gmu_cfg.data.get("message_id", None) is not None:

        # 1. Удаляем существующее письмо
        uClient.delete_message(gmu_cfg.data.get("message_id", None))

        # 2. Создаем новое письмо
        result = uClient.create_email_message(
            sender_name, sender_email, subject, html, int(
                list_id), attachments
        )

        data["message_id"] = result.get('message_id', '')

        gmu_cfg.update(data)
        log("SUCCESS",
            f"Письмо обновлено, старое письмо было удалено. Message ID: {result.get('message_id', '')}")

    # Если gmu.json не существует, то создаем
    else:
        gmu_cfg.create()

        result = uClient.create_email_message(
            sender_name, sender_email, subject, html, int(
                list_id), attachments
        )

        data["message_id"] = result.get('message_id', '')

        gmu_cfg.update(data)

        log("SUCCESS",
            f"Письмо создано. Message ID: {result.get('message_id', '')}")
