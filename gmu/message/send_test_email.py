import typer
from termcolor import colored

from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.Unisender import UnisenderClient
from gmu.utils.utils import log

app = typer.Typer()
uClient = UnisenderClient()


@app.command(name="test")
def send_test_message(message_id: int = typer.Option(None, help="ID письма"), email: str = typer.Option(
        None, help="Email адрес для отправки тестового письма (можно указать несколько адресов через запятую)")):
    """
    Метод для отправки тестового email-сообщения. Отправить можно только уже созданное письмо (например, с помощью метода
    createEmailMessage). Отправлять можно на несколько адресов, перечисленных через запятую.
    """
    if message_id is None:
        gmu_cfg = GmuConfig("gmu.json")
        if gmu_cfg.exists():
            message_id = gmu_cfg.load().get("message_id", None)
        if message_id is None:
            log("ERROR", "Не задан ID письма. Укажите его через параметр --message_id или в gmu.json.")
            return
    if email is None:
        log("ERROR",
            "Не задан email адрес для отправки тестового письма. Укажите его через параметр --email.")
        return

    result = uClient.send_test_message(message_id, email)
    if result:
        log("SUCCESS", "Message send successfully.")
        for email, email_result in result.items():
            # Проверяем словарь результата для каждого email
            if 'success' in email_result and email_result['success']:
                log("SUCCESS", f"{email} - SUCCESS")
            elif 'error' in email_result:
                log("ERROR", f"{email} - {email_result['error']}")
            else:
                log("WARNING", f"{email} - Unknown status")
    else:
        log("ERROR", "Failed to send message")
