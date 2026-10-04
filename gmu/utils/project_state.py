from __future__ import annotations

from typing import Any

from gmu.utils.GmuConfig import GmuConfig, merge_with_defaults
from gmu.utils.user_settings import is_git_auto_sync_enabled, set_git_auto_sync


def ensure_project_config(path: str = "gmu.json") -> tuple[GmuConfig, dict[str, Any]]:
    cfg = GmuConfig(path)
    if not cfg.exists():
        cfg.create()
    data = cfg.migrate()
    return cfg, data


def load_project_config(path: str = "gmu.json") -> tuple[GmuConfig, dict[str, Any]]:
    cfg = GmuConfig(path)
    data = cfg.migrate()
    return cfg, data


def update_project_config(data: dict[str, Any], path: str = "gmu.json") -> bool:
    cfg = GmuConfig(path)
    if not cfg.exists():
        cfg.create(merge_with_defaults(data))
        return True
    return cfg.update(data)


def get_project_settings(path: str = "gmu.json") -> dict[str, Any]:
    _, data = ensure_project_config(path)
    return data.get("settings", {})


def get_letter_version(path: str = "gmu.json") -> int:
    _, data = ensure_project_config(path)
    return int(data.get("letter_version") or 0)


def set_letter_version(version: int, path: str = "gmu.json") -> bool:
    if version < 0:
        raise ValueError("Версия письма не может быть отрицательной.")
    return update_project_config({"letter_version": version}, path)


def bump_letter_version(path: str = "gmu.json") -> int:
    version = get_letter_version(path) + 1
    set_letter_version(version, path)
    return version
