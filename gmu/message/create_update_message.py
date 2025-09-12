import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.Unisender import UnisenderClient
from gmu.utils.utils import (archive_email, get_html_and_attachments,
                             table_print)

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="upsert")
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

    process_result = get_html_and_attachments(
        html_filename, images_folder, True
    )

    archive_email(html_filename, process_result.get(
        'inlined_html'), process_result.get('attachments'))

    data = {
        "sender_name": process_result.get('sender_name'),
        "sender_email":  process_result.get('sender_email'),
        "subject": process_result.get('subject'),
        "preheader": process_result.get('preheader'),
        "lang": process_result.get('lang'),
    }

    gmu_cfg = GmuConfig(path="gmu.json")

    # Если gmu.json существует, то обновляем
    if gmu_cfg.exists() and gmu_cfg.data.get("message_id", None) is not None:

        # 1. Удаляем существующее письмо
        uClient.delete_message(gmu_cfg.data.get("message_id", None))

        # 2. Создаем новое письмо
        api_result = uClient.create_email_message(
            process_result.get('sender_name'), process_result.get('sender_email'), process_result.get('subject'), process_result.get('inlined_html'), int(
                list_id), process_result.get('attachments')
        )

        data["message_id"] = api_result.get('message_id', '')

        gmu_cfg.update(data)
        table_print("SUCCESS",
                    f"Письмо обновлено, старое письмо было удалено. Message ID: {api_result.get('message_id', '')}")

    # Если gmu.json не существует, то создаем
    else:
        gmu_cfg.create()

        api_result = uClient.create_email_message(
            process_result.get('sender_name'), process_result.get('sender_email'), process_result.get('subject'), process_result.get('inlined_html'), int(
                list_id), process_result.get('attachments')
        )

        data["message_id"] = api_result.get('message_id', '')

        gmu_cfg.update(data)

        table_print("SUCCESS",
                    f"Письмо создано. Message ID: {api_result.get('message_id', '')}")
