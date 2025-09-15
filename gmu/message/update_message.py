
from typing import Optional

import typer

from gmu.utils import HTMLprocessor
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.Unisender import UnisenderClient
from gmu.utils.utils import (archive_email, get_html_and_attachments,
                             table_print)

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="update")
def update_message(
    html_filename: Optional[str] = typer.Option(
        None, help="Имя HTML файла (по умолчанию первый .html в папке)"),
    list_id: str = typer.Option(20547119, help="ID списка рассылки"),
    images_folder: Optional[str] = typer.Option(
        "images", help="Папка с картинками")
):
    """
    Обновляет E-mail письмо по ID в Unisender. Если параметры не заданы, берёт их из gmu.json.
    Также архивирует html и images.
    ВАЖНО: Unisender не поддерживает обновление письма, если картинки были подключены через URL.
    Поэтому данная функция сначала удаляет письмо, а затем создаёт новое с теми же параметрами, но с новым ID!
    """
    gmu_cfg = GmuConfig()
    gmu_cfg.load()

    if gmu_cfg is None or gmu_cfg.data is None or gmu_cfg.data.get("message_id", None) is None:
        table_print(
            "ERROR", "Файл gmu.json не найден или не содержит message_id.")
        return

    # Удаляем старое письмо
    uClient.delete_message(gmu_cfg.data["message_id"])

    process_result = HTMLprocessor(
        html_filename, images_folder, True
    ).process()

    archive_email(html_filename, process_result.get(
        'inlined_html'), process_result.get('attachments'))

    api_result = uClient.create_email_message(
        process_result.get('sender_name'), process_result.get('sender_email'), process_result.get('subject'), process_result.get('inlined_html'), int(
            list_id), process_result.get('attachments')
    )

    data = {
        "message_id": api_result.get('message_id', ''),
        "sender_name": process_result.get('sender_name'),
        "sender_email":  process_result.get('sender_email'),
        "subject": process_result.get('subject'),
        "preheader": process_result.get('preheader'),
        "language": process_result.get('language'),
    }
    gmu_cfg.update(data)
