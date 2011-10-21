import os.path
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from gnostic.models import initialize_sql

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    settings["technical_upload_root"] = \
                        os.path.abspath(settings["technical_upload_root"])
    settings["experimental_upload_root"] = \
                        os.path.abspath(settings["experimental_upload_root"])
    config = Configurator(settings=settings)
    config.add_static_view('static', 'gnostic:static', cache_max_age=3600)
    config.add_route('index', '/')
    config.add_route('upload', '/upload/{type}')
    config.scan()
    return config.make_wsgi_app()

