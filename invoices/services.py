from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import EntrepreneurProfile
from invoices.models import Invoice, InvoiceItem


class InvoiceService:
    """Бизнес-логика инвойсов."""

    MONEY_QUANT = Decimal('0.01')
    QUANTITY_QUANT = Decimal('0.001')

    UNSET = object()

    @transaction.atomic
    def create_invoice(
        self,
        *,
        user,
        issue_date,
        currency,
        counterparty,
        financial_account,
        items,
        language='en',
        service_period_start=None,
        service_period_end=None,
        due_date=None,
        discount=Decimal('0.00'),
        extra_charge=Decimal('0.00'),
        tax_note='',
        tax_reference_amount=None,
        payment_purpose='',
        notes='',
    ):
        """Создать черновик инвойса."""

        self._validate_owners(
            user=user,
            counterparty=counterparty,
            financial_account=financial_account,
        )

        self._validate_currency(
            currency=currency,
        )

        self._validate_dates(
            issue_date=issue_date,
            due_date=due_date,
            service_period_start=service_period_start,
            service_period_end=service_period_end,
        )

        if not items:
            raise ValidationError('Инвойс должен содержать хотя бы одну позицию.')

        discount = self._money(discount)

        extra_charge = self._money(extra_charge)

        self._validate_adjustments(
            discount=discount,
            extra_charge=extra_charge,
        )

        prepared_items = self._prepare_items(items)

        subtotal = self._subtotal(prepared_items)

        total = self._calculate_total(
            subtotal=subtotal,
            discount=discount,
            extra_charge=extra_charge,
        )

        number = self._next_invoice_number(user=user)

        invoice = Invoice(
            user=user,
            number=number,
            issue_date=issue_date,
            service_period_start=(service_period_start),
            service_period_end=(service_period_end),
            due_date=due_date,
            currency=currency,
            language=language,
            status='draft',
            counterparty=counterparty,
            seller_snapshot=(self._seller_snapshot(user=user)),
            buyer_snapshot=(self._buyer_snapshot(counterparty=counterparty)),
            payment_details_snapshot=(
                self._payment_details_snapshot(financial_account=(financial_account))
            ),
            subtotal=subtotal,
            discount_amount=discount,
            extra_charge_amount=(extra_charge),
            total_amount=total,
            tax_note=tax_note,
            tax_reference_amount=(tax_reference_amount),
            payment_purpose=(payment_purpose),
            notes=notes,
        )

        invoice.full_clean()
        invoice.save()

        self._save_items(
            invoice=invoice,
            prepared_items=prepared_items,
        )

        return invoice

    @transaction.atomic
    def update_invoice(
        self,
        *,
        invoice,
        issue_date=UNSET,
        currency=UNSET,
        counterparty=UNSET,
        financial_account=UNSET,
        items=UNSET,
        language=UNSET,
        service_period_start=UNSET,
        service_period_end=UNSET,
        due_date=UNSET,
        discount=UNSET,
        extra_charge=UNSET,
        tax_note=UNSET,
        tax_reference_amount=UNSET,
        payment_purpose=UNSET,
        notes=UNSET,
    ):
        """Изменить черновик инвойса."""

        invoice = (
            Invoice.objects.select_for_update()
            .select_related(
                'user',
                'counterparty',
                'currency',
            )
            .get(pk=invoice.pk)
        )

        if invoice.status != 'draft':
            raise ValidationError('Редактировать можно только инвойс в статусе draft.')

        user = invoice.user

        if counterparty is not self.UNSET:
            if counterparty.user_id != user.id:
                raise ValidationError('Контрагент принадлежит другому пользователю.')

        if financial_account is not self.UNSET:
            if financial_account.user_id != user.id:
                raise ValidationError('Финансовый счёт принадлежит другому пользователю.')

        if currency is not self.UNSET:
            self._validate_currency(currency=currency)

        new_issue_date = invoice.issue_date if issue_date is self.UNSET else issue_date

        new_due_date = invoice.due_date if due_date is self.UNSET else due_date

        new_service_start = (
            invoice.service_period_start
            if service_period_start is self.UNSET
            else service_period_start
        )

        new_service_end = (
            invoice.service_period_end if service_period_end is self.UNSET else service_period_end
        )

        self._validate_dates(
            issue_date=new_issue_date,
            due_date=new_due_date,
            service_period_start=(new_service_start),
            service_period_end=(new_service_end),
        )

        if items is self.UNSET:
            prepared_items = None

            subtotal = self._money(
                sum(
                    (item.line_total for item in invoice.invoice_items.all()),
                    Decimal('0.00'),
                )
            )

        else:
            if not items:
                raise ValidationError('Инвойс должен содержать хотя бы одну позицию.')

            prepared_items = self._prepare_items(items)

            subtotal = self._subtotal(prepared_items)

        new_discount = invoice.discount_amount if discount is self.UNSET else self._money(discount)

        new_extra_charge = (
            invoice.extra_charge_amount if extra_charge is self.UNSET else self._money(extra_charge)
        )

        self._validate_adjustments(
            discount=new_discount,
            extra_charge=new_extra_charge,
        )

        total = self._calculate_total(
            subtotal=subtotal,
            discount=new_discount,
            extra_charge=new_extra_charge,
        )

        if issue_date is not self.UNSET:
            invoice.issue_date = issue_date

        if currency is not self.UNSET:
            invoice.currency = currency

        if language is not self.UNSET:
            invoice.language = language

        if counterparty is not self.UNSET:
            invoice.counterparty = counterparty

            invoice.buyer_snapshot = self._buyer_snapshot(counterparty=counterparty)

        if financial_account is not self.UNSET:
            invoice.payment_details_snapshot = self._payment_details_snapshot(
                financial_account=(financial_account)
            )

        if service_period_start is not self.UNSET:
            invoice.service_period_start = service_period_start

        if service_period_end is not self.UNSET:
            invoice.service_period_end = service_period_end

        if due_date is not self.UNSET:
            invoice.due_date = due_date

        if tax_note is not self.UNSET:
            invoice.tax_note = tax_note

        if tax_reference_amount is not self.UNSET:
            invoice.tax_reference_amount = tax_reference_amount

        if payment_purpose is not self.UNSET:
            invoice.payment_purpose = payment_purpose

        if notes is not self.UNSET:
            invoice.notes = notes

        invoice.seller_snapshot = self._seller_snapshot(user=user)

        invoice.subtotal = subtotal
        invoice.discount_amount = new_discount
        invoice.extra_charge_amount = new_extra_charge
        invoice.total_amount = total

        invoice.full_clean()
        invoice.save()

        if prepared_items is not None:
            invoice.invoice_items.all().delete()

            self._save_items(
                invoice=invoice,
                prepared_items=(prepared_items),
            )

        return invoice

    def _prepare_items(
        self,
        items,
    ):
        """Рассчитать позиции."""

        prepared = []

        for item in items:
            description = str(
                item.get(
                    'description',
                    '',
                )
            ).strip()

            if not description:
                raise ValidationError('У позиции должно быть описание.')

            try:
                quantity = Decimal(
                    str(
                        item.get(
                            'quantity',
                            '1',
                        )
                    )
                )

                unit_price = Decimal(
                    str(
                        item.get(
                            'unit_price',
                            '0',
                        )
                    )
                )

            except Exception as error:
                raise ValidationError('Некорректное количество или цена позиции.') from error

            if quantity <= 0:
                raise ValidationError('Количество должно быть больше нуля.')

            if unit_price < 0:
                raise ValidationError('Цена не может быть отрицательной.')

            quantity = quantity.quantize(
                self.QUANTITY_QUANT,
                rounding=ROUND_HALF_UP,
            )

            unit_price = self._money(unit_price)

            line_total = self._money(quantity * unit_price)

            prepared.append(
                {
                    'description': (description),
                    'quantity': quantity,
                    'unit': item.get(
                        'unit',
                        'service',
                    ),
                    'unit_price': (unit_price),
                    'line_total': (line_total),
                }
            )

        return prepared

    def _save_items(
        self,
        *,
        invoice,
        prepared_items,
    ):
        for position, item in enumerate(
            prepared_items,
            start=1,
        ):
            invoice_item = InvoiceItem(
                invoice=invoice,
                position=position,
                description=(item['description']),
                quantity=(item['quantity']),
                unit=item['unit'],
                unit_price=(item['unit_price']),
                line_total=(item['line_total']),
            )

            invoice_item.full_clean()
            invoice_item.save()

    def _subtotal(
        self,
        prepared_items,
    ):
        return self._money(
            sum(
                (item['line_total'] for item in prepared_items),
                Decimal('0.00'),
            )
        )

    def _calculate_total(
        self,
        *,
        subtotal,
        discount,
        extra_charge,
    ):
        total = self._money(subtotal - discount + extra_charge)

        if total < 0:
            raise ValidationError('Итоговая сумма инвойса не может быть отрицательной.')

        return total

    @staticmethod
    def _validate_adjustments(
        *,
        discount,
        extra_charge,
    ):
        if discount < 0:
            raise ValidationError('Скидка не может быть отрицательной.')

        if extra_charge < 0:
            raise ValidationError('Доплата не может быть отрицательной.')

    @staticmethod
    def _validate_dates(
        *,
        issue_date,
        due_date,
        service_period_start,
        service_period_end,
    ):
        if due_date is not None and due_date < issue_date:
            raise ValidationError('Срок оплаты не может быть раньше даты инвойса.')

        if (
            service_period_start is not None
            and service_period_end is not None
            and service_period_end < service_period_start
        ):
            raise ValidationError('Конец периода услуги не может быть раньше начала.')

    @staticmethod
    def _validate_currency(
        *,
        currency,
    ):
        if not currency.is_active:
            raise ValidationError('Нельзя использовать неактивную валюту.')

    @transaction.atomic
    def _next_invoice_number(
        self,
        *,
        user,
    ):
        profile = EntrepreneurProfile.objects.select_for_update().get(user=user)

        number = profile.next_invoice_number

        profile.next_invoice_number += 1

        profile.save(
            update_fields=[
                'next_invoice_number',
                'updated_at',
            ]
        )

        return f'{profile.invoice_prefix}{number}'

    @staticmethod
    def _seller_snapshot(
        *,
        user,
    ):
        profile = user.entrepreneur_profile

        return {
            'business_name': (profile.business_name),
            'entrepreneur_status': (profile.entrepreneur_status),
            'tin': profile.tin,
            'legal_address': (profile.legal_address),
            'phone': profile.phone,
            'email': (profile.public_email or user.email),
        }

    @staticmethod
    def _buyer_snapshot(
        *,
        counterparty,
    ):
        return {
            'name': counterparty.name,
            'type': counterparty.type,
            'country': (counterparty.country),
            'tax_id': (counterparty.tax_id),
            'address': (counterparty.address),
            'email': (counterparty.email),
            'phone': (counterparty.phone),
        }

    @staticmethod
    def _payment_details_snapshot(
        *,
        financial_account,
    ):
        return {
            'account_id': (financial_account.id),
            'name': (financial_account.name),
            'type': (financial_account.type),
            'provider_name': (financial_account.provider_name),
            'account_holder': (financial_account.account_holder),
            'iban': (financial_account.iban),
            'swift_bic': (financial_account.swift_bic),
            'account_identifier': (financial_account.account_identifier),
            'crypto_asset': (financial_account.crypto_asset),
            'crypto_network': (financial_account.crypto_network),
            'wallet_address': (financial_account.wallet_address),
            'memo_tag': (financial_account.memo_tag),
            'payment_instructions': (financial_account.payment_instructions),
            'currency': (financial_account.default_currency.code),
        }

    @staticmethod
    def _validate_owners(
        *,
        user,
        counterparty,
        financial_account,
    ):
        if counterparty.user_id != user.id:
            raise ValidationError('Контрагент принадлежит другому пользователю.')

        if financial_account.user_id != user.id:
            raise ValidationError('Финансовый счёт принадлежит другому пользователю.')

    @classmethod
    def _money(
        cls,
        value,
    ):
        return Decimal(str(value)).quantize(
            cls.MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )
