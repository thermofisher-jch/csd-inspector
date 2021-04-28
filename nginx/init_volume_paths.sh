#!/bin/bash

if [[ "x${NGINX_TEMP_ROOT}" == "x" ]]
then
	echo "\$NGINX_TEMP_ROOT must be set before calling init_volume_paths.sh"
	exit -2
fi

umask 002
for ii in uwsgi scgi fastcgi proxy client_body uploads
do
	mkdir -p ${NGINX_TEMP_ROOT}/${ii}
	for jj in '0' '1' '2' '3' '4' '5' '6' '7' '8' '9'
	do
		for kk in '0' '1' '2' '3' '4' '5' '6' '7' '8' '9'
		do
			for ll in '0' '1' '2' '3' '4' '5' '6' '7' '8' '9'
			do
				mkdir -p ${NGINX_TEMP_ROOT}/${ii}/${jj}/${kk}${ll}
			done
		done
	done
done
mkdir -p ${NGINX_TEMP_ROOT}/tmp ${NGINX_TEMP_ROOT}/cache

# Only touch the top level directories so this script can tolerate being run in
# directory trees that already exist!
chown root:8247 ${NGINX_TEMP_ROOT} 
chown 8247:8247 ${NGINX_TEMP_ROOT}/* ${NGINX_TEMP_ROOT}/*/* ${NGINX_TEMP_ROOT}/*/*/*
chmod 2775 ${NGINX_TEMP_ROOT} ${NGINX_TEMP_ROOT}/* ${NGINX_TEMP_ROOT}/*/* ${NGINX_TEMP_ROOT}/*/*/*
