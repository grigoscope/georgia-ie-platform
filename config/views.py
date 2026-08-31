from django.db import (
    OperationalError,
    connection,
)
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
)
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckAPIView(APIView):
    authentication_classes = []

    permission_classes = [
        AllowAny,
    ]

    throttle_classes = []

    @extend_schema(
        tags=['Service'],
        auth=[],
        responses={
            200: OpenApiResponse(
                description=('Сервис и база данных доступны.'),
            ),
            503: OpenApiResponse(
                description=('База данных недоступна.'),
            ),
        },
    )
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1;')

                cursor.fetchone()

        except OperationalError:
            return Response(
                {
                    'status': 'error',
                    'database': ('unavailable'),
                },
                status=(status.HTTP_503_SERVICE_UNAVAILABLE),
            )

        return Response(
            {
                'status': 'ok',
                'database': 'available',
            },
            status=status.HTTP_200_OK,
        )
