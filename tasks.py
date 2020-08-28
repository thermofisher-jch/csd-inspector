#!/usr/bin/env python3
# python3 and fabric2

from pathlib import Path
from collections import defaultdict

from invoke import task


DOCKER_COMPOSE = "docker-compose"


def create_local_dirs():
    local_dev_dirs = [
        ".local/celery",
        ".local/media",
        ".local/logs",
        ".local/postgresql_log",
    ]

    for dir_name in local_dev_dirs:
        Path(dir_name).mkdir(mode=0o777, parents=True, exist_ok=True)


@task
def build(c, mkdir=False):
    if mkdir:
        create_local_dirs()

    c.run("{cmd} build".format(cmd=DOCKER_COMPOSE))


@task(build)
def up(c):
    c.run("{cmd} up".format(cmd=DOCKER_COMPOSE))


@task
def test(c, path=""):
    c.run(
        "{cmd} run django python manage.py "
        "test {path} --noinput --parallel".format(cmd=DOCKER_COMPOSE, path=path)
    )


@task
def test_profile(c, name="*"):
    c.run(
        "{cmd} run django "
        "python -m cProfile -o /var/log/inspector/test_{name}.pstats "
        "manage.py test --noinput {name}".format(cmd=DOCKER_COMPOSE, name=name)
    )


@task
def regenerate_tags(c, num=10, start=0):
    c.run(
        "{cmd} run django python manage.py "
        "regenerate_tags -s {start} {num}".format(
            cmd=DOCKER_COMPOSE, start=start, num=num
        )
    )
