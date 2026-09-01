import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import (
    APITestCase,
)

REQUIRED_QUERY_PARAMETERS = {
    '/api/v1/accounts/': {
        'type',
        'currency',
        'is_active',
        'use_in_invoices',
    },
    '/api/v1/counterparties/': {
        'type',
        'country',
        'search',
        'ordering',
    },
    '/api/v1/exchange-rates/': {
        'currency',
        'date',
    },
    '/api/v1/incomes/': {
        'date_from',
        'date_to',
        'year',
        'month',
        'account',
        'counterparty',
        'currency',
        'declaration_category',
        'invoice',
        'search',
        'ordering',
    },
    '/api/v1/invoices/': {
        'status',
        'date_from',
        'date_to',
        'counterparty',
        'currency',
        'overdue',
        'search',
        'ordering',
    },
    '/api/v1/tax-periods/': {
        'year',
        'month',
        'declaration_status',
        'status',
        'payment_status',
        'is_overdue',
    },
    '/api/v1/notifications/': {
        'type',
        'is_read',
        'delivery_status',
        'search',
        'ordering',
    },
    '/api/v1/audit/': {
        'action',
        'object_type',
        'object_id',
        'request_id',
        'date_from',
        'date_to',
        'search',
        'ordering',
    },
    '/api/v1/reports/monthly/': {
        'year',
        'month',
    },
    '/api/v1/reports/yearly/': {
        'year',
    },
    '/api/v1/reports/accounts/': {
        'year',
        'month',
    },
    '/api/v1/reports/currencies/': {
        'year',
        'month',
    },
    ('/api/v1/reports/declaration-categories/'): {
        'year',
        'month',
    },
    '/api/v1/incomes/export.csv': {
        'year',
        'month',
    },
    '/api/v1/incomes/export.xlsx': {
        'year',
        'month',
    },
}


PAGINATED_PATHS = [
    '/api/v1/counterparties/',
    '/api/v1/incomes/',
    '/api/v1/invoices/',
    '/api/v1/notifications/',
    '/api/v1/audit/',
]


class OpenAPIParameterTests(APITestCase):
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

    @staticmethod
    def _query_parameters(
        operation,
    ):
        return {
            parameter['name']
            for parameter in operation.get(
                'parameters',
                [],
            )
            if parameter.get('in') == 'query'
        }

    def test_required_filters_are_documented(
        self,
    ):
        schema = self._schema()

        for (
            path,
            required_parameters,
        ) in REQUIRED_QUERY_PARAMETERS.items():
            with self.subTest(path=path):
                self.assertIn(
                    path,
                    schema['paths'],
                )

                operation = schema['paths'][path]['get']

                actual_parameters = self._query_parameters(operation)

                self.assertTrue(
                    required_parameters <= actual_parameters,
                    msg=(f'{path}: отсутствуют {required_parameters - actual_parameters}'),
                )

    def test_required_lists_are_paginated(
        self,
    ):
        schema = self._schema()

        for path in PAGINATED_PATHS:
            with self.subTest(path=path):
                operation = schema['paths'][path]['get']

                parameters = self._query_parameters(operation)

                self.assertIn(
                    'page',
                    parameters,
                )

                self.assertIn(
                    'page_size',
                    parameters,
                )

    def test_exchange_rate_currency_is_required(
        self,
    ):
        schema = self._schema()

        operation = schema['paths']['/api/v1/exchange-rates/']['get']

        parameters = {
            item['name']: item
            for item in operation.get(
                'parameters',
                [],
            )
        }

        self.assertTrue(
            parameters['currency'].get(
                'required',
                False,
            )
        )
