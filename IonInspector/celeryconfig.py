# Copyright (C) 2014 Ion Torrent Systems, Inc. All Rights Reserved
# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from celery import Celery
import os

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IonInspector.settings')

from django.conf import settings  # noqa

app = Celery('IonInspector.celeryconfig', backends='amqp', broker='amqp://guest:guest@rabbitmq:5672//')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
