"""Settings shared by all letter projects for the current OS user."""
import os
import platform
from pathlib import Path

from gmu.utils.GmuConfig import GmuConfig


def user_config_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "gmu"
    return Path.home() / ".config" / "gmu"


def get_user_settings() -> dict:
    cfg = GmuConfig(str(user_config_dir() / "settings.json"))
    return cfg.load() if cfg.exists() else {"git_auto_sync": False}


def is_git_auto_sync_enabled() -> bool:
    return bool(get_user_settings().get("git_auto_sync", False))


def set_git_auto_sync(enabled: bool) -> bool:
    data = get_user_settings()
    data["git_auto_sync"] = enabled
    GmuConfig(str(user_config_dir() / "settings.json"), data).save()
    return True
