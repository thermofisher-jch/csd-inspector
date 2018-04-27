# this dockerfile is used to build the django and celery containers.
FROM ubuntu:18.04
MAINTAINER Alexander Roemer "alexander.roemer@thermofisher.com"

# set an explit gid and uid to simplify perimissions
RUN groupadd -r inspector --gid=8247 && useradd -r -g inspector --uid=8247 inspector

# install all of the software
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
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
python-django-nose \
python-django-tastypie \
python-django-tables2 \
python-cached-property \
python-dateutil \
python-magic \
python-lzma \
python-semver

# install R deps
RUN Rscript -e "source('http://bioconductor.org/biocLite.R')"
RUN Rscript -e "library(BiocInstaller); biocLite('rhdf5')"

# setup variables
ENV PROJECT_DIR /opt/inspector
ENV PYTHONPATH  /opt/inspector/IonInspector:$PYTHONPATH
RUN mkdir -p $PROJECT_DIR
WORKDIR ${PROJECT_DIR}

# add the src code
COPY ./ /opt/inspector