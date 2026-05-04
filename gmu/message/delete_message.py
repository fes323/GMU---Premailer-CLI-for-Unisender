from typing import Optional

import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.git_sync import run_git_auto_sync
from gmu.utils.helpers import table_print
from gmu.utils.project_state import update_project_config
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()


@app.command(name="d", hidden=True)
@app.command(name="delete")
def delete_message(id: Optional[int] = typer.Option(None, help="By default, it deletes the letter by message_id from gmu.json. If you specify message_id as a parameter, it will delete the letter by message_id from the command.")):
    """
    Удаляет E-mail письмо по ID.
    """
    gmu_cfg = GmuConfig()
    gmu_data = gmu_cfg.load() if gmu_cfg.exists() else {}

    if gmu_data.get('message_id') and id == None:
        id = gmu_data.get('message_id')

    if not id:
        raise ValueError('Message_id is None!')

    uClient = UnisenderClient()
    result = uClient.delete_message(id)

    if result:
        table_print("SUCCESS", f"Message {id} deleted successfully.")
        gmu_data['message_id'] = None
        gmu_data['message_url'] = None
        gmu_data['actual_version_id'] = None
        update_project_config(gmu_data)
        run_git_auto_sync("удаления письма из Unisender")
    else:
        table_print("ERROR", f"Failed to delete message {id}.")
