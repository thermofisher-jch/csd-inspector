import os.path
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from gnostic.models import initialize_sql
from gnostic.models import initialize_testers


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    initialize_testers(os.path.abspath("gnostic/diagnostics"))
    settings["technical_upload_root"] = \
                        os.path.abspath(settings["technical_upload_root"])
    settings["experimental_upload_root"] = \
                        os.path.abspath(settings["experimental_upload_root"])
    config = Configurator(settings=settings)
    config.add_static_view('static', 'gnostic:static', cache_max_age=3600)
    config.add_static_view('/tech', settings["technical_upload_root"])
    config.add_static_view('/exp', settings["experimental_upload_root"])
    config.add_route('index', '/')
    config.add_route('upload', '/upload/{type}')
    config.add_route('check', '/check/{archive_id}')

    config.add_subscriber('gnostic.views.add_base_template',
                      'pyramid.events.BeforeRender')
    config.scan()
    return config.make_wsgi_app()

