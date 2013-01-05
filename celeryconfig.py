# Name of nodes to start
# here we have a single node
CELERYD_NODES="celery"

CELERY_IGNORE_RESULT = False
CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "sqlite:///celery_result.db"

BROKER_URL = "amqp://lemon:lemonpass@localhost:5672/lemon"

CELERY_IMPORTS = ("lemontest.upload", "lemontest.diagnostic")

# Extra arguments to celeryd
CELERYD_OPTS=""
CELERYD_TASK_TIME_LIMIT = 300
CELERYD_CONCURRENCY = 9

# Name of the celery config module.
CELERY_CONFIG_MODULE="celeryconfig"

# %n will be replaced with the nodename.
CELERYD_PID_FILE="/var/run/celery/%n.pid"

# Workers should run as an unprivileged user.
CELERYD_USER="celery"
CELERYD_GROUP="celery"
