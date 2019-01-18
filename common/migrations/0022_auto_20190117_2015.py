# Generated by Django 2.1.4 on 2019-01-17 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0021_auto_20190117_2006'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='application',
            field=models.CharField(blank=True, default='Unknown', help_text="Name of the application (i.e. 'Jenkins') whose logs will be remitted under this token.", max_length=80),
        ),
    ]