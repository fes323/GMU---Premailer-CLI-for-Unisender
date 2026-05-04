from __future__ import annotations

import subprocess
from pathlib import Path

from gmu.utils.helpers import table_print
from gmu.utils.project_state import bump_letter_version, is_git_auto_sync_enabled


def _format_output(stdout: str, stderr: str) -> str:
    output = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
    if len(output) > 1200:
        return output[-1200:]
    return output


def _run_git(args: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return False, "git не найден в PATH."

    output = _format_output(result.stdout, result.stderr)
    return result.returncode == 0, output


def run_git_auto_sync(action_name: str = "обновления письма") -> bool:
    if not is_git_auto_sync_enabled():
        return False

    ok, output = _run_git(["rev-parse", "--is-inside-work-tree"])
    if not ok:
        table_print(
            "WARNING",
            f"Git-синхронизация включена, но текущая папка не похожа на git-репозиторий. {output}",
        )
        return False

    ok, output = _run_git(["pull"])
    if not ok:
        table_print("ERROR", f"git pull не выполнен после {action_name}. {output}")
        return False

    version = bump_letter_version()
    commit_message = f"{Path.cwd().name} v {version}"

    ok, output = _run_git(["add", "./"])
    if not ok:
        table_print("ERROR", f"git add ./ не выполнен. {output}")
        return False

    ok, output = _run_git(["commit", "-m", commit_message])
    if not ok:
        table_print("ERROR", f"git commit не выполнен. {output}")
        return False

    ok, output = _run_git(["push"])
    if not ok:
        table_print("ERROR", f"git push не выполнен. {output}")
        return False

    table_print("SUCCESS", f"Git-синхронизация выполнена: {commit_message}")
    return True
