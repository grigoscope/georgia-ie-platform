from notifications.models import Notification


class NotificationService:
    """Бизнес-логика внутренних уведомлений."""

    @staticmethod
    def notify_tax_period_changed(
        *,
        period,
    ):
        """
        Уведомить пользователя о том,
        что поданная декларация изменилась.
        """

        deduplication_key = f'tax-period-changed:{period.user_id}:{period.year}:{period.month}'

        notification, _ = Notification.objects.get_or_create(
            user=period.user,
            deduplication_key=(deduplication_key),
            defaults={
                'type': ('tax_period_changed'),
                'title': ('Изменились данные поданной декларации'),
                'message': (
                    f'После подачи декларации '
                    f'за {period.month:02d}.'
                    f'{period.year} данные '
                    f'доходов изменились. '
                    f'Проверьте декларацию.'
                ),
                'related_object_type': ('TaxPeriod'),
                'related_object_id': (period.id),
                'action_url': (f'/taxes/{period.year}/{period.month}/'),
                'delivery_status': ('pending'),
            },
        )

        return notification
