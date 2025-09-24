import os

import typer

from gmu.utils.archive import archive_email
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.HTMLProcessor import HTMLProcessor
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="upsert")
def create_or_update_message(
    list_id: str = typer.Option(20547119, help="ID списка рассылки"),
    html_filename: str = typer.Option(
        None, help="Имя HTML файла (по умолчанию первый .html в папке)"),
    images_folder: str = typer.Option("images", help="Папка с картинками"),
    force: bool = typer.Option(False, help="Skip delete stage")
):
    """
    Создает E-mail письмо в Unisender. В буфер обмена помещает ID созданного письма.
    Если файл конфигурации существует, предлагает обновить или пересоздать.
    """

    htmlProcessor = HTMLProcessor(
        html_filename, images_folder, True, True)
    process_result = htmlProcessor.process()

    arhchive_path = archive_email(html_filename,
                                  process_result.get('inlined_html'),
                                  process_result.get('attachments'))
    process_result['data']['zip_size'] = os.path.getsize(arhchive_path)
    gmu_cfg = GmuConfig()

    # Если gmu.json существует, то обновляем
    if gmu_cfg.exists() and gmu_cfg.data.get("message_id", None) is not None:

        if force == False:
            # 1. Удаляем существующее письмо
            uClient.delete_message(gmu_cfg.data.get("message_id", None))

        # 2. Создаем новое письмо
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
        table_print("SUCCESS",
                    f"Письмо обновлено в Unisender. Message ID: {api_result.get('message_id', '')} | URL: https://cp.unisender.com/ru/v5/email-campaign/editor/{api_result.get('message_id', '')}?step=send")

    # Если gmu.json не существует, то создаем
    else:
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

        gmu_cfg.create(process_result.get('data', {}))

        table_print("SUCCESS",
                    f"Письмо загружено в Unisender. Message ID: {api_result.get('message_id', '')} | URL: https://cp.unisender.com/ru/v5/email-campaign/editor/{api_result.get('message_id', '')}?step=send")
