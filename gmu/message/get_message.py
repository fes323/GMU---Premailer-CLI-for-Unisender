from typing import Any, Optional

import typer

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.project_state import update_project_config
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()


def _first_message(result: Any) -> dict[str, Any]:
    if isinstance(result, list):
        return result[0] if result else {}
    if isinstance(result, dict):
        return result
    return {}


@app.command(name="i", hidden=True)
@app.command(name="info")
def get_message(
    id: Optional[int] = typer.Option(None, help="Message ID Unisender"),
    save: bool = typer.Option(False, "--save/--no-save", help="Сохранить метаданные письма в gmu.json"),
):
    """Получить информацию о письме из Unisender."""
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
    message = _first_message(uClient.get_message(id))
    if not message:
        table_print("WARNING", f"Письмо {id} не найдено.")
        return

    active_version_id = message.get("active_version_id")
    actual_version_id = active_version_id or message.get("id")
    if save:
        update_project_config({
            "message_id": message.get("id") or id,
            "sender_name": message.get("sender_name"),
            "sender_email": message.get("sender_email"),
            "subject": message.get("subject"),
            "lang": message.get("lang_code"),
            "actual_version_id": actual_version_id,
            "created": message.get("created"),
            "updated": message.get("last_update"),
        })

    table_print("INFO", f"Message ID: {message.get('id')}")
    table_print("INFO", f"Subject: {message.get('subject')}")
    table_print("INFO", f"Sender: {message.get('sender_name')} <{message.get('sender_email')}>")
    table_print("INFO", f"Created: {message.get('created')}")
    table_print("INFO", f"Updated: {message.get('last_update')}")
    table_print("INFO", f"Actual version ID: {actual_version_id}")
