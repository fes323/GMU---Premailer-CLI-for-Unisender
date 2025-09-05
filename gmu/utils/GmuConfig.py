import json
import os

from termcolor import colored

from gmu.utils.utils import log


class GmuConfig:
    def __init__(self, path='gmu.json', data=None):
        """
        path: путь к json-файлу с конфигурацией письма.
        data: словарь с параметрами письма (message_id, sender_name, sender_email, subject, html).
              Если data передан, то он сохранится после вызова save().
        """
        self.path = path
        self._data = data.copy() if data is not None else None

    def exists(self):
        return os.path.exists(self.path)

    def load(self):
        """Загрузить данные из файла в self._data (и вернуть их)."""
        if not self.exists():
            raise FileNotFoundError(f"Файл {self.path} не найден!")
        with open(self.path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        return self._data

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
            answer = log("INPUT",
                         "Создать новый файл конфигурации и письмо в Unisender? (Y/N): "
                         ).strip().lower()
            if answer != 'y':
                log("WARNING", "Создание нового файла конфигурации отменено.")
                return False
        if data is not None:
            self._data = data.copy()
        elif self._data is None:
            # Шаблон по умолчанию
            self._data = {
                "message_id": "",
                "sender_name": "",
                "sender_email": "",
                "subject": "",
                "webletter_id": ""
            }
        self.save()
        log("SUCCESS",
            f"Новый файл конфигурации {self.path} создан.")
        return True

    def update(self, data=None):
        """
        Обновить существующий файл новыми значениями из data (или self._data).
        """
        if not self.exists():
            log("ERROR", f"Файл {self.path} не найден. Обновление невозможно.")
            return False
        old_data = self.load()
        if data is not None:
            self._data = data.copy()
        if self._data != old_data:
            self.save()
        else:
            log("INFO",
                "Данные в JSON не изменились. Обновление не требуется.")
        return True

    def delete(self):
        if self.exists():
            os.remove(self.path)
            log("SUCCESS", f"Файл {self.path} удален.")
            return True
        else:
            log("WARNING",
                f"Файл {self.path} не найден. Удаление не требуется.")
            return False

    @property
    def data(self):
        """
        Получить текущие данные (если не загружены — загрузить с диска).
        """
        if self._data is None:
            return self.load()
        return self._data

    @data.setter
    def data(self, value):
        self._data = value.copy()
