import typer
from utils.Unisender import UnisenderClient

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="status", help="Получить статус кампании")
def get_campaign_status(campaign_id: int = typer.Argument(..., help="ID")):
    status = uClient.get_campaign_status(campaign_id)
    print(f"Status of campaign {campaign_id}: {status}")
