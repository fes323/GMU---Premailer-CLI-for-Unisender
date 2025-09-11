import typer
from termcolor import colored

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.Unisender import UnisenderClient
from gmu.utils.utils import table_print

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="delete")
def delete_message(message_id: int):
    """
    Удаляет E-mail письмо по ID.
    """
    result = uClient.delete_message(message_id)

    gmu_cfg = GmuConfig(path="gmu.json")
    gmu_cfg.delete()

    if result:
        table_print("SUCCESS", f"Message {message_id} deleted successfully.")
    else:
        table_print("ERROR", f"Failed to delete message {message_id}.")
