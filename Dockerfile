FROM ubuntu:14.04

# setup variables
ENV PROJECT_DIR /opt/inspector

# install all of the software
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y sqlite python-django python-pip

# make a working source directory
RUN mkdir -p $PROJECT_DIR
ADD . $PROJECT_DIR

# set the working directory to be the inspector directory
WORKDIR ${PROJECT_DIR}/IonInspector
RUN pip install -r requirements.txt
# expose the development port
EXPOSE 8000