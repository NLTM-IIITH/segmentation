# Generated by Django 4.1.6 on 2023-08-01 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0008_page_qc_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='qc_timestamp',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
