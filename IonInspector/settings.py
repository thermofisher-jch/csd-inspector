"""
Django settings for IonInspector project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

BASE_DIR = os.path.dirname(__file__)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY", "@0gi@=8!#@w!g8d6vibm9+576!rhe949a#w)unk+3s5f4fe0x2"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,.ngrok.io,.itw" if DEBUG else ""
).split(",")
ALLOWED_HOSTS = [] if not any(ALLOWED_HOSTS) else ALLOWED_HOSTS

# Application definition
INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "reports",
    "crispy_forms",
    "django_filters",
    "django_tables2",
    "tastypie",
    "raven.contrib.django.raven_compat",
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

ROOT_URLCONF = "IonInspector.urls"

WSGI_APPLICATION = "IonInspector.wsgi.application"

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

# HOST Note!!! this is defined by the name of the docker container which is running postgres
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "IonInspector",
        "USER": os.getenv("DATABASE_USERNAME", "docker"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "docker"),
        "HOST": "postgres",
        "PORT": "5432",
    }
}

# Cannot use sqlite with array field
# if 'test' in sys.argv or 'test_coverage' in sys.argv:  # Covers regular testing and django-coverage
#    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": {True: "DEBUG", False: "INFO"}[DEBUG],
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": {True: "DEBUG", False: "INFO"}[DEBUG],
            "class": "logging.FileHandler",
            "filename": "/var/log/inspector/django.log",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": {True: "DEBUG", False: "INFO"}[DEBUG],
            "propagate": True,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]


TEMPLATES = [
    {
        "NAME": "Inspector",
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "IonInspector.reports.context_processors.version_number",
                "IonInspector.reports.context_processors.use_datatables",
                "IonInspector.reports.context_processors.active_nav",
            ],
        },
    },
    {
        "NAME": "Diagnostics",
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": False,
        "DIRS": [os.path.join(BASE_DIR, "reports/diagnostics/templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.contrib.messages.context_processors.messages",
                "IonInspector.reports.context_processors.version_number",
                "IonInspector.reports.context_processors.use_datatables",
            ],
        },
    },
]

MEDIA_ROOT = "/var/lib/inspector/media/"
MEDIA_URL = "/media/"

CELERY_IGNORE_RESULT = False
CELERY_TASK_SERIALIZER = "pickle"
CELERY_ACCEPT_CONTENT = ["pickle", "json"]
CELERY_RESULT_BACKEND = "rpc"
CELERY_RESULT_SERIALIZER = "pickle"
SITE_ROOT = os.path.dirname(os.path.dirname(__file__))


VERSION = "1.9.1-rc.4"
try:
    # Allows contextual override of displayed version tag
    with open("/var/lib/inspector/version/VERSION", "r") as fd:
        version_override = fd.read()
        version_override = version_override.rstrip()
        if version_override > "":
            VERSION = version_override
except IOError as e:
    pass


RAVEN_CONFIG = {
    "dsn": "http://d8a6a72730684575afc834c95ebbdc60:1e5b396140654efd9b3361401f530204@sentry.itw//11",
    "release": VERSION,
}

try:
    from local_version import *
except ImportError:
    pass

try:
    from local_settings import *
except ImportError:
    pass
