import typer

from .create_message import app as create_message_app
from .delete_message import app as delete_message_app
from .send_test_email import app as send_test_email_app
from .update_message import app as update_message_app
from .upsert_message import app as create_or_update_message

app = typer.Typer()


app.add_typer(delete_message_app)
app.add_typer(create_message_app)
app.add_typer(send_test_email_app)
app.add_typer(update_message_app)
app.add_typer(create_or_update_message)
