import glob
import os

import requests
import typer
from dotenv import load_dotenv
from termcolor import colored

from gmu.utils.archive import archive_email
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.HTMLprocessor import HTMLProcessor

load_dotenv()
app = typer.Typer()
gmu_cfg = GmuConfig("gmu.json")


@app.command(name="upsert")
def deploy_to_wl():
    html_filename = glob.glob("*.html")[0]
    images_folder = "images"

    if not gmu_cfg.exists():
        gmu_cfg.create()

    htmlProcessor = HTMLProcessor(
        html_filename, images_folder, False, False)
    process_result = htmlProcessor.process()

    arhchive_path = archive_email(html_filename,
                                  process_result.get('inlined_html'),
                                  process_result.get('attachments'))
    process_result['data']['zip_size'] = os.path.getsize(arhchive_path)
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
    cfg_data = gmu_cfg.load()

    with open(arhchive_path, "rb") as file:
        files = {"file": (zipName, file, "application/zip")}
        if cfg_data.get("webletter_id"):
            result = requests.put(
                str(os.environ.get("WL_ENDPOINT") +
                    cfg_data.get('webletter_id')),
                headers=headers,
                files=files
            )
        else:
            result = requests.post(
                str(os.environ.get("WL_ENDPOINT") + 'upload'),
                headers=headers,
                files=files
            )
    try:
        result_json = result.json()
        if 'data' in result_json:
            resData = result_json.get("data")
            process_result["data"]["webletter_id"] = resData.get("id", "")
            gmu_cfg.update(process_result.get("data", {}))

            table_print("SUCCESS",
                        f"Файл успешно загружен на WL - {os.environ.get('WL_URL')}{resData.get('id')}")
        else:
            table_print(
                "ERROR", f"Ошибка при загрузке файла на WL: {result_json}")
    except Exception as e:
        table_print("ERROR", f"Ошибка при обработке ответа от WL: {e}")
