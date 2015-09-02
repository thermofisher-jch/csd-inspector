import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'Beaker==1.6.4',
    'Mako==1.0.0',
    'MarkupSafe==0.23',
    'Paste==1.7.5.1',
    'PasteDeploy==1.5.2',
    'Pygments==1.6',
    'SQLAlchemy==0.9.6',
    'WTForms==2.0.1',
    'WebHelpers==1.3',
    'WebOb==1.4',
    'alembic==0.6.5',
    'amqp==1.0.13',
    'anyjson==0.3.3',
    'anykeystore==0.2',
    'apex==0.9.10dev',
    'billiard==2.7.3.34',
    'celery==3.0.25',
    'cryptacular==1.4.1',
    'gunicorn==19.1.1',
    'kombu==2.5.16',
    'matplotlib==1.4.0',
    'numpy==1.9.0',
    'oauthlib==0.6.3',
    'pbkdf2==1.3',
    'pyramid==1.5.1',
    'pyramid-beaker==0.8',
    'pyramid-celery==1.3',
    'pyramid-debugtoolbar==2.1',
    'pyramid-mailer==0.13',
    'pyramid-mako==1.0.2',
    'pyramid-tm==0.7',
    'python-dateutil==2.2',
    'python-openid==2.2.5',
    'pytz==2014.4',
    'repoze.lru==0.6',
    'repoze.sendmail==4.2',
    'requests==2.3.0',
    'requests-oauthlib==0.4.1',
    'six==1.7.3',
    'transaction==1.4.3',
    'translationstring==1.1',
    'velruse==1.1.1',
    'venusian==1.0',
    'waitress==0.8.9',
    'wsgiref==0.1.2',
    'wtforms-recaptcha==0.3.2',
    'zope.deprecation==4.1.1',
    'zope.interface==4.1.1',
    'zope.sqlalchemy==0.7.5'
]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='lemontest',
      version='0.0',
      description='lemontest',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='lemontest',
      install_requires = requires,
      entry_points = """\
      [paste.app_factory]
      main = lemontest:main
      """,
      paster_plugins=['pyramid'],
      )

