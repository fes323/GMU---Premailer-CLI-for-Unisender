
import os
from typing import Optional

import typer

from gmu.utils.archive import archive_email
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.HTMLProcessor import HTMLProcessor
from gmu.utils.Unisender import UnisenderClient

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

    htmlProcessor = HTMLProcessor(
        html_filename, images_folder, True, True)
    process_result = htmlProcessor.process()

    arhchive_path = archive_email(html_filename,
                                  process_result.get('inlined_html'),
                                  process_result.get('attachments'))
    process_result['data']['zip_size'] = os.path.getsize(arhchive_path)
    api_result = uClient.create_email_message(
        sender_name=process_result.get('data', {}).get('sender_name'),
        sender_email=process_result.get('data', {}).get('sender_email'),
        subject=process_result.get('data', {}).get('subject'),
        body=process_result.get('inlined_html', {}),
        list_id=int(list_id),
        attachments=process_result.get('attachments'),
        lang=process_result.get('data', {}).get('language')
    )

    process_result["data"]["message_id"] = api_result.get('message_id', '')

    gmu_cfg.update(process_result.get('data', {}))
