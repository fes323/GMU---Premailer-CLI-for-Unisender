import copy
import json
import os

from gmu.utils.helpers import table_print


DEFAULT_GMU_CONFIG = {
    "message_id": None,
    "message_url": None,
    "sender_name": None,
    "sender_email": None,
    "subject": None,
    "preheader": None,
    "webletter_id": None,
    "webletter_url": None,
    "campaign_id": None,
    "campaign_status": None,
    "campaign_creation_time": None,
    "campaign_start_time": None,
    "web_version_url": None,
    "web_version_letter_id": None,
    "actual_version_id": None,
    "lang": None,
    "zip_size": None,
    "created": None,
    "updated": None,
    "letter_version": 0,
    "settings": {
        "git_auto_sync": False
    }
}


def default_gmu_config() -> dict:
    return copy.deepcopy(DEFAULT_GMU_CONFIG)


def merge_with_defaults(data: dict | None) -> dict:
    source = data.copy() if data else {}
    result = default_gmu_config()

    for key, value in source.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key].update(value)
        else:
            result[key] = value

    if "size" in result and result.get("zip_size") is None:
        result["zip_size"] = result.get("size")
    result.pop("size", None)
    return result


class GmuConfig:
    def __init__(self, path='gmu.json', data=None):
        """
        path: путь к json-файлу с конфигурацией письма.
        data: словарь с параметрами письма (message_id, sender_name, sender_email, subject, html).
              Если data передан, то он сохранится после вызова save().
        """
        self.path = path
        self._data = data.copy() if data != None else None

    def exists(self):
        return os.path.exists(self.path)

    def load(self) -> dict:
        """Загрузить данные из файла в self._data (и вернуть их)."""
        if not self.exists():
            raise FileNotFoundError(f"Файл {self.path} не найден!")
        with open(self.path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        return self._data

    def migrate(self) -> dict:
        """Добавить в существующий конфиг новые поля, не меняя пользовательские значения."""
        data = merge_with_defaults(self.load())
        if data != self._data:
            self.save(data)
        return data

    def save(self, data=None):
        """Сохранить данные (или свои внутренние, если data не передан) в файл."""
        if data is not None:
            self._data = data.copy()
        if self._data is None:
            raise ValueError("Нет данных для сохранения!")
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

    def create(self, data=None):
        """
        Создать новый конфиг.
        Если файл уже есть — запросить подтверждение на перезапись.
        data: словарь с параметрами письма. Если не передан — пробует self._data.
        """
        if self.exists():
            answer = table_print(
                "INPUT",
                "Создать новый файл конфигурации и письмо в Unisender? (Y/N): "
            ).strip().lower()
            if answer != 'y':
                table_print(
                    "WARNING", "Создание нового файла конфигурации отменено.")
                return False
        if data is not None:
            self._data = merge_with_defaults(data)
        elif self._data is None:
            self._data = default_gmu_config()
        else:
            self._data = merge_with_defaults(self._data)
        self.save()
        table_print("SUCCESS", f"Новый файл конфигурации {self.path} создан.")
        return True

    def update(self, data=None):
        """
        Обновить существующий файл новыми значениями из data (или self._data).
        ВАЖНО: при обновлении мы делаем слияние: прежние поля сохраняются,
        а новые перезаписывают только соответствующие ключи.
        """
        if not self.exists():
            table_print(
                "ERROR", f"Файл {self.path} не найден. Обновление невозможно.")
            return False

        current_data = self.load()
        old_data = merge_with_defaults(current_data)  # загрузили текущие данные из файла
        # Если data не передано, берем текущее состояние self._data (или пустой словарь)
        if data is None:
            data = self._data or {}

        new_data = old_data.copy()
        for key, value in data.items():
            if isinstance(value, dict) and isinstance(new_data.get(key), dict):
                new_data[key] = {**new_data[key], **value}
            else:
                new_data[key] = value
        new_data = merge_with_defaults(new_data)

        if new_data != current_data:
            self.save(new_data)
        else:
            table_print(
                "INFO", "Данные в JSON не изменились. Обновление не требуется.")
        return True

    def delete(self):
        if self.exists():
            os.remove(self.path)
            table_print("SUCCESS", f"Файл {self.path} удален.")
            return True
        else:
            table_print(
                "WARNING", f"Файл {self.path} не найден. Удаление не требуется.")
            return False

    @property
    def data(self) -> dict:
        """
        Получить текущие данные (если не загружены — загрузить с диска).
        """
        if self._data is None:
            return self.load()
        return self._data

    @data.setter
    def data(self, value):
        self._data = value.copy()
