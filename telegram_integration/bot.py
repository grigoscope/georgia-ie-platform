import requests
from django.conf import settings


class TelegramBotClient:
    API_BASE = 'https://api.telegram.org'

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN

    def request(
        self,
        method,
        payload=None,
    ):
        if not self.token:
            raise RuntimeError(
                'TELEGRAM_BOT_TOKEN не настроен.'
            )

        response = requests.post(
            (
                f'{self.API_BASE}/'
                f'bot{self.token}/'
                f'{method}'
            ),
            json=payload or {},
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get('ok'):
            raise RuntimeError(
                data.get(
                    'description',
                    'Ошибка Telegram Bot API',
                )
            )

        return data

    def send_message(
        self,
        *,
        chat_id,
        text,
        reply_markup=None,
    ):
        payload = {
            'chat_id': chat_id,
            'text': text,
        }

        if reply_markup is not None:
            payload['reply_markup'] = (
                reply_markup
            )

        return self.request(
            'sendMessage',
            payload,
        )

    def send_start_message(
        self,
        *,
        chat_id,
    ):
        return self.send_message(
            chat_id=chat_id,
            text=(
                'Georgia IE Accounting\n\n'
                'Доходы, инвойсы и налоги '
                'в одном приложении.'
            ),
            reply_markup={
                'inline_keyboard': [
                    [
                        {
                            'text': (
                                'Открыть приложение'
                            ),
                            'web_app': {
                                'url': (
                                    settings
                                    .MINI_APP_URL
                                ),
                            },
                        }
                    ]
                ]
            },
        )