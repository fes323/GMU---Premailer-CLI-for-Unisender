
import os

import requests
import typer
from dotenv import load_dotenv

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.utils import table_print

load_dotenv()
app = typer.Typer()
gmu_cfg = GmuConfig("gmu.json")


@app.command(name="delete")
def delete_to_wl(id: str = typer.Option(None, help="ID письма в Webletter")):

    if gmu_cfg.exists() is False:
        table_print("ERROR", 'Файл gmu.json не найден.')
        gmu_cfg.create()

    headers = {"Authorization": os.environ.get("WL_AUTH_TOKEN")}
    cfg_data = gmu_cfg.load()
    if id is not None:
        id = id
    else:
        id = cfg_data.get("webletter_id")

    if id is None:
        table_print(
            "ERROR", "Не задан ID письма в Webletter. Укажите его через параметр --id или в gmu.json.")
        return

    requests.delete(
        f"https://wl.gefera.ru/api/webletters/{id}",
        headers=headers,
    )

    cfg_data["webletter_id"] = None
    gmu_cfg.update(cfg_data)
    table_print("SUCCESS", f"Письмо успешно удалено из Webletter")
