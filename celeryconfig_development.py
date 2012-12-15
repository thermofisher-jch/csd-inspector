# Name of nodes to start
# here we have a single node
CELERYD_NODES="lemon"

CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "sqlite:///celery_result.db"

BROKER_URL = 'amqp://guest:guest@localhost'

CELERY_IMPORTS = ("lemontest.upload", "lemontest.diagnostic")

# Extra arguments to celeryd
CELERYD_OPTS=""

# Name of the celery config module.
CELERY_CONFIG_MODULE="celeryconfig_development"

# %n will be replaced with the nodename.
CELERYD_PID_FILE="%n.pid"

# Workers should run as an unprivileged user.
CELERYD_USER="celery"
CELERYD_GROUP="celery"
