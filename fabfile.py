from fabric.api import env, run, cd, sudo
from fabric.contrib.files import upload_template

env.user = 'deploy'
env.forward_agent = True
env.use_ssh_config = True

HOST_DATA_DIR = "/var/lib/inspector"


def provision():
    sudo("apt-get install -y python python-pip docker-engine nginx")
    sudo("pip install docker-compose")
    sudo("mkdir -p {dir}".format(dir=HOST_DATA_DIR))
    sudo("chown deploy:deploy {dir}".format(dir=HOST_DATA_DIR))
    with cd(HOST_DATA_DIR):
        run("git clone -b django ssh://git@stash.amer.thermo.com:7999/io/inspector.git")
    sudo("mkdir -p {dir}/postgres".format(dir=HOST_DATA_DIR))


def deploy():
    with cd(HOST_DATA_DIR + "/inspector"):
        run("git pull --rebase")
        run("docker-compose -f docker-compose.yml -f docker-compose.prod.yml build")
        run("docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d")
        upload_template("./conf/nginx.conf", "/etc/sites-enabled/inspector.conf", {

        })
        sudo("service nginx reload")
