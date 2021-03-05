#!/bin/bash

if [[ "x${MEDIA_ROOT}" == "x" ]]
then
	echo "\$MEDIA_ROOT must be set before calling init_volume_paths.sh"
	exit -1
fi

mkdir -p ${MEDIA_ROOT}/archive_files/placeholder

# Only touch the top level directories so this script can tolerate being run in
# directory trees that already exist!
chown root:8247 ${MEDIA_ROOT} 
chown 8247:8247 ${MEDIA_ROOT}/archive_files ${MEDIA_ROOT}/archive_files/*
chmod 2775 ${MEDIA_ROOT} ${MEDIA_ROOT}/archive_files ${MEDIA_ROOT}/archive_files/*
rmdir ${MEDIA_ROOT}/archive_files/placeholder
