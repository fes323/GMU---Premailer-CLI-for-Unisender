
import os
import pathlib
import platform
from typing import Optional

import typer
from dotenv import load_dotenv

from gmu.archive import app as archive_app
from gmu.campaign import app as campaign_app
from gmu.message import app as message_app
from gmu.settings import app as settings_app
from gmu.version import VERSION_TEXT, app as version_app
from gmu.webletter import app as webletter_app

BASE_DIR = pathlib.Path(__file__).parent
env_path = BASE_DIR / ".env"
APP_NAME = "gmu"

if not env_path.exists():
    # Если не нашли .env в BASE_DIR, ищем в профиле пользователя
    if platform.system() == "Windows":
        appdata = os.getenv("APPDATA")
        user_env_path = pathlib.Path(appdata) / "gmu" / ".env" if appdata else None
    else:
        # Linux и macOS
        home = pathlib.Path.home()
        user_env_path = home / ".config" / "gmu" / ".env"

    if user_env_path:
        env_path = user_env_path  # пробуем этот путь

if env_path.exists():
    load_dotenv(dotenv_path=env_path)


app = typer.Typer()


def _version_callback(value: bool):
    if value:
        print(VERSION_TEXT)
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Показать версию CLI",
    )
):
    pass


app.add_typer(version_app)
app.add_typer(archive_app)
app.add_typer(campaign_app, name="campaign")
app.add_typer(campaign_app, name="c", hidden=True)
app.add_typer(message_app, name="message")
app.add_typer(message_app, name="m", hidden=True)
app.add_typer(settings_app, name="settings")
app.add_typer(settings_app, name="cfg", hidden=True)
app.add_typer(webletter_app, name="webletter", hidden=True)
app.add_typer(webletter_app, name="wl")


if __name__ == "__main__":
    app()
