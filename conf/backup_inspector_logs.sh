#!/usr/bin/env bash
cat /var/log/inspector/django.log | gzip > /mnt/raid/inspector/backups/django_$(date +%s).log.gz