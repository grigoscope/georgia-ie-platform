from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import EntrepreneurProfile
from invoices.models import Invoice, InvoiceItem


class InvoiceService:
    """Бизнес-логика создания инвойсов."""

    MONEY_QUANT = Decimal('0.01')
    QUANTITY_QUANT = Decimal('0.001')

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

        if not items:
            raise ValidationError('Инвойс должен содержать хотя бы одну позицию.')

        discount = self._money(discount)
        extra_charge = self._money(extra_charge)

        if discount < 0:
            raise ValidationError('Скидка не может быть отрицательной.')

        if extra_charge < 0:
            raise ValidationError('Доплата не может быть отрицательной.')

        prepared_items = self._prepare_items(items)

        subtotal = self._money(
            sum(
                (item['line_total'] for item in prepared_items),
                Decimal('0.00'),
            )
        )

        total = self._money(subtotal - discount + extra_charge)

        if total < 0:
            raise ValidationError('Итоговая сумма инвойса не может быть отрицательной.')

        number = self._next_invoice_number(user=user)

        seller_snapshot = self._seller_snapshot(user=user)

        buyer_snapshot = self._buyer_snapshot(counterparty=counterparty)

        payment_details_snapshot = self._payment_details_snapshot(
            financial_account=financial_account
        )

        invoice = Invoice(
            user=user,
            number=number,
            issue_date=issue_date,
            service_period_start=service_period_start,
            service_period_end=service_period_end,
            due_date=due_date,
            currency=currency,
            language=language,
            status='created',
            counterparty=counterparty,
            seller_snapshot=seller_snapshot,
            buyer_snapshot=buyer_snapshot,
            payment_details_snapshot=payment_details_snapshot,
            subtotal=subtotal,
            discount_amount=discount,
            extra_charge_amount=extra_charge,
            total_amount=total,
            tax_note=tax_note,
            tax_reference_amount=tax_reference_amount,
            payment_purpose=payment_purpose,
            notes=notes,
        )

        invoice.full_clean()
        invoice.save()

        for position, item in enumerate(
            prepared_items,
            start=1,
        ):
            invoice_item = InvoiceItem(
                invoice=invoice,
                position=position,
                description=item['description'],
                quantity=item['quantity'],
                unit=item['unit'],
                unit_price=item['unit_price'],
                line_total=item['line_total'],
            )

            invoice_item.full_clean()
            invoice_item.save()

        return invoice

    def _prepare_items(self, items):
        """Рассчитать позиции инвойса."""

        prepared = []

        for item in items:
            description = str(item.get('description', '')).strip()

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
                    'description': description,
                    'quantity': quantity,
                    'unit': item.get(
                        'unit',
                        'service',
                    ),
                    'unit_price': unit_price,
                    'line_total': line_total,
                }
            )

        return prepared

    @transaction.atomic
    def _next_invoice_number(
        self,
        *,
        user,
    ):
        """Получить и зарезервировать номер инвойса."""

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
    def _seller_snapshot(*, user):
        """Замороженные данные продавца."""

        profile = user.entrepreneur_profile

        return {
            'business_name': profile.business_name,
            'entrepreneur_status': (profile.entrepreneur_status),
            'tin': profile.tin,
            'legal_address': profile.legal_address,
            'phone': profile.phone,
            'email': (profile.public_email or user.email),
        }

    @staticmethod
    def _buyer_snapshot(*, counterparty):
        """Замороженные данные покупателя."""

        return {
            'name': counterparty.name,
            'type': counterparty.type,
            'country': counterparty.country,
            'tax_id': counterparty.tax_id,
            'address': counterparty.address,
            'email': counterparty.email,
            'phone': counterparty.phone,
        }

    @staticmethod
    def _payment_details_snapshot(
        *,
        financial_account,
    ):
        """Замороженные платёжные реквизиты."""

        return {
            'account_id': financial_account.id,
            'name': financial_account.name,
            'type': financial_account.type,
            'provider_name': (financial_account.provider_name),
            'account_holder': (financial_account.account_holder),
            'iban': financial_account.iban,
            'swift_bic': financial_account.swift_bic,
            'account_identifier': (financial_account.account_identifier),
            'crypto_asset': (financial_account.crypto_asset),
            'crypto_network': (financial_account.crypto_network),
            'wallet_address': (financial_account.wallet_address),
            'memo_tag': financial_account.memo_tag,
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
        """Проверить владельцев объектов."""

        if counterparty.user_id != user.id:
            raise ValidationError('Контрагент принадлежит другому пользователю.')

        if financial_account.user_id != user.id:
            raise ValidationError('Финансовый счёт принадлежит другому пользователю.')

    @classmethod
    def _money(cls, value):
        return Decimal(str(value)).quantize(
            cls.MONEY_QUANT,
            rounding=ROUND_HALF_UP,
        )
