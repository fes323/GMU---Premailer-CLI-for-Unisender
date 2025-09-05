import glob
import os

import requests
import typer
from dotenv import load_dotenv
from termcolor import colored

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.utils import archive_email, get_html_and_attachments

load_dotenv()
app = typer.Typer()
gmu_cfg = GmuConfig("gmu.json")


@app.command(name="wl")
def deploy_to_wl():
    html_filename = glob.glob("*.html")[0]
    images_folder = "images"
    if gmu_cfg.exists() is False:
        gmu_cfg.create()

    sender_name, sender_email, subject, html, attachments = get_html_and_attachments(
        html_filename, images_folder, replace_src=False
    )

    arhchive_path = archive_email(html_filename, html, attachments)

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
            "https://wl.gefera.ru/api/webletters/upload",
            headers=headers,
            files=files
        )
    else:
        result = requests.post(
            "https://wl.gefera.ru/api/webletters/upload",
            headers=headers,
            files=files
        )
    if 'data' in result.json():
        resData = result.json().get("data")
        data = {
            "message_id": None,
            "sender_name": sender_name or "",
            "sender_email": sender_email or "",
            "subject": subject or "",
            "webletter_id": resData.get("id", "")
        }
    gmu_cfg.update(data)

    print("SUCCESS",
          f"Файл успешно загружен на WL - https://wl.gefera.ru/{data.get('webletter_id')}")
