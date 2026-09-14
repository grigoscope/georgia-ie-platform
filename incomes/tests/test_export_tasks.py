import os
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import (
    get_user_model,
)
from django.test import (
    TestCase,
    override_settings,
)
from django.utils import timezone
from openpyxl import load_workbook

from incomes.tasks import (
    cleanup_expired_exports,
    generate_xlsx_export,
)
from notifications.models import (
    Notification,
)


class IncomeExportTaskTests(
    TestCase,
):
    def setUp(self):
        self.user = (
            get_user_model()
            .objects
            .create_user(
                email='export@example.com',
                password='Password123!',
            )
        )

        self.temp_directory = (
            TemporaryDirectory()
        )

        self.addCleanup(
            self.temp_directory.cleanup
        )

        self.override = (
            override_settings(
                MEDIA_ROOT=(
                    self.temp_directory.name
                ),
                MEDIA_URL='/media/',
            )
        )

        self.override.enable()

        self.addCleanup(
            self.override.disable
        )

    def test_generate_xlsx_export(
        self,
    ):
        result = (
            generate_xlsx_export(
                self.user.pk,
            )
        )

        self.assertEqual(
            result['status'],
            'ready',
        )

        path = (
            Path(
                self.temp_directory.name
            )
            / 'exports'
            / result['filename']
        )

        self.assertTrue(
            path.exists()
        )

        workbook = (
            load_workbook(path)
        )

        worksheet = (
            workbook['Incomes']
        )

        self.assertEqual(
            worksheet['A1'].value,
            'date',
        )

        notification = (
            Notification.objects.get(
                user=self.user,
                type='export_ready',
            )
        )

        self.assertEqual(
            notification.action_url,
            result['action_url'],
        )

    def test_cleanup_expired_exports(
        self,
    ):
        directory = (
            Path(
                self.temp_directory.name
            )
            / 'exports'
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        old_file = (
            directory
            / 'old.xlsx'
        )

        old_file.write_bytes(
            b'test'
        )

        old_time = (
            timezone.now()
            - timedelta(hours=25)
        ).timestamp()

        os.utime(
            old_file,
            (
                old_time,
                old_time,
            ),
        )

        fresh_file = (
            directory
            / 'fresh.xlsx'
        )

        fresh_file.write_bytes(
            b'test'
        )

        result = (
            cleanup_expired_exports()
        )

        self.assertEqual(
            result['deleted'],
            1,
        )

        self.assertFalse(
            old_file.exists()
        )

        self.assertTrue(
            fresh_file.exists()
        )
