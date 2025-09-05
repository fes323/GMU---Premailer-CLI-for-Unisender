import typer

from .create_campaign import app as create_campaign_app
from .get_campaign_status import app as get_campaign_status_app

app = typer.Typer()


app.add_typer(get_campaign_status_app)
app.add_typer(create_campaign_app)
