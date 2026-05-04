import logging
import os
import pathlib
import platform


if platform.system() == "Windows":
    appdata = os.getenv("APPDATA")
    log_candidates = []
    if appdata:
        log_candidates.append(pathlib.Path(appdata) / "gmu" / 'gmu.log')
    log_candidates.append(pathlib.Path("gmu.log"))
else:
    # Linux и macOS
    home = pathlib.Path.home()
    log_candidates = [
        home / ".config" / "gmu" / "gmu.log",
        pathlib.Path("gmu.log"),
    ]

for log_candidate in log_candidates:
    try:
        log_candidate.parent.mkdir(parents=True, exist_ok=True)
        with open(log_candidate, "a", encoding="utf-8"):
            pass
        gmu_log = log_candidate
        break
    except OSError:
        continue
else:
    gmu_log = None


logging_kwargs = {
    "format": "[%(asctime)s] [%(levelname)s] %(message)s",
    "datefmt": "%m.%d.%Y %H:%M",
    "level": logging.INFO,
}
if gmu_log is not None:
    logging_kwargs["filename"] = str(gmu_log)
    logging_kwargs["encoding"] = "utf-8"

logging.basicConfig(**logging_kwargs)

gmu_logger = logging.getLogger('gmu_logger')
