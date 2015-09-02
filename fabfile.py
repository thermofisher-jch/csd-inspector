from fabric.api import local, warn_only, settings, run, get
from fabric.colors import green, red
import os
import platform

ENVIRONMENTS = {
    "production": {
        "hostname": "example.com",
    },
    "testing": {
        "hostname": "sherlock.itw",
        "extra_vars": "is_test_instance=true"
    },
    "inspector2": {
        "hostname": "inspector2.itw",
        "extra_vars": ""
    }
}


def deploy(environment_name="testing", provision=False):
    hostname = ENVIRONMENTS.get(environment_name, {}).get("hostname")
    extra_vars = ENVIRONMENTS.get(environment_name, {}).get("extra_vars")

    ansible_file = "site.yml" if provision else "site.yml"
    if hostname:
        with open("temp.inventory.ini", "w") as inventory:
            inventory.write(str(hostname))
        with warn_only():
            local(
                "ANSIBLE_SSH_PIPELINING=True ANSIBLE_HOST_KEY_CHECKING=False ANSIBLE_SSH_ARGS='-o ForwardAgent=yes' ansible-playbook --extra-vars \""+extra_vars+"\" -u ionadmin -i temp.inventory.ini installation/" + ansible_file,
                capture=False)
        os.remove("temp.inventory.ini")
        print green("Deployed to %s!" % hostname)
        if platform.system() == "Darwin":
            local("say Deployed to %s" % environment_name)
            local("osascript -e 'display notification \"to %s\" with title \"Deployed\"'" % environment_name)
    else:
        print red("Could not find environment %s. Choices are %s." % (environment_name, ", ".join(ENVIRONMENTS.keys())))


def provision(environment_name="testing"):
    deploy(environment_name, provision=True)


def clone_db():
    with settings(host_string="inspector.itw", user="ionadmin"):
        run("pg_dump -U lemon lemondb -f /tmp/lemondb.sql --clean")
        get("/tmp/lemondb.sql", "/tmp/lemondb.sql")
        local("psql -U lemon -d lemondb -f /tmp/lemondb.sql")
