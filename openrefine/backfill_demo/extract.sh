#!/bin/sh

export DOCKER_HOST='ssh://docker-inspector'
docker-compose -f ../../docker-compose.yml -f ../../docker-compose.prod.yml exec postgres psql -U docker IonInspector -tA -c "select id,site,submitter_name,archive_type,doc_file,search_tags from reports_archive where archive_type = 'Valkyrie';" -o /tmp/export.dat
docker cp inspector_postgres_1:/tmp/export.dat /tmp
# docker-compose -f ../../docker-compose.yml -f ../../docker-compose.prod.yml exec postgres rm /tmp/export.dat
unset DOCKER_HOST
