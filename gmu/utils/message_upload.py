"""One upload workflow for create, upsert and update commands."""
import os
import pyperclip

from gmu.utils.archive import archive_email
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.git_sync import run_git_auto_sync
from gmu.utils.helpers import table_print
from gmu.utils.HTMLprocessor import HTMLProcessor
from gmu.utils.project_lock import project_lock
from gmu.utils.Unisender import UnisenderAPIError, UnisenderClient
from gmu.utils.unisender_urls import build_unisender_message_url


def upload_message(list_id, html_filename, images_folder, mode="upsert", force=False):
    with project_lock():
        cfg = GmuConfig()
        data = cfg.load() if cfg.exists() else {}
        if data.get("message_creation_pending"):
            raise ValueError(
                "Результат предыдущего создания письма неизвестен. Проверьте Unisender. "
                "Если письмо создано, сохраните его ID: gmu m info --id ID --save. "
                "Если письма нет, установите message_creation_pending=false в gmu.json."
            )
        old_id = data.get("message_id")
        if mode == "create" and old_id and not force:
            table_print("WARNING", f"Письмо уже существует: {old_id}. Для обновления: gmu m u.")
            return
        if mode == "update" and not old_id:
            raise ValueError("Нет message_id в gmu.json. Для создания: gmu m u.")
        # Validate locally before deleting a remote message.
        list_id = int(list_id)
        if list_id <= 0:
            raise ValueError("list_id должен быть положительным числом.")
        processor = HTMLProcessor(html_filename, images_folder, True, True)
        result = processor.process()
        metadata = result["data"]
        missing = [key for key in ("sender_name", "sender_email", "subject")
                   if not metadata.get(key) or not str(metadata[key]).strip()]
        if missing:
            raise ValueError(f"Не заполнены обязательные поля HTML: {', '.join(missing)}")
        metadata["lang"] = metadata.pop("language", None) or "ru"
        archive_path = archive_email(processor.html_filename, result["inlined_html"], result["attachments"])
        metadata["zip_size"] = os.path.getsize(archive_path)
        client = UnisenderClient()
        # Fail before the request if configuration cannot be saved.
        if not cfg.exists():
            cfg.save({})
        if old_id:
            if client.delete_message(old_id) is not True:
                raise RuntimeError("Удаление старого письма не подтверждено; создание отменено.")
            cfg.update({"message_id": None, "message_url": None, "actual_version_id": None})
        cfg.update({"message_creation_pending": True})
        try:
            api_result = client.create_email_message(
                sender_name=metadata["sender_name"], sender_email=metadata["sender_email"],
                subject=metadata["subject"], body=result["inlined_html"], list_id=list_id,
                attachments=result["attachments"], lang=metadata["lang"],
            )
        except UnisenderAPIError:
            # Explicit rejection; retrying is safe.
            cfg.update({"message_creation_pending": False})
            raise
        message_id = api_result.get("message_id") if isinstance(api_result, dict) else None
        if not message_id:
            raise RuntimeError("API не вернул message_id. Проверьте Unisender перед повторной загрузкой.")
        metadata.update(message_id=message_id, message_url=build_unisender_message_url(message_id),
                        actual_version_id=None, message_creation_pending=False)
        try:
            cfg.update(metadata)
        except OSError as exc:
            raise RuntimeError(
                f"Письмо создано (ID {message_id}), но gmu.json не сохранён. "
                f"Восстановите привязку: gmu m info --id {message_id} --save."
            ) from exc
        try:
            pyperclip.copy(str(message_id))
        except (pyperclip.PyperclipException, OSError):
            pass
        table_print("SUCCESS", f"Письмо {'обновлено' if old_id else 'создано'}. "
                    f"Message ID: {message_id} | URL: {metadata['message_url']}")
        run_git_auto_sync("загрузки письма в Unisender")
