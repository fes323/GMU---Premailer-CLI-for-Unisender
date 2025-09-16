from typing import Optional

import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="delete")
def delete_message(id: Optional[int] = typer.Option(None, help="By default, it deletes the letter by message_id from gmu.json. If you specify message_id as a parameter, it will delete the letter by message_id from the command.")):
    """
    Удаляет E-mail письмо по ID.
    """

    gmu_cfg = GmuConfig()
    gmu_data = gmu_cfg.load()

    if gmu_data.get('message_id') and id == None:
        id = gmu_data.get('message_id')

    if id:
        result = uClient.delete_message(id)
    else:
        raise ValueError('Message_id is None!')

    if result:
        table_print("SUCCESS", f"Message {id} deleted successfully.")
        gmu_data['message_id'] = None
        gmu_cfg.update(gmu_data)
    else:
        table_print("ERROR", f"Failed to delete message {id}.")
