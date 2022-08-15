# this dockerfile is used to build the django and celery containers.
FROM ion-inspector-base-2022_08_15:bionic

# setup variables
ENV PROJECT_DIR /opt/inspector
ENV MEDIA_ROOT /var/lib/inspector/media
ENV NGINX_TEMP_ROOT /var/lib/inspector/nginxTemp
ENV PYTHONPATH  /opt/inspector/IonInspector:$PYTHONPATH
WORKDIR ${PROJECT_DIR}

# add the src code
COPY ./ ${PROJECT_DIR}

# Bootstrap cointainer volume mount points with required directories and permission bits
RUN umask 002 && ${PROJECT_DIR}/init_volume_paths.sh 

# Yield root
USER 8247
