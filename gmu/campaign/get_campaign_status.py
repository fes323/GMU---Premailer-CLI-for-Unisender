from typing import Optional

import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.project_state import update_project_config
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()


@app.command(name="s", hidden=True, help="Получить статус кампании")
@app.command(name="status", help="Получить статус кампании")
def get_campaign_status(campaign_id: Optional[int] = typer.Argument(None, help="ID")):
    gmu_cfg = GmuConfig()
    if campaign_id is None:
        if not gmu_cfg.exists():
            table_print("ERROR", "Не задан campaign_id и файл gmu.json не найден.")
            return
        campaign_id = gmu_cfg.load().get("campaign_id")

    if not campaign_id:
        table_print("ERROR", "Не задан campaign_id. Укажите его аргументом или сохраните в gmu.json.")
        return

    uClient = UnisenderClient()
    status = uClient.get_campaign_status(campaign_id)
    update_project_config({
        "campaign_id": campaign_id,
        "campaign_status": status.get("status"),
        "campaign_creation_time": status.get("creation_time"),
        "campaign_start_time": status.get("start_time"),
    })
    table_print("INFO", f"Campaign ID: {campaign_id}")
    table_print("INFO", f"Status: {status.get('status')}")
    if status.get("creation_time"):
        table_print("INFO", f"Creation time: {status.get('creation_time')}")
    if status.get("start_time"):
        table_print("INFO", f"Start time: {status.get('start_time')}")
