from typing import Optional

import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.Unisender import UnisenderClient
from gmu.utils.utils import table_print

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="delete")
def delete_message(id: Optional[int] = typer.Option(None, help="By default, it deletes the letter by message_id from gmu.json. If you specify message_id as a parameter, it will delete the letter by message_id from the command.")):
    """
    Удаляет E-mail письмо по ID.
    """
    gmu_cfg = GmuConfig()
    gmu_cfg.load()

    if gmu_cfg.exists() and id == None:
        id = gmu_cfg.get('message_id')

    if id:
        result = uClient.delete_message(id)
    else:
        raise ValueError('Message_id is None!')

    if result:
        table_print("SUCCESS", f"Message {id} deleted successfully.")
        gmu_cfg['message_id'] = ""
        gmu_cfg.save()
    else:
        table_print("ERROR", f"Failed to delete message {id}.")
