# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-18 16:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import reports.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Archive',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=255)),
                ('site', models.CharField(db_index=True, max_length=255)),
                ('time', models.DateTimeField()),
                ('submitter_name', models.CharField(db_index=True, max_length=255)),
                ('archive_type', models.CharField(choices=[(b'PGM_Run', b'PGM'), (b'Proton', b'PROTON'), (b'S5', b'S5'), (b'OT_Log', b'OT'), (b'Ion_Chef', b'CHEF')], max_length=255)),
                ('summary', models.CharField(default='', max_length=255)),
                ('taser_ticket_number', models.IntegerField(null=True)),
                ('doc_file', models.FileField(blank=True, max_length=1000, null=True, upload_to=reports.models.get_file_path)),
            ],
        ),
        migrations.CreateModel(
            name='Diagnostic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default=b'', max_length=255)),
                ('status', models.CharField(choices=[(b'U', b'Unexecuted'), (b'E', b'Executing'), (b'A', b'Alert'), (b'I', b'Info'), (b'W', b'Warning'), (b'O', b'OK'), (b'N', b'NA'), (b'F', b'Failed')], default=b'Unexecuted', max_length=255)),
                ('details', models.CharField(default=b'', max_length=2048)),
                ('error', models.CharField(default=b'', max_length=2048)),
                ('html', models.CharField(default=b'', max_length=255)),
                ('priority', models.IntegerField(default=0)),
                ('start_execute', models.DateTimeField(null=True)),
                ('archive', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='diagnostics', to='reports.Archive')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('archive', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='reports.Archive')),
            ],
        ),
    ]
