import typer
from utils.Unisender import UnisenderClient

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="create")
def create_campaign(
    message_id: int,
    start_time: str = typer.Option(
        None, help="Время начала кампании в формате 'YYYY-MM-DD HH:MM'"),
):
    """
    Создает E-mail кампанию в Unisender.
    """
    uClient.create_campaign(message_id, start_time)
