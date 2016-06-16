FROM ubuntu:14.04
MAINTAINER Brian Bourke-Martin "brian.bourke-martin@thermofisher.com"

# setup variables
ENV PROJECT_DIR /opt/inspector
RUN mkdir -p $PROJECT_DIR
WORKDIR ${PROJECT_DIR}


# install all of the software
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y sqlite python-pip rabbitmq-server celeryd python-dev r-base r-cran-rjson python-matplotlib

# set the working directory to be the inspector directory
ADD requirements.txt ${PROJECT_DIR}/requirements.txt
RUN pip install -r requirements.txt

# setup the celery service
RUN sed -i 's/ENABLED="false"/ENABLED="true"/' /etc/default/celeryd
RUN sed -i 's/CELERYD_CHDIR="\/opt\/Myproject\/"/CELERYD_CHDIR="\/opt\/inspector\/"/' /etc/default/celeryd
RUN sed -i 's/CELERY_CONFIG_MODULE="celeryconfig"/CELERY_CONFIG_MODULE="inspector_celery"/' /etc/default/celeryd
