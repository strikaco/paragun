# Generated by Django 2.1.4 on 2019-01-17 23:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0022_auto_20190117_2015'),
    ]

    operations = [
        migrations.RenameField(
            model_name='token',
            old_name='backup_email',
            new_name='contact',
        ),
    ]
