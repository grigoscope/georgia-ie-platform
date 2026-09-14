from django.test import TestCase
from django.conf import settings

from config.celery import app
from notifications.tasks import (
    celery_healthcheck,
)


class CeleryConfigurationTests(
    TestCase,
):
    def test_celery_uses_django_settings(
        self,
    ):
        self.assertEqual(
            app.conf.broker_url,
            settings.CELERY_BROKER_URL,
        )

    def test_healthcheck_task_is_registered(
        self,
    ):
        self.assertEqual(
            celery_healthcheck.name,
            'notifications.celery_healthcheck',
        )

    def test_healthcheck_task_runs_in_eager_mode(
        self,
    ):
        with self.settings(
            CELERY_TASK_ALWAYS_EAGER=True,
            CELERY_TASK_EAGER_PROPAGATES=True,
        ):
            result = (
                celery_healthcheck
                .apply()
                .get()
            )

        self.assertEqual(
            result['status'],
            'ok',
        )

        self.assertIn(
            'checked_at',
            result,
        )
