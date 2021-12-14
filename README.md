## Quick Take-Home Points:

* inspector repo checkout: `/var/lib/inspector`
* archive media: `/mnt/raid/inspector/media` See [docker-compose.prod.yml]()
* `inspector` user and group id (8247). See [Dockerfile]()
* `deploy` user is used on prod and stage machines

## Host

Any Docker compatible linux distribution:

* Ubuntu: 14.04+
* CentOS: 7+

## Dependencies

For both deployment and development:

* Docker Community Edition: https://www.docker.com/
    * [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
    * [Mac](https://docs.docker.com/docker-for-mac/)
    * [Windows](https://docs.docker.com/docker-for-windows/)
* Docker Compose: https://docs.docker.com/compose/
    * [Install](https://docs.docker.com/compose/install/)

For development only:

On your (dev) machine:

* (Optional 1) [Fabric 1.x](http://www.fabfile.org/installing-1.x.html).
* (Optional 2) [Python 3.4+](https://www.python.org/downloads/).


## Development

Run `fab dev` from this directory. See [fabfile.py]().

Or run this script with Python 3.4+. See [setup_dev_environment.py]() for more details.

    python3 setup_dev_environment.py
    docker-compose build
    docker-compose up

The inspector should be running at http://localhost:8090/. See [docker-compose.override.yml]()


## Tests

* Run all tests with `fab test` from this directory.
* Run one test with `fab test:IonInspector.reports.tests.test_Chef_Kit_Details.ChefChipTestCase` from this directory.

Or run these commands:

    # running all tests
    docker-compose run django python manage.py test --noinput --parallel

    # running one tests
    docker-compose run django python manage.py test \
        IonInspector.reports.tests.test_Chef_Kit_Details.ChefChipTestCase \
        --noinput --parallel 


## Deployment

Commit and push your changes to this repository, then create a tag 
marking the commit point with the desired deployment state.  Tags
are expected to embed a semantic version tag formatted as follows.
Pay close attention to use of punctuation and digits.

   release-<MAJOR>.<MINOR>.<PATCH>

For a pre-release test candidate, use:

   release-<MAJOR>.<MINOR>.<PATCH>-rc.<RCNUM>


### To Staging (inspector.sigproc.itw)

Run `fab deploy:<tag name> -H sigproc.itw` from this directory.

Or run these commands when logging in as `deploy@sigproc.itw`:

    cd /var/lib/inspector/inspector
    git fetch --all --tags --prune
    git checkout <tag> --force
    # if using 'master' instead of <tag>, run `git pull`
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    # add `--force-recreate` if starting from scratch/fresh

If nginx conf has changed:

    scp -p ./conf/nginx.conf $server:/etc/nginx/sites-enabled/inspector.conf
    ssh deploy@$server 'service nginx reload'

## Provisioning

* Had to add `deploy` to `docker` group
* Had to modify the nginx conf to include from /sites-enabled
* Had to run `sudo chown 8247:8247 django.log`
* Had to run `sudo chown 8247:8247 /mnt/raid/inspector/media/archive_files`

### Upgrading postgres

pg dump:

    docker-compose exec -e PGPASSWORD=docker postgres bash -c 'pg_dumpall --username docker --host postgres > /var/log/postgresql/backup.sql'

Delete the data dir and upgrade pg

    docker-compose exec -e PGPASSWORD=docker postgres bash -c 'psql --username docker --host postgres -d IonInspector -f /var/log/postgresql/backup.sql'


## Bring Inspector up and down

### Development Environment

From the local clone direcotry, i.e. this directory:

    docker-compose up

and `Control+C` to bring down services gracefully.

### Production Environment

from inspector directory (`/var/lib/inspector/inspector`)

Graceful shutdown

    docker-compose down

Bring up in daemon mode

    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

