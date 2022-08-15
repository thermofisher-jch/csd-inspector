

all: build

#HOSTNAME=`hostname`
#ifeq ($(HOSTNAME),vulkan2)
#	REQUIRED_USER='ionadmin'
#endif
#
#ifeq ($(HOSTNAME),inspector2)
#	REQUIRED_USER='deploy'
#endif
#ifneq($(USER),$(REQUIRED_USER))
#echo("must be run as $(REQUIRED_USER) on this machine")
#exit(-1)
#endif
INSPECTOR_BASE_VER=$(shell grep ion-inspector-base- Dockerfile | sed 's/FROM //g' | sed 's/:bionic//g')
NGINX_BASE_VER=$(shell grep nginx-base- nginx/Dockerfile | sed 's/FROM //g' | sed 's/:bionic//g')

VERSION=$(shell grep "VERSION = \"" IonInspector/settings.py | sed 's/VERSION = \"//g' | sed 's/\"//g')
BLDSVR=vulcan.itw:5000/

base:
	/bin/bash -c "if [ \"`sudo docker images | grep ${INSPECTOR_BASE_VER}`\" == \"\" ]; then cd docker_base; if [ ! -e ${INSPECTOR_BASE_VER}_bionic.txz ]; then wget http://updates.itw/updates/software/external/${INSPECTOR_BASE_VER}_bionic.txz ; fi; sudo /usr/bin/docker load -i ${INSPECTOR_BASE_VER}_bionic.txz ; fi"
	/bin/bash -c "if [ \"`sudo docker images | grep ${NGINX_BASE_VER}`\" == \"\" ]; then cd nginx/docker_base; if [ ! -e ${NGINX_BASE_VER}_bionic.txz ]; then wget http://updates.itw/updates/software/external/${NGINX_BASE_VER}_bionic.txz ; fi; sudo /usr/bin/docker load -i ${NGINX_BASE_VER}_bionic.txz ; fi"


build: base
	-@ if [ ! -e .local ]; then mkdir -p .local/celery .local/media .local/logs/inspector .local/postgresql_log; chmod -R 777 .local; fi
	docker-compose build
	
test: base
  # running all tests
	docker-compose run django python manage.py test --noinput --parallel
		
# for development environment.. won't return, needs to be ^C to stop		
debug: build
	docker-compose up

# for production environment.  will return
up: down
	export VERSION=$(VERSION); docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	
# to stop inspector	
down:
	export VERSION=$(VERSION); docker-compose -f docker-compose.yml -f docker-compose.prod.yml stop




deploy_prod:
	docker pull ${BLDSVR}inspector_django:$(VERSION)
	docker pull ${BLDSVR}inspector_celery:$(VERSION)
	docker pull ${BLDSVR}inspector_uploader:$(VERSION)
  
	# launch the docker images locally 
	export VERSION=$(VERSION); docker-compose -f docker-compose.yml -f docker-compose.prod.yml stop
	export VERSION=$(VERSION); docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

deploy: base
	@echo $(VERSION)
	# tag the release in git
	
	# build the images
	docker build -t ${BLDSVR}inspector_django:$(VERSION) -f Dockerfile .
	docker build -t ${BLDSVR}inspector_celery:$(VERSION) -f Dockerfile .
	docker build -t ${BLDSVR}inspector_uploader:$(VERSION) -f ./nginx/Dockerfile .
	
	# push the images to vulcan
	docker push ${BLDSVR}inspector_django:$(VERSION)
	docker push ${BLDSVR}inspector_celery:$(VERSION)
	docker push ${BLDSVR}inspector_uploader:$(VERSION)
  
	# launch the docker images locally 
	export VERSION=$(VERSION); docker-compose -f docker-compose.yml -f docker-compose.prod.yml stop
	export VERSION=$(VERSION); docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
