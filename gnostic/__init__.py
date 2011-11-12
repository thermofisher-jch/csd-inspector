import logging
import os.path
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from gnostic.models import initialize_sql
from gnostic.models import initialize_testers


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    logging.basicConfig()
    log = logging.getLogger(__file__)
    log.info("Starting Gnostic.")
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    initialize_testers(os.path.abspath("gnostic/diagnostics"))
    # I have an inexplicable distrust of the relative file paths given in
    # the config file.  This step also lets us die early if they're erroneous.
    settings["technical_upload_root"] = \
                        os.path.abspath(settings["technical_upload_root"])
    config = Configurator(settings=settings)
    # configure various URL routes and
    config.add_static_view('static', 'gnostic:static', cache_max_age=3600)
    config.add_static_view('output', settings["technical_upload_root"])
    config.add_route('index', '/')
    config.add_route('upload', '/upload')
    config.add_route('check', '/check/{archive_id}')
    config.add_route('reports', '/reports')
    config.add_route('documentation', '/documentation')
    # This lets the function 'add_base_template' tack the layout template into
    # the mystical universe of chameleon templating so that the other templates
    # can put themselves inside layout.pt like they're supposed to.
    config.add_subscriber('gnostic.views.add_base_template',
                      'pyramid.events.BeforeRender')
    config.scan()
    return config.make_wsgi_app()

