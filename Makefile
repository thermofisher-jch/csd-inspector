

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

VERSION=$(shell grep "VERSION = \"" IonInspector/settings.py | sed 's/VERSION = \"//g' | sed 's/\"//g')

build:
	-@mkdir -p .local/celery .local/media .local/logs/inspector .local/postgresql_log; chmod -R 777 .local
	docker-compose build
	
test:
  # running all tests
	docker-compose run django python manage.py test --noinput --parallel
		
# for development environment.. won't return, needs to be ^C to stop		
debug: build
	docker-compose up

# for production environment.  will return
up:
	docker-compose down	
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	
# to stop inspector	
down:
	docker-compose down	


deploy:
	@echo $(VERSION)
	# tag the release in git
	docker build -t vulcan.itw:5000/inspector_django:$(VERSION) -f Dockerfile .
	docker build -t vulcan.itw:5000/inspector_celery:$(VERSION) -f Dockerfile .
	docker build -t vulcan.itw:5000/inspector_uploader:$(VERSION) -f ./nginx/Dockerfile .
	
	# launch the docker images locally 
	docker-compose down
	export VERSION=$(VERSION); docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
