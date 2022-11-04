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
libpq-dev \
python-bs4 \
python-coverage \
python-django \
python-django-tastypie \
python-django-tables2 \
python-django-filters \
python-django-crispy-forms \
python-cached-property \
python-dateutil \
python-functools32 \
python-lxml \
python-lzma \
python-matplotlib \
python-magic \
python-numpy \
python-opencv \
python-pandas \
python-semver \
python-skimage \
python-scipy \
python-raven \
python-tblib \
mupdf-tools \
imagemagick \
postgresql-client \
wait-for-it && \
apt-get autoremove -y && \
apt-get purge -y && \
apt-get clean -y && \
rm -rf /var/lib/apt/lists/*lz4

# install R deps
RUN Rscript -e "source('http://bioconductor.org/biocLite.R')" \
 && Rscript -e "library(BiocInstaller); biocLite('rhdf5')" \
 && pip install 'dependency-injector>=4.0,<5.0'

