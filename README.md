## Host
Ubuntu: 14.04+

## Dependencies
Install fabric on your machine: http://www.fabfile.org/installing.html
Docker: https://www.docker.com/
Docker Compose: https://docs.docker.com/compose/

## Development

Run `fab dev` from this directory.

## Tests

Run all tests with `fab test` from this directory.
Run one test with `fab test:IonInspector.reports.tests.test_Chef_Kit_Details.ChefChipTestCase` from this directory.

## Deployment

Commit and push your changes to this repository.

### To Testing (inspector.vulcan.itw)

Run `fab deploy:<tag name> -H jarvis.itw` from this directory.

## Provisioning

Had to add deploy to docker group

Had to modify the nginx conf to include from /sites-enabled

Had to sudo chown 8247:8247 django.log

Had to sudo chown 8247:8247 /mnt/raid/inspector

### Upgrading postgres

docker-compose exec -e PGPASSWORD=docker postgres bash -c 'pg_dumpall --username docker --host postgres > /var/log/postgresql/backup.sql'
Delete the data dir and upgrade pg

docker-compose exec -e PGPASSWORD=docker postgres bash -c 'psql --username docker --host postgres -d IonInspector -f /var/log/postgresql/backup.sql'