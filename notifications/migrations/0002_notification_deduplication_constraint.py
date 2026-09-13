from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        (
            'notifications',
            '0001_initial',
        ),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='notification',
            constraint=models.UniqueConstraint(
                fields=(
                    'deduplication_key',
                ),
                condition=~Q(
                    deduplication_key='',
                ),
                name='unique_notification_deduplication_key',
            ),
        ),
    ]
