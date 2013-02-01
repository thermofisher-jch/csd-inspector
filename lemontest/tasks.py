#!/usr/bin/env python

from datetime import datetime

from celery.task import periodic_task
from celery.schedules import crontab

@periodic_task(run_every=crontab(minute=0, hour=0))
def all_time_weekly_historgram():
	"""Generate a histogram plotting the weekly number of uploads for all time!
	"""
	return None