import os

from invoke import task
from fabric import Connection

"""
Note for encrypted private key. For some reason, "--prompt-for-phrase"
may not work if there are multiple keys. Below is the way to ensure

Host inspector
  User deploy
  HostName inspector.itw
  IdentityFile ~/.ssh/stash_thermo_rsa
  IdentitiesOnly yes
  ProxyJump op
"""

ROOT_DIR = "/var/lib/inspector/"
REQ_DIRS = ["postgres", "celery", "media"]

GIT_CHECKOUT_URL = "ssh://git@stash.amer.thermo.com:7999/io/inspector.git"
GIT_CHECKOUT_DIR = os.path.join(ROOT_DIR, "inspector")

DOCKER_COMPOSE = (
    "docker-compose "
    "--project-directory {dir} "
    "-f {dir}/docker-compose.yml "
    "-f {dir}/docker-compose.prod.yml ".format(dir=GIT_CHECKOUT_DIR)
)

DEFAULT_USER = "deploy"
DEFAULT_HOST = "sigproc.itw"
PRODUCTION_HOSTS = ["inspector", "sigproc"]


def setup_nginx(rc):
    rc.sudo(
        "cp -p {root}/conf/nginx.conf /etc/nginx/sites-enabled/inspector.conf".format(
            root=GIT_CHECKOUT_DIR
        )
    )
    rc.sudo("service nginx reload")


def setup_cron_tasks(rc):
    if rc.run("test -d {}".format(GIT_CHECKOUT_DIR), warn=True).failed:
        return

    destination_files = [
        (
            "config/backup_inspector_database.sh",
            "/etc/cron.hourly/backup_inspector_database",
        ),
        ("conf/backup_inspector_logs.sh", "/etc/cron.hourly/backup_inspector_logs"),
        ("conf/prune_docker.sh", "/etc/cron.weekly/prune_docker"),
    ]

    for src, dst in destination_files:
        rc.sudo(
            "cp -fvp {root}/{src} {dst}".format(
                root=GIT_CHECKOUT_DIR, src=src, dst=dst,
            )
        )
        rc.sudo("chmod 755 {dst}".format(dst=dst))


def setup_appdir_and_repo(rc):
    # check and create app dir
    if rc.run("test -d {}".format(ROOT_DIR), warn=True).failed:
        rc.sudo("mkdir -p {}".format(ROOT_DIR))

    # always set permission
    rc.sudo("chown deploy:deploy {}".format(ROOT_DIR))

    for req_dir in REQ_DIRS:
        fpath = os.path.join(ROOT_DIR, req_dir)
        if rc.run("test -d {}".format(fpath), warn=True).failed:
            rc.run("mkdir -p {}".format(fpath))

        # always set permission
        rc.run("chmod 777 {}".format(fpath))

    # check and clone repo
    if rc.run("test -d {}".format(GIT_CHECKOUT_DIR), warn=True).failed:
        rc.run("git clone {} {}".format(GIT_CHECKOUT_URL, GIT_CHECKOUT_DIR))


@task
def provision(c, host=DEFAULT_HOST, user=DEFAULT_USER):
    rc = Connection(host=host, user=user)

    rc.sudo("apt-get install -y python python-pip docker-ce nginx")
    rc.sudo("pip install docker-compose")

    setup_appdir_and_repo(rc)
    setup_cron_tasks(rc)


@task
def deploy(c, tag=None, host=None, force=False, nginx=False, user=DEFAULT_USER):
    if not host:
        print("Deploy must specify host.")
        exit(1)

    if not tag:
        print("Deploy must be passed a specific git tag!")
        exit(1)

    if host in PRODUCTION_HOSTS:
        expected = "PROD"
        msg = "This looks like a deploy to production! Enter {expected} to continue: ".format(
            expected=expected
        )

        if input(msg) != expected:
            exit()

    rc = Connection(host=host, user=user)
    rc.run("uname -a")
    rc.run("hostname; whoami")

    # setup_appdir_and_repo(rc)

    with rc.cd(GIT_CHECKOUT_DIR):
        rc.run("git fetch --all --tags --prune")
        rc.run("git checkout %s --force" % tag)
        if tag == "master":
            rc.run("git pull")

        rc.run("{cmd} build".format(cmd=DOCKER_COMPOSE))
        rc.run("{cmd} down".format(cmd=DOCKER_COMPOSE))

        force_create = " --force-recreate" if force else ""
        rc.run("{cmd} {force} up -d".format(cmd=DOCKER_COMPOSE, force=force_create))

    if nginx:
        setup_nginx(rc)


@task
def regenerate_tags(c, num=10, start=0):
    c.run(
        "{cmd} run django python manage.py "
        "regenerate_tags -s {start} {num}".format(
            cmd=DOCKER_COMPOSE, start=start, num=num
        )
    )


@task
def test_conn(c):
    c.run("hostname")
    c.run("whoami")
    c.run("uname -a")
