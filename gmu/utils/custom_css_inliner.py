"""
CSS inlining adapter backed by the Node.js Juice package.
"""

import os
import subprocess
from pathlib import Path


class JuiceInlinerError(RuntimeError):
    """Raised when Juice cannot inline CSS."""


def _format_stderr(stderr: str) -> str:
    stderr = (stderr or "").strip()
    if not stderr:
        return "No error output was returned by the Node.js process."

    lines = stderr.splitlines()
    tail = lines[-12:]
    return "\n".join(tail)


def inline_css_custom(html_content: str) -> str:
    """Inline CSS with Juice while keeping the historical Python API."""
    script_path = Path(__file__).with_name("juice_inliner.js")
    node_binary = os.environ.get("GMU_NODE_BINARY", "node")

    try:
        completed = subprocess.run(
            [node_binary, str(script_path)],
            input=html_content,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:
        raise JuiceInlinerError(
            "Node.js was not found. Install Node.js or set GMU_NODE_BINARY "
            "to the node executable path."
        ) from exc

    if completed.returncode != 0:
        raise JuiceInlinerError(
            "Juice CSS inlining failed. Install npm dependencies with "
            "`npm install` in the project directory, then run GMU again.\n"
            f"{_format_stderr(completed.stderr)}"
        )

    return completed.stdout
