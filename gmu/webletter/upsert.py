import os

import requests
import typer
from dotenv import load_dotenv

from gmu.utils.archive import archive_email
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.git_sync import run_git_auto_sync
from gmu.utils.helpers import table_print
from gmu.utils.HTMLprocessor import HTMLProcessor
from gmu.utils.project_lock import locked_project

load_dotenv()
app = typer.Typer()


@app.command(name="u", hidden=True)
@app.command(name="upsert")
@locked_project
def deploy_to_wl():
    gmu_cfg = GmuConfig("gmu.json")
    for key in ("WL_AUTH_TOKEN", "WL_ENDPOINT", "WL_URL"):
        if not os.environ.get(key):
            raise ValueError(f"Не задан {key} в .env.")
    images_folder = "images"

    htmlProcessor = HTMLProcessor(
        None, images_folder, False, False)
    process_result = htmlProcessor.process()

    arhchive_path = archive_email(htmlProcessor.html_filename,
                                  process_result.get('inlined_html'),
                                  process_result.get('attachments'))
    process_result['data']['zip_size'] = os.path.getsize(arhchive_path)
    zipName = os.path.basename(arhchive_path)
    headers = {"Authorization": os.environ.get("WL_AUTH_TOKEN")}
    cfg_data = gmu_cfg.load() if gmu_cfg.exists() else {}
    if not gmu_cfg.exists():
        gmu_cfg.save({})
    endpoint = os.environ["WL_ENDPOINT"].rstrip('/') + '/'

    with open(arhchive_path, "rb") as file:
        files = {"file": (zipName, file, "application/zip")}
        if cfg_data.get("webletter_id"):
            result = requests.put(
                endpoint + str(cfg_data['webletter_id']),
                headers=headers,
                files=files,
                timeout=(10, 120),
            )
        else:
            result = requests.post(
                endpoint + 'upload',
                headers=headers,
                files=files,
                timeout=(10, 120),
            )
    result.raise_for_status()
    try:
        result_json = result.json()
        if 'data' in result_json:
            resData = result_json.get("data")
            if not isinstance(resData, dict) or not resData.get("id"):
                raise ValueError("WebLetter не вернул ID письма.")
            process_result['data']['lang'] = process_result['data'].pop('language', None)
            process_result["data"]["webletter_id"] = resData.get("id", "")
            process_result["data"]["webletter_url"] = (
                f"{os.environ['WL_URL'].rstrip('/')}/{resData['id']}"
            )
            gmu_cfg.update(process_result.get("data", {}))

            table_print("SUCCESS",
                        f"Файл успешно загружен на WL - {process_result['data']['webletter_url']}")
            run_git_auto_sync("загрузки письма в WebLetter")
        else:
            raise RuntimeError(f"Ошибка при загрузке файла на WL: {result_json}")
    except Exception as e:
        raise RuntimeError(f"Ошибка при обработке ответа от WL: {e}") from e
