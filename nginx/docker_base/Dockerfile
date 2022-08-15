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

