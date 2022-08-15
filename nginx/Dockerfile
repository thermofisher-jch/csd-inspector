FROM nginx-base-2022-08-15:bionic
#
# Augment Bitnami's
#

USER root

# setup variables
ENV PROJECT_DIR /opt/inspector
ENV MEDIA_ROOT /var/lib/inspector/media
ENV NGINX_TEMP_ROOT /var/lib/inspector/nginxTemp
ENV PYTHONPATH  /opt/inspector/IonInspector:$PYTHONPATH

COPY ./ ${PROJECT_DIR}

# Initialize permissions for injetion to attached volumes
RUN umask 002 && ${PROJECT_DIR}/nginx/init_volume_paths.sh && \ 
    mv /opt/bitnami/nginx/conf/nginx.conf.default ${PROJECT_DIR}/orig_nginx.conf.default && \
    mv ${PROJECT_DIR}/nginx/nginx.conf /opt/bitnami/nginx/conf/nginx.conf && \
    mkdir /opt/bitnami/nginx/proxy_temp && \
    mkdir /opt/bitnami/nginx/tmp && \
    chown -R 8247:daemon /opt/bitnami && \
    chmod -R g+w /opt/bitnami 

VOLUME /opt/bitnami/nginx/logs
VOLUME /var/lib/inspector/media
VOLUME /var/lib/inspector/nginxTemp

# Set the container to be run as a non-root user by default.  This is a precaution against leaving root
# access intact, but consumers are still advised to presume their given UID will be effectively random.
USER 8247
WORKDIR /opt/bitnami/nginx
