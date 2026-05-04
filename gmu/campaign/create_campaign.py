from typing import Optional

import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.git_sync import run_git_auto_sync
from gmu.utils.helpers import table_print, validate_datetime_string
from gmu.utils.project_state import update_project_config
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()
gmu_cfg = GmuConfig()


@app.command(name="c", hidden=True)
@app.command(name="create")
def create_campaign(
    message_id: Optional[int] = typer.Option(
        None, help="Message ID Unisender. Если значение пустое, то берется из gmu.json"),
    start_time: Optional[str] = typer.Option(
        None, help="Время начала кампании в формате 'YYYY-MM-DD HH:MM'"),
    now: bool = typer.Option(False, "--now", help="Запустить кампанию сразу, без start_time"),
    timezone: Optional[str] = typer.Option(None, help="Часовой пояс кампании. Unisender поддерживает UTC."),
    track_read: int = typer.Option(
        1, help="Отслеживать открытия. 1 - включить, 0 - выключить"),
    track_links: int = typer.Option(
        1, help="Отслеживать переходы. 1 - включить, 0 - выключить"),
    track_ga: int = typer.Option(
        1, help="UTM метки. 1 - включить, 0 - выключить. По умолчанию 1"),
    ga_medium: str = typer.Option('email', help="UTM medium"),
    ga_source: str = typer.Option('Unisender', help="UTM source"),
    ga_campaign: str = typer.Option('gefera', help="UTM campaign"),
    use_actual_version: bool = typer.Option(
        True,
        "--use-actual-version/--skip-actual-version",
        help="Перед созданием кампании проверить актуальную версию письма",
    )
):
    """
    Создает E-mail кампанию в Unisender.
    """
    if message_id is None:
        try:
            message_id = gmu_cfg.load().get('message_id', None)
        except FileNotFoundError as exc:
            raise ValueError(
                'message_id is not set and gmu.json was not found.') from exc

    if not message_id:
        raise ValueError('message_id not found in gmu.json.')

    if not now and not start_time:
        raise ValueError("Укажите --start-time 'YYYY-MM-DD HH:MM' или --now.")

    if start_time and not validate_datetime_string(start_time, '%Y-%m-%d %H:%M'):
        raise ValueError(
            f'start_time должно быть формата YYYY-MM-DD HH:MM! Текущее значение: {start_time}')

    uClient = UnisenderClient()
    if use_actual_version:
        version_info = uClient.get_actual_message_version(message_id)
        actual_version_id = version_info.get("actual_version_id")
        actual_message_id = int(actual_version_id) if actual_version_id else None
        if actual_message_id and actual_message_id != int(message_id):
            table_print(
                "INFO",
                f"Найдена актуальная версия письма: {actual_message_id}. Использую ее для кампании.",
            )
            message_id = actual_message_id
            if gmu_cfg.exists():
                gmu_cfg.update({
                    "message_id": message_id,
                    "actual_version_id": actual_message_id,
                })

    result = uClient.create_campaign(
        message_id=message_id,
        start_time=None if now else start_time,
        timezone=timezone,
        track_read=track_read,
        track_links=track_links,
        track_ga=track_ga,
        ga_medium=ga_medium,
        ga_source=ga_source,
        ga_campaign=ga_campaign,
    )

    campaign_id = result.get("campaign_id")
    campaign_status = result.get("status")
    update_project_config({
        "message_id": message_id,
        "campaign_id": campaign_id,
        "campaign_status": campaign_status,
    })

    table_print(
        "SUCCESS",
        f"Кампания создана. Campaign ID: {campaign_id} | Status: {campaign_status}",
    )
    run_git_auto_sync("создания кампании")
