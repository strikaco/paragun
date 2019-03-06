# Generated by Django 2.1.4 on 2019-03-05 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0015_remove_parser_benchmark'),
    ]

    operations = [
        migrations.AddField(
            model_name='field',
            name='type',
            field=models.PositiveIntegerField(choices=[(0, 'String'), (1, 'Boolean'), (10, 'Integer'), (11, 'Float'), (50, 'IP Address'), (60, 'List/Array'), (61, 'Dict/Hash')], default=0),
        ),
    ]
