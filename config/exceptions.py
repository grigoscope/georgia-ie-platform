import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import (
    exception_handler as drf_exception_handler,
)

logger = logging.getLogger(__name__)


def api_exception_handler(
    exc,
    context,
):
    """
    DRF-ошибки обрабатывает стандартный
    handler.

    Неожиданные исключения в production
    превращаем в безопасный JSON 500.
    """

    response = drf_exception_handler(
        exc,
        context,
    )

    if response is not None:
        return response

    if settings.DEBUG:
        return None

    logger.error(
        'Unhandled API exception',
        exc_info=(
            type(exc),
            exc,
            exc.__traceback__,
        ),
    )

    return Response(
        {'detail': ('Внутренняя ошибка сервера.')},
        status=(status.HTTP_500_INTERNAL_SERVER_ERROR),
    )
