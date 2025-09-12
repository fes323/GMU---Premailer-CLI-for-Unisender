from typing import Optional

import typer
from utils.GmuConfig import GmuConfig
from utils.Unisender import UnisenderClient
from utils.utils import table_print

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="test")
def send_test_message(id: Optional[int] = typer.Option(None, help="Unisender Letter ID"),
                      email: str = typer.Option(
                          None, help="Email адрес для отправки тестового письма (можно указать несколько адресов через запятую)")
                      ):
    """
    Метод для отправки тестового email-сообщения. Отправить можно только уже созданное письмо (например, с помощью метода
    createEmailMessage). Отправлять можно на несколько адресов, перечисленных через запятую.
    """
    if id is None:
        gmu_cfg = GmuConfig("gmu.json")
        if gmu_cfg.exists():
            id = gmu_cfg.load().get("message_id", None)
        if id is None:
            table_print(
                "ERROR", "Не задан ID письма. Укажите его через параметр --message_id или в gmu.json.")
            return
    if email is None:
        table_print("ERROR",
                    "Не задан email адрес для отправки тестового письма. Укажите его через параметр --email.")
        return

    result = uClient.send_test_message(id, email)
    if result:
        table_print("SUCCESS", "Message send successfully.")
        for email, email_result in result.items():
            # Проверяем словарь результата для каждого email
            if 'success' in email_result and email_result['success']:
                table_print("SUCCESS", f"{email} - SUCCESS")
            elif 'error' in email_result:
                table_print("ERROR", f"{email} - {email_result['error']}")
            else:
                table_print("WARNING", f"{email} - Unknown status")
    else:
        table_print("ERROR", "Failed to send message")
