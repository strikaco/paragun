# Generated by Django 2.1.4 on 2019-01-17 20:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0020_auto_20190117_0137'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='application',
            field=models.CharField(blank=True, default='', help_text="Name of the application (i.e. 'Jenkins') whose logs will be remitted under this token.", max_length=80),
        ),
        migrations.AlterField(
            model_name='pulse',
            name='tags',
            field=models.CharField(blank=True, help_text='Comma-separated list of any custom tags related to this object.', max_length=160, null=True),
        ),
        migrations.AlterField(
            model_name='token',
            name='tags',
            field=models.CharField(blank=True, help_text='Comma-separated list of any custom tags related to this object.', max_length=160, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='tags',
            field=models.CharField(blank=True, help_text='Comma-separated list of any custom tags related to this object.', max_length=160, null=True),
        ),
    ]
