import datetime

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


def validate_datetime_string(date_string, format_string):
    """
    Проверяет, является ли строка валидной датой и временем в заданном формате.

    Args:
        date_string (str): Строка для проверки.
        format_string (str): Ожидаемый формат даты и времени (например, "%Y-%m-%d %H:%M:%S").

    Returns:
        bool: True, если строка соответствует формату, False в противном случае.
    """
    try:
        datetime.datetime.strptime(date_string, format_string)
        return True
    except ValueError:
        return False
