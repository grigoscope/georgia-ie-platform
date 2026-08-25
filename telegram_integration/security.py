import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from django.conf import settings


class TelegramInitDataError(ValueError):
    """Ошибка проверки Telegram initData."""


class TelegramInitDataVerifier:
    """Проверка подписи Telegram Mini App."""

    @classmethod
    def verify(cls, init_data):
        if not init_data:
            raise TelegramInitDataError('init_data обязателен.')

        pairs = parse_qsl(
            init_data,
            keep_blank_values=True,
        )

        data = {}

        for key, value in pairs:
            if key in data:
                raise TelegramInitDataError('init_data содержит повторяющиеся параметры.')

            data[key] = value

        received_hash = data.pop(
            'hash',
            None,
        )

        if not received_hash:
            raise TelegramInitDataError('Отсутствует hash.')

        bot_token = settings.TELEGRAM_BOT_TOKEN

        if not bot_token:
            raise TelegramInitDataError('Telegram Bot Token не настроен.')

        data_check_string = '\n'.join((f'{key}={value}' for key, value in sorted(data.items())))

        secret_key = hmac.new(
            b'WebAppData',
            bot_token.encode(),
            hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            received_hash,
            calculated_hash,
        ):
            raise TelegramInitDataError('Неверная подпись Telegram.')

        try:
            auth_date = int(data['auth_date'])

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise TelegramInitDataError('Некорректный auth_date.') from error

        current_timestamp = int(time.time())

        max_age = settings.TELEGRAM_INIT_DATA_MAX_AGE

        age = current_timestamp - auth_date

        if age < -30:
            raise TelegramInitDataError('auth_date находится в будущем.')

        if age > max_age:
            raise TelegramInitDataError('Telegram init_data устарел.')

        try:
            telegram_user = json.loads(data['user'])

        except (
            KeyError,
            json.JSONDecodeError,
            TypeError,
        ) as error:
            raise TelegramInitDataError('Некорректные данные Telegram-пользователя.') from error

        telegram_user_id = telegram_user.get('id')

        if not isinstance(
            telegram_user_id,
            int,
        ):
            raise TelegramInitDataError('Некорректный Telegram ID.')

        return {
            'raw': data,
            'user': telegram_user,
            'auth_date': auth_date,
        }
