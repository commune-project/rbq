# Generated by Django 2.2.5 on 2019-09-18 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rbq_backend', '0007_auto_20190918_0715'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='name',
            field=models.TextField(blank=True, default=''),
        ),
    ]
