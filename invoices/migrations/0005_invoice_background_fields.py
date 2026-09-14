from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            'invoices',
            '0004_invoicesharelink',
        ),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='is_overdue',
            field=models.BooleanField(
                default=False,
                verbose_name='Просрочен',
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='telegram_message_id',
            field=models.BigIntegerField(
                blank=True,
                null=True,
                verbose_name='Telegram message ID',
            ),
        ),
        migrations.AddField(
            model_name='invoice',
            name='telegram_sent_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Дата отправки PDF в Telegram',
            ),
        ),
    ]
