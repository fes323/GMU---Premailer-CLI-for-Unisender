from dotenv import load_dotenv
from rich.console import Console
from termcolor import colored

load_dotenv()
console = Console()


def table_print(status: str, message: str):
    colors = {
        "INFO": "cyan",
        "WARNING": "yellow",
        "SUCCESS": "green",
        "ERROR": "red",
        "INPUT": "white"
    }
    status_width = 10  # можно увеличить если статус длинный
    status_str = f"{status:<{status_width}}"
    if status == "INPUT":
        return input(f"{colored(status_str, colors.get(status, 'white'))}  {message}")
    else:
        return print(
            f"{colored(status_str, colors.get(status, 'white'))}  {message}"
        )
