FROM ubuntu:14.04
MAINTAINER Brian Bourke-Martin "brian.bourke-martin@thermofisher.com"

# install all of the software
RUN apt-get update && apt-get install -y sqlite python-pip celeryd python-dev r-base r-cran-rjson python-matplotlib libpq-dev vim

# setup variables
ENV PROJECT_DIR /opt/inspector
ENV PYTHONPATH  /opt/inspector/IonInspector:$PYTHONPATH
RUN mkdir -p $PROJECT_DIR
WORKDIR ${PROJECT_DIR}

# set the working directory to be the inspector directory
ADD requirements.txt ${PROJECT_DIR}/requirements.txt
RUN pip install -r requirements.txt

# setup the celery service
RUN sed -i 's/ENABLED="false"/ENABLED="true"/' /etc/default/celeryd
RUN sed -i 's/CELERYD_CHDIR="\/opt\/Myproject\/"/CELERYD_CHDIR="\/opt\/inspector\/"/' /etc/default/celeryd
RUN sed -i 's/CELERYD_OPTS="--time-limit=300 --concurrency=8"/CELERYD_OPTS="--time-limit=300 --concurrency=8 --broker=amqp:\/\/guest:guest@rabbitmq:5672\/\/ --config=IonInspector.celeryconfig"/' /etc/default/celeryd
RUN echo "export DJANGO_SETTINGS_MODULE=\"IonInspector.settings\"" >> /etc/default/celeryd