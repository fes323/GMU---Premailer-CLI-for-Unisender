import bz2
import gzip
import os
import pathlib
import platform
import urllib.parse
from typing import Dict, Literal, Optional, Union

import pyperclip
import requests
from dotenv import load_dotenv

load_dotenv()


class UnisenderClient:
    def __init__(self):
        self.API_KEY = os.environ.get(
            "UNISENDER_API_KEY", "No API key provided")
        self.API_URL = os.environ.get(
            "UNISENDER_API_URL", "No API ulr provided")

        if self.API_KEY == "No API key provided":
            raise ValueError(
                "UNISENDER_API_KEY environment variables must be set.")
        if self.API_URL == "No API ulr provided":
            raise ValueError(
                "UNISENDER_API_URL environment variables must be set.")

    def _get_log_file_path(self):
        if platform.system() == "Windows":
            appdata = os.getenv("APPDATA")
            log_dir = pathlib.Path(appdata) / "GMU"
        else:
            home = pathlib.Path.home()
            log_dir = home / ".config" / "GMU"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "requests.log"

    def _log_https_request(self, url, params, request_method, extra_info=None):
        # Не логгируем api_key явно
        safe_params = {}
        for k, v in params.items():
            if k.lower() == "api_key":
                safe_params[k] = "***"
            elif isinstance(v, bytes):
                safe_params[k] = "<binary>"
            else:
                safe_params[k] = v
        qs = urllib.parse.urlencode(safe_params, doseq=True)
        log_text = f"{request_method} {url}?{qs}"
        if extra_info:
            log_text += f" | {extra_info}"
        logfile = self._get_log_file_path()
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(log_text + "\n")

    def u_request(
        self,
        method: str,
        params: dict = None,
        request_compression: str = None,
        response_compression: str = None,
    ):
        """
        request_compression: None, 'gzip', или 'bzip2'
        response_compression: None, 'gzip', или 'bzip2'
        """
        if params is None:
            params = {}

        # Извлекаем специальные параметры
        base_params = {"api_key": self.API_KEY}
        if request_compression:
            base_params["request_compression"] = request_compression
        if response_compression:
            base_params["response_compression"] = response_compression

        url = f"{self.API_URL}{method}"

        # Все остальные — остаются в params_to_compress
        params_to_compress = params.copy()

        # POST запрос передаём параметры по-разному:
        if request_compression in ("gzip", "bzip2"):
            # query string из base_params
            query_url = url + "?" + \
                urllib.parse.urlencode(base_params, doseq=True)
            # form data для сжатия — кроме api_key и request_compression
            form_encoded = urllib.parse.urlencode(
                params_to_compress, doseq=True).encode("utf-8")

            # Сжимаем данные в тело
            if request_compression == "gzip":
                payload = gzip.compress(form_encoded)
                headers = {"Content-Encoding": "gzip",
                           "Content-Type": "application/x-www-form-urlencoded"}
            else:
                payload = bz2.compress(form_encoded)
                headers = {"Content-Encoding": "bzip2",
                           "Content-Type": "application/x-www-form-urlencoded"}

            # Логгируем
            self._log_https_request(
                query_url, params_to_compress, "POST",
                extra_info=f"compressed:{request_compression}, size:{len(payload)}"
            )

            response = requests.post(query_url, data=payload, headers=headers)
        else:
            # Обычный POST: всё через form-data
            full_params = {**base_params, **params_to_compress}
            post_url = url
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            self._log_https_request(post_url, full_params, "POST")
            response = requests.post(
                post_url, data=full_params, headers=headers)

        # Проверяем статус и возвращаем результат
        try:
            resp_json = response.json()
        except Exception:
            resp_json = {
                "error": f"Failed to decode JSON: {response.text[:500]}"}

        if 'result' in resp_json and 'error' not in resp_json:
            return resp_json['result']
        else:
            raise Exception(resp_json.get('error', resp_json))

    def get_campaign_status(self, campaign_id: int) -> Union[Literal['error'], Dict[str, Union[str, int]]]:
        result = self.u_request('getCampaignStatus', {
            'campaign_id': campaign_id})
        return result

    def get_campaign_common_stats(self, campaign_id: int) -> Union[Literal['error'], Dict[str, Union[str, int]]]:
        result = self.u_request('getCampaignCommonStats', {
            'campaign_id': campaign_id})
        return result

    def update_email_message(
        self,
        id: int,
        sender_name: str,
        sender_email: str,
        subject: str,
        body: str,
        list_id: Optional[int] = None
    ) -> Union[Literal['error'], Dict[str, Union[str, int]]]:
        params = {
            'id': id,
            'sender_name': sender_name,
            'sender_email': sender_email,
            'subject': subject,
            'body': body
        }
        if list_id is not None:
            params['list_id'] = list_id

        result = self.u_request('updateEmailMessage', params)
        return result

    def create_email_message(
        self,
        sender_name: str,
        sender_email: str,
        subject: str,
        body: str,
        list_id: int,
        attachments: Optional[Dict[str, bytes]] = None,
        generate_text: int = 1,
        lang: str = 'ru',
        wrap_type: str = 'skip'
    ) -> Union[Literal['error'], Dict[str, Union[str, int]]]:
        """
        Создает E-mail письмо в Unisender.
        :param sender_name: Имя отправителя
        :param sender_email: Email отправителя
        :param subject: Тема E-mail
        :param body: Тело E-mail (HTML)
        :param list_id: ID списка рассылки
        :param attachments: Словарь с вложениями, где ключ - attachments[{filename}], значение - содержимое файла в виде байтов
        :param generate_text: Флаг для генерации текстовой версии письма (1 - да, 0 - нет)
        :param lang: Язык письма (по умолчанию 'ru')
        :param wrap_type: Тип обертки (по умолчанию 'skip'. Доступны значения: 'skip' - не применять, 'right' - по правому краю, 'left' - по левому краю, 'center' - по центру)
        :return: Результат выполнения запроса к API Unisender
        """
        params: Dict[str, Union[str, int, Dict[str, bytes]]] = {
            'sender_name': sender_name,
            'sender_email': sender_email,
            'subject': subject,
            'body': body,
            'list_id': list_id,
            'generate_text': generate_text,
            'lang': lang,
            'wrap_type': wrap_type,
        }
        if attachments:
            for filename, content in attachments.items():
                params[f'attachments[{filename}]'] = content

        result = self.u_request('createEmailMessage', params)

        pyperclip.copy(str(result.get('message_id', '')))

        return result

    def send_test_message(self, message_id: int, email: str) -> str:
        """
        Метод для отправки тестового email-сообщения. Отправить можно только уже созданное письмо (например, с помощью метода
        createEmailMessage). Отправлять можно на несколько адресов, перечисленных через запятую.
        """
        result = self.u_request(
            'sendTestEmail', {'id': message_id, 'email': email})
        if 'message' in result:
            return result.get('message', 'N/A')
        else:
            return result

    def delete_message(self, message_id: int) -> Union[Literal['error'], bool]:
        """
        Удаляет E-mail письмо в Unisender.
        :param message_id: ID E-mail кампании для удаления
        :return: Пустой словарь при успешном удалении или сообщение об ошибке
        """
        result = self.u_request('deleteMessage', {'message_id': message_id})
        if isinstance(result, dict):
            return True
        else:
            return result

    def create_campaign(
        self,
        message_id: int,
        start_time: str,
        track_read: int = 1,
        track_links: int = 1,
        track_ga: int = 1,
        ga_medium: str = 'email',
        ga_source: str = 'Unisender',
        ga_campaign: str = 'gefera'
    ) -> Union[Literal['error'], Dict[str, Union[str, int]]]:
        """
        Создает E-mail кампанию в Unisender. Формат времени: YYYY-MM-DD HH:MM
        """
        params = {
            'message_id': message_id,
            'start_time': start_time,
            'track_read': track_read,
            'track_links': track_links,
            'track_ga': track_ga,
            'ga_medium': ga_medium,
            'ga_source': ga_source,
            'ga_campaign': ga_campaign
        }
        result = self.u_request('createCampaign', params)
        return result
