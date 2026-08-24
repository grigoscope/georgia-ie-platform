from django.db import migrations, models


def created_to_draft(apps, schema_editor):
    Invoice = apps.get_model(
        'invoices',
        'Invoice',
    )

    Invoice.objects.filter(status='created').update(status='draft')


def draft_to_created(apps, schema_editor):
    Invoice = apps.get_model(
        'invoices',
        'Invoice',
    )

    Invoice.objects.filter(status='draft').update(status='created')


class Migration(migrations.Migration):
    dependencies = [
        (
            'invoices',
            '0002_alter_invoice_status_alter_invoicepayment_amount_and_more',
        ),
    ]

    operations = [
        migrations.RunPython(
            created_to_draft,
            draft_to_created,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='status',
            field=models.CharField(
                verbose_name='Статус',
                max_length=30,
                choices=[
                    (
                        'draft',
                        'Черновик',
                    ),
                    (
                        'pending',
                        'Ожидает оплаты',
                    ),
                    (
                        'partially_paid',
                        'Частично оплачен',
                    ),
                    (
                        'paid',
                        'Оплачен',
                    ),
                    (
                        'cancelled',
                        'Отменён',
                    ),
                ],
                default='draft',
            ),
        ),
    ]
