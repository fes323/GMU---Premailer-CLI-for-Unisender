import typer

from .delete_to_wl import app as delete_message_to_wl_app
from .upsert import app as deploy_to_wl_app

app = typer.Typer()

app.add_typer(deploy_to_wl_app)
app.add_typer(delete_message_to_wl_app)
