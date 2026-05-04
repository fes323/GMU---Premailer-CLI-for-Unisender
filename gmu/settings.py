from __future__ import annotations

from typing import Optional

import typer

from gmu.utils.helpers import table_print
from gmu.utils.project_state import (
    ensure_project_config,
    get_letter_version,
    set_git_auto_sync,
    set_letter_version,
)

app = typer.Typer()


@app.command(name="show")
def show_settings():
    """Показать настройки текущего проекта."""
    _, data = ensure_project_config()
    settings = data.get("settings", {})

    table_print("INFO", f"letter_version: {data.get('letter_version', 0)}")
    table_print("INFO", f"git_auto_sync: {settings.get('git_auto_sync', False)}")
    table_print("INFO", f"message_id: {data.get('message_id')}")
    table_print("INFO", f"webletter_id: {data.get('webletter_id')}")
    table_print("INFO", f"campaign_id: {data.get('campaign_id')}")


@app.command(name="git")
def configure_git(
    enable: bool = typer.Option(False, "--enable", help="Включить git-автосинхронизацию"),
    disable: bool = typer.Option(False, "--disable", help="Выключить git-автосинхронизацию"),
):
    """Включить, выключить или показать статус git-автосинхронизации."""
    _, data = ensure_project_config()

    if enable and disable:
        raise typer.BadParameter("Используйте только один параметр: --enable или --disable.")

    if enable:
        set_git_auto_sync(True)
        table_print("SUCCESS", "Git-автосинхронизация включена.")
        return

    if disable:
        set_git_auto_sync(False)
        table_print("SUCCESS", "Git-автосинхронизация выключена.")
        return

    enabled = data.get("settings", {}).get("git_auto_sync", False)
    table_print("INFO", f"git_auto_sync: {enabled}")


@app.command(name="version")
def configure_version(
    version: Optional[int] = typer.Argument(None, help="Новое значение версии письма"),
):
    """Показать или вручную задать версию письма для commit message."""
    if version is None:
        table_print("INFO", f"letter_version: {get_letter_version()}")
        return

    set_letter_version(version)
    table_print("SUCCESS", f"letter_version установлен: {version}")
