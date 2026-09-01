import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

REQUIRED_OPERATIONS = {
    '/api/v1/auth/register/': {
        'post',
    },
    '/api/v1/auth/login/': {
        'post',
    },
    '/api/v1/auth/token/refresh/': {
        'post',
    },
    '/api/v1/auth/logout/': {
        'post',
    },
    '/api/v1/auth/me/': {
        'get',
    },
    '/api/v1/auth/password/reset/': {
        'post',
    },
    '/api/v1/auth/password/reset/confirm/': {
        'post',
    },
    '/api/v1/profile/': {
        'get',
        'patch',
    },
    '/api/v1/profile/signature/': {
        'post',
        'delete',
    },
    '/api/v1/profile/logo/': {
        'post',
        'delete',
    },
    '/api/v1/telegram/link/': {
        'post',
        'delete',
    },
    '/api/v1/telegram/mini-app/auth/': {
        'post',
    },
    '/api/v1/telegram/webhook/': {
        'post',
    },
    '/api/v1/accounts/': {
        'get',
        'post',
    },
    '/api/v1/accounts/{id}/': {
        'get',
        'patch',
        'delete',
    },
    '/api/v1/accounts/{id}/set-default/': {
        'post',
    },
    '/api/v1/accounts/{id}/archive/': {
        'post',
    },
    '/api/v1/counterparties/': {
        'get',
        'post',
    },
    '/api/v1/counterparties/{id}/': {
        'get',
        'patch',
        'delete',
    },
    '/api/v1/currencies/': {
        'get',
    },
    '/api/v1/exchange-rates/': {
        'get',
    },
    '/api/v1/exchange-rates/convert/': {
        'post',
    },
    '/api/v1/exchange-rates/crypto-estimate/': {
        'post',
    },
    '/api/v1/incomes/': {
        'get',
        'post',
    },
    '/api/v1/incomes/{id}/': {
        'get',
        'patch',
        'delete',
    },
    '/api/v1/incomes/{id}/restore/': {
        'post',
    },
    '/api/v1/incomes/preview/': {
        'post',
    },
    '/api/v1/incomes/export.csv': {
        'get',
    },
    '/api/v1/incomes/export.xlsx': {
        'get',
    },
    '/api/v1/reports/dashboard/': {
        'get',
    },
    '/api/v1/reports/monthly/': {
        'get',
    },
    '/api/v1/reports/yearly/': {
        'get',
    },
    '/api/v1/reports/accounts/': {
        'get',
    },
    '/api/v1/reports/currencies/': {
        'get',
    },
    ('/api/v1/reports/declaration-categories/'): {
        'get',
    },
    '/api/v1/tax-periods/': {
        'get',
    },
    '/api/v1/tax-periods/{id}/': {
        'get',
    },
    '/api/v1/tax-periods/generate/': {
        'post',
    },
    '/api/v1/tax-periods/{id}/recalculate/': {
        'post',
    },
    ('/api/v1/tax-periods/{id}/preview-tax-rate/'): {
        'post',
    },
    ('/api/v1/tax-periods/{id}/mark-submitted/'): {
        'post',
    },
    ('/api/v1/tax-periods/{id}/unmark-submitted/'): {
        'post',
    },
    ('/api/v1/tax-periods/{id}/mark-paid/'): {
        'post',
    },
    ('/api/v1/tax-periods/{id}/unmark-paid/'): {
        'post',
    },
    ('/api/v1/tax-periods/{id}/declaration-values/'): {
        'get',
    },
    '/api/v1/invoices/': {
        'get',
        'post',
    },
    '/api/v1/invoices/{id}/': {
        'get',
        'patch',
        'delete',
    },
    '/api/v1/invoices/{id}/preview/': {
        'post',
    },
    ('/api/v1/invoices/{id}/generate-pdf/'): {
        'post',
    },
    '/api/v1/invoices/{id}/pdf/': {
        'get',
    },
    ('/api/v1/invoices/{id}/send-to-telegram/'): {
        'post',
    },
    ('/api/v1/invoices/{id}/send-email/'): {
        'post',
    },
    ('/api/v1/invoices/{id}/create-share-link/'): {
        'post',
    },
    ('/api/v1/invoices/{id}/share-link/'): {
        'delete',
    },
    ('/api/v1/invoices/{id}/mark-sent/'): {
        'post',
    },
    ('/api/v1/invoices/{id}/mark-paid/'): {
        'post',
    },
    ('/api/v1/invoices/{id}/mark-partially-paid/'): {
        'post',
    },
    '/api/v1/invoices/{id}/cancel/': {
        'post',
    },
    ('/api/v1/invoices/{id}/create-income/'): {
        'post',
    },
    ('/api/v1/invoices/{id}/duplicate/'): {
        'post',
    },
    '/api/v1/notifications/': {
        'get',
    },
    '/api/v1/notifications/{id}/': {
        'get',
    },
    ('/api/v1/notifications/{id}/mark-read/'): {
        'post',
    },
    ('/api/v1/notifications/mark-all-read/'): {
        'post',
    },
    '/api/v1/notification-settings/': {
        'get',
        'patch',
    },
    '/api/v1/files/': {
        'post',
    },
    ('/api/v1/files/{id}/download-link/'): {
        'post',
    },
    '/api/v1/files/{id}/': {
        'delete',
    },
    '/api/v1/audit/': {
        'get',
    },
    '/api/v1/health/': {
        'get',
    },
}


class Stage4AcceptanceTests(APITestCase):
    def _schema(self):
        response = self.client.get(
            reverse('schema'),
            HTTP_ACCEPT=('application/json'),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        return json.loads(response.content)

    def _normalized_paths(self):
        schema = self._schema()

        result = {}

        for (
            path,
            operations,
        ) in schema['paths'].items():
            normalized = path.replace(
                '{pk}',
                '{id}',
            )

            result[normalized] = operations

        return result

    def test_all_required_operations_are_in_openapi(
        self,
    ):
        paths = self._normalized_paths()

        for (
            path,
            methods,
        ) in REQUIRED_OPERATIONS.items():
            with self.subTest(path=path):
                self.assertIn(
                    path,
                    paths,
                )

                available_methods = {
                    key
                    for key in paths[path].keys()
                    if key
                    in {
                        'get',
                        'post',
                        'put',
                        'patch',
                        'delete',
                    }
                }

                for method in methods:
                    self.assertIn(
                        method,
                        available_methods,
                    )

    def test_schema_contains_only_v1_api(
        self,
    ):
        schema = self._schema()

        for path in schema['paths']:
            self.assertTrue(
                path.startswith('/api/v1/'),
                msg=(f'Legacy endpoint попал в OpenAPI: {path}'),
            )

    def test_service_endpoints_match_contract(
        self,
    ):
        self.assertEqual(
            reverse('health'),
            '/api/v1/health/',
        )

        self.assertEqual(
            reverse('schema'),
            '/api/v1/schema/',
        )

        self.assertEqual(
            reverse('swagger-ui'),
            '/api/v1/docs/',
        )

    def test_jwt_scheme_is_present(
        self,
    ):
        schema = self._schema()

        schemes = schema['components'].get(
            'securitySchemes',
            {},
        )

        self.assertIn(
            'BearerAuth',
            schemes,
        )

        self.assertEqual(
            schemes['BearerAuth']['scheme'],
            'bearer',
        )

    def test_core_resources_require_authentication(
        self,
    ):
        requests = [
            (
                'get',
                '/api/v1/profile/',
            ),
            (
                'get',
                '/api/v1/accounts/',
            ),
            (
                'get',
                '/api/v1/counterparties/',
            ),
            (
                'get',
                '/api/v1/currencies/',
            ),
            (
                'get',
                '/api/v1/incomes/',
            ),
            (
                'get',
                ('/api/v1/reports/dashboard/'),
            ),
            (
                'get',
                '/api/v1/tax-periods/',
            ),
            (
                'get',
                '/api/v1/invoices/',
            ),
            (
                'get',
                '/api/v1/notifications/',
            ),
            (
                'get',
                ('/api/v1/notification-settings/'),
            ),
            (
                'get',
                '/api/v1/audit/',
            ),
            (
                'post',
                '/api/v1/files/',
            ),
            (
                'post',
                ('/api/v1/telegram/link/'),
            ),
        ]

        for (
            method,
            path,
        ) in requests:
            with self.subTest(
                method=method,
                path=path,
            ):
                response = getattr(
                    self.client,
                    method,
                )(
                    path,
                    {},
                    format='json',
                )

                self.assertEqual(
                    response.status_code,
                    (status.HTTP_401_UNAUTHORIZED),
                )
