from typing import Optional

import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.project_state import update_project_config
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()


@app.command(name="act", hidden=True)
@app.command(name="actual")
def actual_message_version(
    id: Optional[int] = typer.Option(None, help="Message ID Unisender"),
    save: bool = typer.Option(True, "--save/--no-save", help="Сохранить actual_version_id в gmu.json"),
):
    """Проверить актуальную версию письма в Unisender."""
    gmu_cfg = GmuConfig()
    if id is None:
        if not gmu_cfg.exists():
            table_print("ERROR", "Не задан message_id и файл gmu.json не найден.")
            return
        id = gmu_cfg.load().get("message_id")

    if not id:
        table_print("ERROR", "Не задан message_id. Укажите --id или сохраните его в gmu.json.")
        return

    uClient = UnisenderClient()
    result = uClient.get_actual_message_version(id)
    actual_version_id = result.get("actual_version_id")

    if save and actual_version_id:
        update_project_config({
            "message_id": actual_version_id,
            "actual_version_id": actual_version_id,
        })

    table_print("INFO", f"Message ID: {result.get('message_id')}")
    table_print("SUCCESS", f"Actual version ID: {actual_version_id}")
