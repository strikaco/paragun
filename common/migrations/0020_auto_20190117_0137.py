# Generated by Django 2.1.4 on 2019-01-17 01:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0019_token_backup_email'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Host',
        ),
        migrations.RemoveField(
            model_name='token',
            name='hosts',
        ),
    ]
