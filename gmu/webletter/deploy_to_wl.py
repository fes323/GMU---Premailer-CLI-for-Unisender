import glob
import os

import requests
import typer
from dotenv import load_dotenv
from termcolor import colored

from gmu.utils import HTMLprocessor
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.utils import archive_email

load_dotenv()
app = typer.Typer()
gmu_cfg = GmuConfig("gmu.json")


@app.command(name="upsert")
def deploy_to_wl():
    html_filename = glob.glob("*.html")[0]
    images_folder = "images"

    if not gmu_cfg.exists():
        gmu_cfg.create()

    process_result = HTMLprocessor(
        html_filename, images_folder, False
    ).process()

    arhchive_path = archive_email(html_filename, process_result.get(
        'inlined_html'), process_result.get('attachments'))

    if not os.environ.get("WL_AUTH_TOKEN"):
        print(
            colored(
                "[ERROR] Не задан WL_AUTH_TOKEN в переменных окружения. "
                "Пожалуйста, установите его перед использованием этой команды.",
                "red"
            )
        )
        return
    zipName = os.path.basename(arhchive_path)
    headers = {"Authorization": os.environ.get("WL_AUTH_TOKEN")}
    files = {"file": (zipName, open(arhchive_path, "rb"), "application/zip")}
    cfg_data = gmu_cfg.load()
    if cfg_data.get("webletter_id"):
        result = requests.put(
            str(os.environ.get("WL_ENDPOINT")),
            headers=headers,
            files=files
        )
    else:
        result = requests.post(
            str(os.environ.get("WL_ENDPOINT")),
            headers=headers,
            files=files
        )
    if 'data' in result.json():
        resData = result.json().get("data")
        cfg_data["webletter_id"] = resData.get("id", "")

    gmu_cfg.update(cfg_data)

    print("SUCCESS",
          f"Файл успешно загружен на WL - {os.environ.get('WL_URL')}{resData.get('id')}")
