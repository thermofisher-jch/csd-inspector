FROM bitnami/nginx:1.19.8-debian-10-r1
#
# Augment Bitnami's
#
ARG NGINX_VERSION=1.19.8
ARG BITNAMI_NGINX_REVISION=r1
ARG BITNAMI_NGINX_TAG=${NGINX_VERSION}-debian-10-${BITNAMI_NGINX_REVISION}
ARG UPLOAD_PLUGIN_VERSION=2.3.0
ARG NGINX_OPENTRACING_PLUGIN_VERSION=v0.14.0

USER root
ARG NGINX_VERSION
ARG UPLOAD_PLUGIN_VERSION

# Install required packages and build dependencies
# Add trusted NGINX PGP key for tarball integrity verification
# RUN gpg --keyserver pgp.mit.edu --recv-key 520A9993A1C052F8
# Download NGINX, verify integrity and extract, build, install, then remove tools before they get committed to a layer
RUN install_packages dirmngr gpg gpg-agent curl build-essential libpcre3-dev libssl-dev zlib1g-dev unzip && \
    cd /tmp && \
    curl -OL http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz && \
    curl -OL http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz.asc && \
    # gpg --verify nginx-${NGINX_VERSION}.tar.gz.asc nginx-${NGINX_VERSION}.tar.gz && \
    tar xzf nginx-${NGINX_VERSION}.tar.gz && \
    curl -OL https://github.com/fdintino/nginx-upload-module/archive/${UPLOAD_PLUGIN_VERSION}.zip && \
    unzip ${UPLOAD_PLUGIN_VERSION} && \
    rm nginx-${NGINX_VERSION}.tar.gz ${UPLOAD_PLUGIN_VERSION}.zip && \
    # Compile NGINX with desired module \
    cd /tmp/nginx-${NGINX_VERSION} && \
    rm -rf /opt/bitnami/nginx && \
    ./configure --prefix=/opt/bitnami/nginx --with-compat --add-dynamic-module=/tmp/nginx-upload-module-${UPLOAD_PLUGIN_VERSION} --with-threads --with-file-aio && \
    make && make install && \
    curl -OL https://github.com/opentracing-contrib/nginx-opentracing/releases/download/${NGINX_OPENTRACING_PLUGIN_VERSION}/linux-amd64-nginx-${NGINX_VERSION}-ot16-ngx_http_module.so.tgz && \
    tar xzf linux-amd64-nginx-${NGINX_VERSION}-ot16-ngx_http_module.so.tgz && \
    # rm linux-amd64-nginx-${NGINX_VERSION}-ot16-ngx_http_module.so.tgz && \
    curl -OL https://github.com/opentracing-contrib/nginx-opentracing/releases/download/${NGINX_OPENTRACING_PLUGIN_VERSION}/linux-amd64-nginx-${NGINX_VERSION}-ngx_http_module.so.tgz && \
    tar xzf linux-amd64-nginx-${NGINX_VERSION}-ngx_http_module.so.tgz && \
    # rm linux-amd64-nginx-${NGINX_VERSION}-ngx_http_module.so.tgz && \
    apt-get remove -y dirmngr gpg gpg-agent build-essential libpcre3-dev libssl-dev zlib1g-dev 

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
