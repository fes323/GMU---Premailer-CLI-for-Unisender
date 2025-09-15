
import os
import pathlib
import platform

import typer
from dotenv import load_dotenv

from gmu.archive import app as archive_app
from gmu.campaign import app as campaign_app
from gmu.message import app as message_app
from gmu.pdf import app as pdf_app
from gmu.version import app as version_app
from gmu.webletter import app as webletter_app

BASE_DIR = pathlib.Path(__file__).parent
env_path = BASE_DIR / ".env"
APP_NAME = "gmu"

if not env_path.exists():
    # Если не нашли .env в BASE_DIR, ищем в профиле пользователя
    if platform.system() == "Windows":
        appdata = os.getenv("APPDATA")
        user_env_path = pathlib.Path(appdata) / "gmu" / ".env"
        gmu_log = pathlib.Path(appdata) / "gmu" / 'gmu.log'
    else:
        # Linux и macOS
        home = pathlib.Path.home()
        user_env_path = home / ".config" / "gmu" / ".env"
        gmu_log = "var" / "log"

    env_path = user_env_path  # пробуем этот путь

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(
        f"[WARNING] Файл .env не найден ни в {BASE_DIR} ни в {env_path.parent}")
    raise FileNotFoundError


app = typer.Typer()


app.add_typer(version_app)
app.add_typer(archive_app)
app.add_typer(pdf_app)
app.add_typer(campaign_app, name="campaign")
app.add_typer(message_app, name="message")
app.add_typer(webletter_app, name="wl")


if __name__ == "__main__":
    app()
