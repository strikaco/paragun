# Generated by Django 2.1.4 on 2019-03-04 20:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0013_field_validator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='field',
            name='key',
            field=models.CharField(max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name='field',
            name='validator',
            field=models.TextField(default='(.*)', help_text="Regex string to apply against parsed value to detect match. Use '(.*)' to match any."),
        ),
    ]
