from django.db import OperationalError, connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckAPIView(APIView):
    '''Проверка работоспособности БД'''
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1;')
                cursor.fetchone()
        except OperationalError:
            return Response(
                {
                    'status': 'error',
                    'database': 'unavailable',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                'status': 'ok',
                'database': 'available',
            }
        )