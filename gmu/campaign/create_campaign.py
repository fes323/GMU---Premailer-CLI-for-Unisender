

import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import validate_datetime_string
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()
uClient = UnisenderClient()
gmu_cfg = GmuConfig.load()


@app.command(name="create")
def create_campaign(
    message_id: int = typer.Option(
        None, help="Message ID Unisender. Если значение пустое, то берется из gmu.json"),
    start_time: str = typer.Option(
        None, help="Время начала кампании в формате 'YYYY-MM-DD HH:MM'"),
    track_ga: int = typer.Option(
        1, help="UTM метки. 1 - включить, 0 - выключить. По умолчанию 1"),
    ga_medium: str = typer.Option('email', help="UTM medium"),
    ga_source: str = typer.Option('Unisender', help="UTM source"),
    ga_campaign: str = typer.Option('gefera', help="UTM campaign")
):
    """
    Создает E-mail кампанию в Unisender.
    """
    if message_id == None:
        try:
            message_id = gmu_cfg.get('message_id', None)
            if message_id:
                if validate_datetime_string(start_time, '%Y-%m-%d HH:MM'):
                    uClient.create_campaign(message_id=message_id, start_time=start_time,
                                            track_ga=track_ga, ga_medium=ga_medium, ga_source=ga_source, ga_campaign=ga_campaign)
                else:
                    raise ValueError(
                        f'start_time должно быть формата YYYY-MM-DD HH-MM! Текущее значение: {start_time}')
            else:
                raise ValueError(
                    f'message_id not fount in gmu.json.'
                )
        except Exception as e:
            raise Exception(f'Expetion: {e}')
