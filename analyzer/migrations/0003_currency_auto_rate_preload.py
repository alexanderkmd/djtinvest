# Generated by Django 5.1 on 2024-09-08 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0002_split'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='auto_rate_preload',
            field=models.BooleanField(default=False, verbose_name='Подгружать курс'),
        ),
    ]
