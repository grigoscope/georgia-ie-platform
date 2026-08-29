from rest_framework.exceptions import (
    ErrorDetail,
)
from rest_framework.renderers import (
    JSONRenderer,
)

ERROR_CODES = {
    400: 'validation_error',
    401: 'authentication_error',
    403: 'permission_denied',
    404: 'not_found',
    405: 'method_not_allowed',
    409: 'conflict',
    422: 'unprocessable_entity',
    429: 'rate_limited',
    500: 'server_error',
    502: 'upstream_error',
    503: 'service_unavailable',
}


ERROR_MESSAGES = {
    400: 'Проверьте данные.',
    401: 'Требуется авторизация.',
    403: 'Доступ запрещён.',
    404: 'Объект не найден.',
    405: 'Метод не поддерживается.',
    409: 'Конфликт состояния ресурса.',
    422: 'Данные не могут быть обработаны.',
    429: 'Слишком много запросов.',
    500: 'Внутренняя ошибка сервера.',
    502: 'Ошибка внешнего сервиса.',
    503: 'Сервис временно недоступен.',
}


class APIJSONRenderer(JSONRenderer):
    """
    Приводит все ошибочные JSON-ответы
    к единому формату API.
    """

    def render(
        self,
        data,
        accepted_media_type=None,
        renderer_context=None,
    ):
        response = None

        if renderer_context:
            response = renderer_context.get('response')

        if response is not None and response.status_code >= 400:
            data = self._error_payload(
                data=data,
                status_code=(response.status_code),
            )

        return super().render(
            data,
            accepted_media_type,
            renderer_context,
        )

    @classmethod
    def _error_payload(
        cls,
        *,
        data,
        status_code,
    ):
        if isinstance(data, dict) and 'error' in data:
            return data

        code = ERROR_CODES.get(
            status_code,
            'api_error',
        )

        message = ERROR_MESSAGES.get(
            status_code,
            'Ошибка API.',
        )

        fields = {}

        plain_data = cls._plain(data)

        if status_code == 400:
            if isinstance(
                plain_data,
                dict,
            ):
                detail = plain_data.get('detail')

                if detail:
                    message = cls._first_message(detail) or message

                fields = {
                    key: value
                    for key, value in plain_data.items()
                    if key
                    not in {
                        'detail',
                        'code',
                    }
                }

            elif isinstance(
                plain_data,
                list,
            ):
                fields = {'non_field_errors': (plain_data)}

            elif plain_data:
                message = str(plain_data)

        else:
            if isinstance(
                plain_data,
                dict,
            ):
                detail = plain_data.get('detail')

                if detail:
                    message = cls._first_message(detail) or message

            elif plain_data:
                message = cls._first_message(plain_data) or message

        return {
            'error': {
                'code': code,
                'message': message,
                'fields': fields,
            }
        }

    @classmethod
    def _plain(cls, value):
        if isinstance(
            value,
            ErrorDetail,
        ):
            return str(value)

        if isinstance(value, dict):
            return {str(key): cls._plain(item) for key, item in value.items()}

        if isinstance(
            value,
            (list, tuple),
        ):
            return [cls._plain(item) for item in value]

        return value

    @classmethod
    def _first_message(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            return value

        if isinstance(value, dict):
            for item in value.values():
                message = cls._first_message(item)

                if message:
                    return message

            return None

        if isinstance(
            value,
            (list, tuple),
        ):
            for item in value:
                message = cls._first_message(item)

                if message:
                    return message

            return None

        return str(value)
