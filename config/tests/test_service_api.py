import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)


class ServiceAPITests(APITestCase):
    def test_health_is_public(
        self,
    ):
        response = self.client.get(reverse('health'))

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.json(),
            {
                'status': 'ok',
                'database': 'available',
            },
        )

    def test_schema_is_available(
        self,
    ):
        response = self.client.get(
            reverse('schema'),
            HTTP_ACCEPT=('application/json'),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        schema = json.loads(response.content)

        self.assertIn(
            'openapi',
            schema,
        )

        self.assertIn(
            'paths',
            schema,
        )

        self.assertIn(
            'components',
            schema,
        )

    def test_schema_contains_core_paths(
        self,
    ):
        response = self.client.get(
            reverse('schema'),
            HTTP_ACCEPT=('application/json'),
        )

        schema = json.loads(response.content)

        paths = schema['paths']

        required_paths = [
            '/api/v1/auth/login/',
            '/api/v1/profile/',
            '/api/v1/accounts/',
            '/api/v1/incomes/',
            '/api/v1/invoices/',
            '/api/v1/notifications/',
            '/api/v1/audit/',
            '/api/v1/files/',
            '/api/v1/health/',
        ]

        for path in required_paths:
            self.assertIn(
                path,
                paths,
            )

    def test_schema_has_jwt_security(
        self,
    ):
        response = self.client.get(
            reverse('schema'),
            HTTP_ACCEPT=('application/json'),
        )

        schema = json.loads(response.content)

        security_schemes = schema['components'].get(
            'securitySchemes',
            {},
        )

        self.assertIn(
            'BearerAuth',
            security_schemes,
        )

        bearer = security_schemes['BearerAuth']

        self.assertEqual(
            bearer['type'],
            'http',
        )

        self.assertEqual(
            bearer['scheme'],
            'bearer',
        )

        self.assertEqual(
            bearer['bearerFormat'],
            'JWT',
        )

    def test_protected_endpoint_uses_jwt(
        self,
    ):
        response = self.client.get(
            reverse('schema'),
            HTTP_ACCEPT=('application/json'),
        )

        schema = json.loads(response.content)

        operation = schema['paths']['/api/v1/profile/']['get']

        security = operation.get(
            'security',
            [],
        )

        self.assertTrue(any('BearerAuth' in item for item in security))

    def test_swagger_is_available(
        self,
    ):
        response = self.client.get(reverse('swagger-ui'))

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            'text/html',
            response['Content-Type'],
        )

    def test_redoc_is_available(
        self,
    ):
        response = self.client.get(reverse('redoc'))

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
