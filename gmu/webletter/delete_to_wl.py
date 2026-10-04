
import os

import requests
import typer
from dotenv import load_dotenv

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.git_sync import run_git_auto_sync
from gmu.utils.helpers import table_print
from gmu.utils.project_lock import locked_project

load_dotenv()
app = typer.Typer()


@app.command(name="d", hidden=True)
@app.command(name="delete")
@locked_project
def delete_to_wl(id: str = typer.Option(None, help="ID письма в Webletter")):
    gmu_cfg = GmuConfig("gmu.json")

    headers = {"Authorization": os.environ.get("WL_AUTH_TOKEN")}
    cfg_data = gmu_cfg.load() if gmu_cfg.exists() else {}
    if id is not None:
        id = id
    else:
        id = cfg_data.get("webletter_id")

    if id is None:
        table_print(
            "ERROR", "Не задан ID письма в Webletter. Укажите его через параметр --id или в gmu.json.")
        return

    endpoint = os.environ.get("WL_ENDPOINT", "https://wl.gefera.ru/api/webletters/")

    if not os.environ.get("WL_AUTH_TOKEN"):
        raise ValueError("Не задан WL_AUTH_TOKEN.")
    response = requests.delete(
        f"{endpoint.rstrip('/')}/{id}",
        headers=headers,
        timeout=(10, 120),
    )
    response.raise_for_status()

    if str(cfg_data.get("webletter_id")) == str(id):
        gmu_cfg.update({"webletter_id": None, "webletter_url": None})
    table_print("SUCCESS", f"Письмо успешно удалено из Webletter")
    run_git_auto_sync("удаления письма из WebLetter")
