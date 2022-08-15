
VER=$(shell grep ion-inspector-base- ../Dockerfile | sed 's/FROM //g' | sed 's/:bionic//g')
IMG=${VER}:bionic
FILE=${VER}_bionic.txz
all:
	echo Version=${VER}
	docker build . -t ${IMG}
	sudo /usr/bin/docker save ${IMG} | xz -v -T 4 -9 > ${FILE}
	
transfer:
	scp ${FILE} aptadmin@updates.itw:public_html/updates_server_root/updates/software/external/
  
clean:
	rm ion-inspector-base-*