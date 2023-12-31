# Generated by Django 4.1.6 on 2023-02-21 10:58

from django.db import migrations, models
import page.models


class Migration(migrations.Migration):

    dependencies = [
        ('page', '0002_page_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='image',
            field=models.ImageField(blank=True, help_text='original page image', null=True, upload_to=page.models.get_image_path, verbose_name='Page Image'),
        ),
        migrations.AlterField(
            model_name='page',
            name='parent',
            field=models.CharField(default='', help_text='This field stores the ID or information of the source of the page', max_length=100),
        ),
    ]
