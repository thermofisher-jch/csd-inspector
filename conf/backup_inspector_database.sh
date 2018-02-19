#!/usr/bin/env bash
cd /var/lib/inspector/inspector
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.jobs.yml run django python manage.py dumpdata reports | gzip > /mnt/raid/inspector/backups/reports_$(date +%s).json.gz