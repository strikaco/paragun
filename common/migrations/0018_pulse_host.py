# Generated by Django 2.1.4 on 2019-01-16 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0017_auto_20190102_1802'),
    ]

    operations = [
        migrations.AddField(
            model_name='pulse',
            name='host',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
