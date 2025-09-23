import typer

from gmu.utils.archive import archive_email
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.HTMLProcessor import HTMLProcessor
from gmu.utils.logger import gmu_logger
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="create")
def create_message(
    list_id: str = typer.Option(20547119, help="ID списка рассылки"),
    html_filename: str = typer.Option(
        None, help="Имя HTML файла (по умолчанию первый .html в папке)"),
    images_folder: str = typer.Option("images", help="Папка с картинками"),
    force: bool = typer.Option(False, help="Skip delete message stage")
):
    """
    Создает E-mail письмо в Unisender. В буфер обмена помещает ID созданного письма.
    Если файл конфигурации существует, предлагает обновить или пересоздать.
    """

    gmu_cfg = GmuConfig()

    if force == False:
        if gmu_cfg.exists() and gmu_cfg.data.get("message_id", None) != None:
            gmu_logger.warning(
                f"Email exist in Unisender! Message id: {gmu_cfg.data.get('message_id', None)}")
            return table_print("WARNING", f"Email exist in Unisender! Message id: {gmu_cfg.data.get('message_id', None)}")

    htmlProcessor = HTMLProcessor(
        html_filename, images_folder, True, True)
    process_result = htmlProcessor.process()

    required_fields = ['sender_name', 'sender_email', 'subject']
    missing_fields = [
        field for field in required_fields if process_result.get(field) is None]

    if missing_fields:
        raise ValueError(
            f'Missing required fields: {", ".join(missing_fields)}')

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

    if gmu_cfg.exists():
        gmu_cfg.update(data)
    else:
        gmu_cfg.create(data)

    table_print("SUCCESS",
                f"Письмо загружено в Unisender. Message ID: {api_result.get('message_id', '')} | URL: https://cp.unisender.com/ru/v5/email-campaign/editor/{api_result.get('message_id', '')}?step=send")
