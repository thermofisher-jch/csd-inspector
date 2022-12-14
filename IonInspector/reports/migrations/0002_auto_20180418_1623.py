# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-18 16:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="archive",
            name="archive_type",
            field=models.CharField(
                choices=[
                    (b"PGM_Run", b"PGM"),
                    (b"Proton", b"PROTON"),
                    (b"S5", b"S5"),
                    (b"OT_Log", b"OT"),
                    (b"Ion_Chef", b"CHEF"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
