# Copyright (C) 2014 Ion Torrent Systems, Inc. All Rights Reserved
# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from celery import Celery
import os

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IonInspector.settings')

app = Celery('IonInspector.celery')

app.conf.update(
    CELERY_IMPORTS="IonInspector.models"
)
