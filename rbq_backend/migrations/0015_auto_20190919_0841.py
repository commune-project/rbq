# Generated by Django 2.2.5 on 2019-09-19 08:41

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rbq_backend', '0014_auto_20190919_0753'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asactivity',
            name='recipients',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), null=True, size=None),
        ),
    ]