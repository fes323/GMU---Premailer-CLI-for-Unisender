"""
SVG to PNG adapter backed by the Node.js resvg-js package.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


class SvgConversionError(RuntimeError):
    """Raised when SVG cannot be rendered to PNG."""


def _format_stderr(stderr: bytes) -> str:
    text = (stderr or b"").decode("utf-8", errors="replace").strip()
    if not text:
        return "No error output was returned by the Node.js process."

    lines = text.splitlines()
    tail = lines[-12:]
    return "\n".join(tail)


def svg_to_png(svg_bytes: bytes, output_width: Optional[int] = None) -> bytes:
    """Render SVG bytes to PNG bytes without requiring system Cairo/GTK."""
    script_path = Path(__file__).with_name("svg_to_png.js")
    node_binary = os.environ.get("GMU_NODE_BINARY", "node")
    args = [node_binary, str(script_path)]

    if output_width:
        args.extend(["--width", str(output_width)])

    try:
        completed = subprocess.run(
            args,
            input=svg_bytes,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SvgConversionError(
            "Node.js was not found. Install Node.js or set GMU_NODE_BINARY "
            "to the node executable path."
        ) from exc

    if completed.returncode != 0:
        raise SvgConversionError(
            "SVG to PNG conversion failed. Install npm dependencies with "
            "`npm install` in the project directory, then run GMU again.\n"
            f"{_format_stderr(completed.stderr)}"
        )

    return completed.stdout
