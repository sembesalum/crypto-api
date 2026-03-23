# Generated manually for last_successful_payment_at

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_successful_payment_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When a payment was last completed (webhook/verify).',
                null=True,
            ),
        ),
    ]
