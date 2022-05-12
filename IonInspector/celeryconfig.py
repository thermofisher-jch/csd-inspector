# Copyright (C) 2014 Ion Torrent Systems, Inc. All Rights Reserved
# -*- coding: UTF-8 -*-
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "IonInspector.settings")
os.environ.setdefault("MPLBACKEND","Agg")
from django.conf import settings

celery_app = Celery(
    "IonInspector", backend="rpc://", broker="amqp://guest:guest@rabbitmq:5672//"
)
celery_app.config_from_object(settings)
celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
