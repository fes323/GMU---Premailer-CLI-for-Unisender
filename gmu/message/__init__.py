import typer

from .create_message import app as create_message_app
from .delete_message import app as delete_message_app
from .delete_to_wl import app as delete_message_to_wl_app
from .deploy_to_wl import app as deploy_to_wl_app
from .send_test_email import app as send_test_email_app
from .update_message import app as update_message_app

app = typer.Typer()

app.add_typer(delete_message_app)
app.add_typer(create_message_app)
app.add_typer(send_test_email_app)
app.add_typer(update_message_app)
app.add_typer(deploy_to_wl_app)
app.add_typer(delete_message_to_wl_app)
