# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-07-25 19:59
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_auto_20181108_1440'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnostic',
            name='results',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}, null=True),
        ),
        migrations.AlterField(
            model_name='archive',
            name='archive_type',
            field=models.CharField(choices=[(b'PGM_Run', b'PGM'), (b'Proton', b'PROTON'), (b'S5', b'S5'), (b'Valkyrie', b'Genexus'), (b'OT_Log', b'OT'), (b'Ion_Chef', b'CHEF')], max_length=255, null=True),
        ),
    ]