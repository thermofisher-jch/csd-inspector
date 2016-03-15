"""
Django settings for IonInspector project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@0gi@=8!#@w!g8d6vibm9+576!rhe949a#w)unk+3s5f4fe0x2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'IonInspector',
    'south'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'IonInspector.urls'

WSGI_APPLICATION = 'IonInspector.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIR_ROOT = os.path.join(BASE_DIR, 'static')

TEST_MANIFEST = {
      "PGM_Run": [
        "Filter_Metrics",
        "Raw_Trace",
        "Version_Check",
        "ISP_Loading",
        "Chip_Temperature",
        "PGM_Temperature",
        "PGM_Pressure",
        "Chip_Noise",
        "Chip_Gain",
        "Auto_pH",
        "Seq_Kit",
        "Reference_Electrode",
        "Templating_Kit",
        "Sequencing_Kit",
        "Chip_Type"
      ],
      "Proton": [
        "Filter_Metrics",
        "Raw_Trace",
        "Version_Check",
        "ISP_Loading",
        "Chip_Noise",
        "Chip_Gain",
        "Proton_Pressure",
        "Auto_pH",
        "Seq_Kit",
        "Flow",
        "Templating_Kit",
        "Sequencing_Kit",
        "Chip_Type"
      ],
      "Raptor_S5": [
        "Filter_Metrics",
        "Raw_Trace",
        "Version_Check",
        "ISP_Loading",
        "Chip_Noise",
        "Chip_Gain",
        "Seq_Kit",
        "S5_Pressure",
        "Version_Check",
        "Raw_Trace",
        "Flow",
        "Ion_S5_Reagent_Lots",
        "Templating_Kit",
        "Sequencing_Kit",
        "Chip_Type"
      ],
      "OT_Log": [
        "Plots",
        "Sample_Pump",
        "Oil_Pump",
        "OT_Script"
      ],
      "Ion_Chef": [
        "Alarms",
        "Notifications",
        "Chef_Kit",
        "Chef_Chip",
        "Chef_Timer",
        "Chef_Version",
        "Flow",
        "Run_Type",
        "Fans"
      ]
    }

