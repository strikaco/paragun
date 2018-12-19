# Generated by Django 2.1.4 on 2018-12-19 18:53

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0007_auto_20181210_1735'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pulse',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, help_text='Date and time of object creation.')),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, help_text='Date and time of last object modification.')),
                ('enabled', models.BooleanField(default=True, help_text='Whether or not this object should be enabled.')),
                ('app', models.CharField(max_length=8)),
                ('count', models.PositiveIntegerField()),
                ('bytes', models.PositiveIntegerField()),
                ('token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.Token')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
