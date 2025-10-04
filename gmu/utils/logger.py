import logging
import os
import pathlib
import platform

if platform.system() == "Windows":
    appdata = os.getenv("APPDATA")
    if appdata:
        gmu_log = pathlib.Path(appdata) / "gmu" / 'gmu.log'
        # Создаем директорию если она не существует
        gmu_log.parent.mkdir(parents=True, exist_ok=True)
    else:
        gmu_log = pathlib.Path("gmu.log")
else:
    # Linux и macOS
    home = pathlib.Path.home()
    gmu_log = home / "var" / "log" / "gmu.log"
    # Создаем директорию если она не существует
    gmu_log.parent.mkdir(parents=True, exist_ok=True)


logging.basicConfig(
    filename=str(gmu_log),
    encoding='utf-8',
    format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%m.%d.%Y %H:%M',
    level=logging.INFO
)

gmu_logger = logging.getLogger('gmu_logger')
