# Generated by Django 2.1.4 on 2019-02-27 21:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='field',
            options={'ordering': ('key',)},
        ),
        migrations.AlterField(
            model_name='field',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
