import os
from fabric.api import env, run, cd, sudo, local
from fabric.contrib.files import upload_template

env.user = 'deploy'
env.forward_agent = True
env.use_ssh_config = True

HOST_DATA_DIR = "/var/lib/inspector"
PRODUCTION_HOSTS = ["vulcan", "inspector"]


def dev():
    local("docker-compose build")
    local("docker-compose up")


def test(path=""):
    local("docker-compose run django python manage.py test --noinput %s" % path)


def provision():
    sudo("apt-get install -y python python-pip docker-ce nginx")
    sudo("pip install docker-compose")
    sudo("mkdir -p {dir}".format(dir=HOST_DATA_DIR))
    sudo("chown deploy:deploy {dir}".format(dir=HOST_DATA_DIR))
    sudo("mkdir -p {dir}/postgres; chown deploy:deploy {dir}; chmod 777 {dir}/postgres".format(dir=HOST_DATA_DIR))
    sudo("mkdir -p {dir}/celery; chown deploy:deploy {dir}; chmod 777 {dir}/celery".format(dir=HOST_DATA_DIR))
    sudo("mkdir -p {dir}/media; chown deploy:deploy {dir}; chmod 777 {dir}/media".format(dir=HOST_DATA_DIR))
    with cd(HOST_DATA_DIR):
        run("git clone -b master ssh://git@stash.amer.thermo.com:7999/io/inspector.git")


def deploy(tag=None):
    if not tag:
        print "Deploy must be passed a specific git tag!"
        exit()
    if any([host in env.host for host in PRODUCTION_HOSTS]):
        if raw_input("This looks like a deploy to production! Enter PRODUCTION to continue: ") != "PRODUCTION":
            exit()
    with cd(HOST_DATA_DIR + "/inspector"):
        run("git fetch")
        run("git checkout %s" % tag)
        run("git fetch")
        run("docker-compose -f docker-compose.yml -f docker-compose.prod.yml build")
        run("docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d")
        upload_template("./conf/nginx.conf", "/etc/nginx/sites-enabled/inspector.conf", {

        }, use_sudo=True)
        sudo("service nginx reload")
