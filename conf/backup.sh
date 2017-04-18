#!/usr/bin/env bash

#cd /var/lib/inspector/inspector

# pg_dump the ion inspector database
if ! docker-compose exec --user postgres postgres pg_dump -Fp IonInspector | gzip > IonInspector.sql.gz.in_progress; then
    echo "[!!ERROR!!] Failed to produce plain backup database $DATABASE" 1>&2
    exit
else
    mv IonInspector.sql.gz.in_progress IonInspector.sql.gz
fi

# rsync the pg_dump
rsync ./IonInspector.sql.gz backupadm@rnd10.itw:inspector/IonInspector.sql.gz
rsync -avz --delete /var/lib/inspector/media