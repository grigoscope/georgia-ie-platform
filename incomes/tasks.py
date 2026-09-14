import os
import uuid
from datetime import timedelta
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font

from config.business_time import (
    to_business_datetime,
)
from incomes.models import IncomeEntry
from notifications.models import Notification


EXPORT_TTL_HOURS = 24


def _export_directory():
    directory = (
        Path(settings.MEDIA_ROOT)
        / 'exports'
    )
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    return directory


def _headers():
    return [
        'date',
        'description',
        'counterparty',
        'account',
        'document',
        'original_amount',
        'currency',
        'exchange_rate',
        'exchange_rate_unit',
        'exchange_rate_source',
        'amount_gel',
        'declaration_category',
        'vat_amount',
        'invoice',
        'comment',
    ]


def _income_row(income):
    received_at = (
        to_business_datetime(
            income.received_at
        )
    )

    return [
        received_at.date(),
        income.description,
        (
            income.counterparty.name
            if income.counterparty
            else ''
        ),
        income.financial_account.name,
        income.document_number,
        income.original_amount,
        income.original_currency.code,
        income.exchange_rate_value,
        income.exchange_rate_unit,
        income.exchange_rate_source,
        income.amount_gel,
        income.declaration_category,
        income.vat_amount,
        (
            income.invoice.number
            if income.invoice
            else ''
        ),
        income.comment,
    ]


def _build_workbook(queryset):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Incomes'
    worksheet.freeze_panes = 'A2'

    worksheet.append(
        _headers()
    )

    for cell in worksheet[1]:
        cell.font = Font(
            bold=True,
        )

    for income in queryset:
        worksheet.append(
            _income_row(
                income
            )
        )

    for cell in worksheet['A'][1:]:
        cell.number_format = (
            'yyyy-mm-dd'
        )

    money_columns = [
        'F',
        'H',
        'K',
        'M',
    ]

    for column in money_columns:
        for cell in (
            worksheet[column][1:]
        ):
            cell.number_format = (
                '#,##0.00########'
            )

    column_widths = {
        'A': 14,
        'B': 35,
        'C': 28,
        'D': 24,
        'E': 18,
        'F': 20,
        'G': 12,
        'H': 20,
        'I': 18,
        'J': 22,
        'K': 18,
        'L': 24,
        'M': 16,
        'N': 18,
        'O': 35,
    }

    for (
        column,
        width,
    ) in column_widths.items():
        worksheet.column_dimensions[
            column
        ].width = width

    return workbook


@shared_task(
    name='incomes.generate_xlsx_export',
)
def generate_xlsx_export(
    user_id,
):
    user = (
        get_user_model()
        .objects
        .get(pk=user_id)
    )

    queryset = (
        IncomeEntry.objects
        .filter(
            user=user,
            is_deleted=False,
        )
        .select_related(
            'counterparty',
            'financial_account',
            'original_currency',
            'invoice',
        )
        .order_by('-received_at')
    )

    filename = (
        f'incomes-'
        f'{user_id}-'
        f'{uuid.uuid4().hex}.xlsx'
    )

    path = (
        _export_directory()
        / filename
    )

    workbook = (
        _build_workbook(
            queryset
        )
    )

    workbook.save(path)

    media_url = (
        settings.MEDIA_URL
        if settings.MEDIA_URL.endswith('/')
        else f'{settings.MEDIA_URL}/'
    )

    action_url = (
        f'{media_url}'
        f'exports/'
        f'{filename}'
    )

    Notification.objects.create(
        user=user,
        type='export_ready',
        title='Экспорт готов',
        message=(
            'XLSX-файл с журналом '
            'доходов готов к скачиванию.'
        ),
        action_url=action_url,
        delivery_status='pending',
        deduplication_key=(
            f'export:'
            f'{user_id}:'
            f'{filename}'
        ),
    )

    return {
        'status': 'ready',
        'user_id': user_id,
        'filename': filename,
        'action_url': action_url,
    }


@shared_task(
    name='incomes.cleanup_expired_exports',
)
def cleanup_expired_exports():
    directory = (
        _export_directory()
    )

    cutoff = (
        timezone.now()
        - timedelta(
            hours=EXPORT_TTL_HOURS,
        )
    )

    deleted = 0

    for path in (
        directory.glob('*.xlsx')
    ):
        modified_at = (
            timezone.datetime
            .fromtimestamp(
                path.stat().st_mtime,
                tz=timezone.get_current_timezone(),
            )
        )

        if modified_at < cutoff:
            path.unlink(
                missing_ok=True,
            )
            deleted += 1

    return {
        'deleted': deleted,
    }
