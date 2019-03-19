from fabric.api import env, run, cd, sudo, local, get
from fabric.contrib.files import upload_template, put

import collections

env.user = 'deploy'
env.forward_agent = True
env.use_ssh_config = True

HOST_DATA_DIR = "/var/lib/inspector"
PRODUCTION_HOSTS = ["vulcan", "inspector"]


def dev():
    local('mkdir -p .local/celery')
    local('mkdir -p .local/media')
    local('mkdir -p .local/logs')
    local('chmod 777 .local/celery')
    local('chmod 777 .local/media')
    local('chmod 777 .local/logs')
    local("docker-compose build")
    local("docker-compose up")


def test(path=""):
    local("docker-compose run django "
          "python manage.py test %s --noinput --parallel" % path)


def test_profile(name="*"):
    local("docker-compose run django "
          "python -m cProfile -o /var/log/inspector/test_%s.pstats "
          "manage.py test --noinput %s" % (name, name))


def provision():
    sudo("apt-get install -y python python-pip docker-ce nginx")
    sudo("pip install docker-compose")
    sudo("mkdir -p {dir}".format(dir=HOST_DATA_DIR))
    sudo("chown deploy:deploy {dir}".format(dir=HOST_DATA_DIR))
    sudo("mkdir -p {dir}/postgres; chown deploy:deploy {dir}; chmod 777 {dir}/postgres".format(dir=HOST_DATA_DIR))
    sudo("mkdir -p {dir}/celery; chown deploy:deploy {dir}; chmod 777 {dir}/celery".format(dir=HOST_DATA_DIR))
    sudo("mkdir -p {dir}/media; chown deploy:deploy {dir}; chmod 777 {dir}/media".format(dir=HOST_DATA_DIR))
    # Setup db backups
    put("./conf/backup_inspector_database.sh", "/etc/cron.hourly/backup_inspector_database", use_sudo=True)
    sudo("chmod 755 /etc/cron.hourly/backup_inspector_database")
    put("./conf/backup_inspector_logs.sh", "/etc/cron.hourly/backup_inspector_logs", use_sudo=True)
    sudo("chmod 755 /etc/cron.hourly/backup_inspector_logs")
    put("./conf/prune_docker.sh", "/etc/cron.weekly/prune_docker", use_sudo=True)
    sudo("chmod 755 /etc/cron.weekly/prune_docker")
    with cd(HOST_DATA_DIR):
        run("git clone -b master ssh://git@stash.amer.thermo.com:7999/io/inspector.git")


def deploy(tag=None, force=None):
    if not tag:
        print("Deploy must be passed a specific git tag!")
        exit()
    if any([host in env.host for host in PRODUCTION_HOSTS]):
        if raw_input("This looks like a deploy to production! Enter PRODUCTION to continue: ") != "PRODUCTION":
            exit()
    with cd(HOST_DATA_DIR + "/inspector"):
        run("git fetch --all --tags --prune")
        run("git checkout %s --force" % tag)
        if tag == "master":
            run("git pull")
        run("docker-compose -f docker-compose.yml -f docker-compose.prod.yml build")
        run("docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d" +
            (" --force-recreate" if force else ""))
        upload_template("./conf/nginx.conf", "/etc/nginx/sites-enabled/inspector.conf", {

        }, use_sudo=True)
        sudo("service nginx reload")


def stats():
    diagnostics_count = collections.defaultdict(int)

    #get("/var/log/nginx/access.log.1", "./access.log")
    with open("./access.log") as fp:
        for line in fp:
            url = line.split("\"")[1]
            if "/test_results/" in url:
                if "results.html" in url:
                    diagnostics_count[url.split("/test_results/")[1].split("/")[0]] += 1
                else:
                    print (url)


    total = float(sum([v for k, v in diagnostics_count.items()]))

    for k, v in sorted(diagnostics_count.items(), key=lambda x: x[1]):
        print (k, (v/total) * 100)
