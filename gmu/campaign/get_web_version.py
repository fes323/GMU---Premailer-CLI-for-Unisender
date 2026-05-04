from typing import Optional

import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.project_state import update_project_config
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()


@app.command(name="w", hidden=True, help="Получить ссылку на веб-версию кампании")
@app.command(name="web", help="Получить ссылку на веб-версию кампании")
def get_web_version(campaign_id: Optional[int] = typer.Option(None, help="ID кампании")):
    gmu_cfg = GmuConfig()
    if campaign_id is None:
        if not gmu_cfg.exists():
            table_print("ERROR", "Не задан campaign_id и файл gmu.json не найден.")
            return
        campaign_id = gmu_cfg.load().get("campaign_id")

    if not campaign_id:
        table_print("ERROR", "Не задан campaign_id. Укажите --campaign-id или сохраните его в gmu.json.")
        return

    uClient = UnisenderClient()
    result = uClient.get_web_version(campaign_id)
    web_version_url = result.get("web_letter_link")
    letter_id = result.get("letter_id")

    update_project_config({
        "campaign_id": campaign_id,
        "web_version_url": web_version_url,
        "web_version_letter_id": letter_id,
    })

    table_print("SUCCESS", f"Web version: {web_version_url}")
