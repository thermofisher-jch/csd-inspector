CELERY_IGNORE_RESULT = False
CELERY_RESULT_BACKEND = "database"
CELERY_RESULT_DBURI = "sqlite:///celery_result.db"

BROKER_TRANSPORT = "sqlakombu.transport.Transport"
BROKER_HOST = "sqlite:///celery_broker.db"

CELERY_IMPORTS = ("lemontest.upload", "lemontest.diagnostic")

CELERYD_LOG_FILE = "celeryd.log"
CELERYD_LOG_LEVEL = "DEBUG"