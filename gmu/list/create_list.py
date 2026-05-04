import typer

from gmu.utils.archive import archive_email
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.helpers import table_print
from gmu.utils.HTMLProcessor import HTMLProcessor
from gmu.utils.logger import gmu_logger
from gmu.utils.Unisender import UnisenderClient

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="create")
def create_list(
        title: str = typer.Option(None, help="Title for list")):
    ...
