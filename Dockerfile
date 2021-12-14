# this dockerfile is used to build the django and celery containers.
FROM ubuntu:18.04
MAINTAINER Alexander Roemer "alexander.roemer@thermofisher.com"

# set an explit gid and uid to simplify perimissions
RUN groupadd -r inspector --gid=8247 && useradd -r -g inspector --uid=8247 inspector

# install all of the software
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
gunicorn \
python-numpy \
python-pip \
python-celery \
python-dev \
python-psycopg2 \
r-base \
r-cran-rjson \
python-matplotlib \
libpq-dev \
python-lxml \
python-bs4 \
python-lzma \
python-django \
python-django-tastypie \
python-django-tables2 \
python-django-filters \
python-django-crispy-forms \
python-cached-property \
python-dateutil \
python-functools32 \
python-magic \
python-lzma \
python-pandas \
python-semver \
python-raven \
python-tblib \
python-coverage \
postgresql-client \
wait-for-it \
openssh-server

# setup ssh user for dev
RUN mkdir /var/run/sshd
RUN echo 'root:ionadmin' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# install R deps
RUN Rscript -e "source('http://bioconductor.org/biocLite.R')" \
 && Rscript -e "library(BiocInstaller); biocLite('rhdf5')" \
 && pip install 'dependency-injector>=4.0,<5.0'

# setup variables
ENV PROJECT_DIR /opt/inspector
ENV MEDIA_ROOT /var/lib/inspector/media
ENV NGINX_TEMP_ROOT /var/lib/inspector/nginxTemp
ENV PYTHONPATH  /opt/inspector/IonInspector:$PYTHONPATH
WORKDIR ${PROJECT_DIR}

# create ssh keys
RUN /usr/bin/ssh-keygen -A

# add the src code
COPY ./ ${PROJECT_DIR}

# Bootstrap cointainer volume mount points with required directories and permission bits
RUN umask 002 && ${PROJECT_DIR}/init_volume_paths.sh 

# Yield root
USER 8247
