# this dockerfile is used to build the django and celery containers.
FROM ubuntu:14.04
MAINTAINER Brian Bourke-Martin "brian.bourke-martin@thermofisher.com"

# set an explit gid and uid to simplify perimissions
RUN groupadd -r inspector --gid=8247 && useradd -r -g inspector --uid=8247 inspector

# install all of the software
RUN apt-get update && apt-get install -y python-pip celeryd python-dev r-base r-cran-rjson python-matplotlib libpq-dev

# install R deps
RUN Rscript -e "source('http://bioconductor.org/biocLite.R')"
RUN Rscript -e "library(BiocInstaller); biocLite('rhdf5')"

# setup variables
ENV PROJECT_DIR /opt/inspector
ENV PYTHONPATH  /opt/inspector/IonInspector:$PYTHONPATH
RUN mkdir -p $PROJECT_DIR
WORKDIR ${PROJECT_DIR}

# set the working directory to be the inspector directory
ADD requirements.txt ${PROJECT_DIR}/requirements.txt
RUN pip install -r requirements.txt

# add the src code
COPY ./ /opt/inspector