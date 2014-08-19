import logging
import os.path
import pyramid_beaker
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from lemontest.models import initialize_sql
from lemontest.models import initialize_testers


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    log = logging.getLogger(__file__)
    log.info("Starting Lemon Test.")
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    # I have an inexplicable distrust of the relative file paths given in
    # the config file.  This step also lets us die early if they're erroneous.
    settings["upload_root"] = os.path.abspath(settings["upload_root"])
    settings["test_root"] = os.path.abspath(settings["test_root"])
    settings["test_manifest"] = os.path.abspath(settings["test_manifest"])

    # Setup cache configuration
    pyramid_beaker.set_cache_regions_from_settings(settings)

    # Create configurator
    config = Configurator(settings=settings)

    # Set up session configuration
    session_factory = pyramid_beaker.session_factory_from_settings(settings)
    config.set_session_factory(session_factory)

    config.include('apex', route_prefix='/auth')

    # configure various URL routes and
    config.add_static_view('static', 'lemontest:static', cache_max_age=3600)
    config.add_static_view('archives', settings["upload_root"])
    config.add_static_view('output', settings["upload_root"])
    config.add_route('index', '/')
    config.add_route('upload', '/upload')
    config.add_route('check', '/check/{archive_id:\d+}')
    config.add_route('rerun', '/check/{archive_id:\d+}/rerun')
    config.add_route('super_delete', '/check/{archive_id:\d+}/super_delete')
    config.add_route('reports', '/reports')
    config.add_route('documentation', '/documentation')
    config.add_route('test_readme', '/test/{test_name}/README')
    config.add_route('stats', '/stats')
    config.add_route('old_browser', '/old_browser')

    config.add_route('api_auto_complete', '/api/auto_complete')

    # New things to add
    config.add_route('analysis_pgm', '/trace/pgm')
    config.add_route('analysis_proton', '/trace/proton')
    config.add_route('analysis_show_hide', '/analysis/showhide')
    config.add_route('analysis_csv', '/analysis.csv')
    config.add_route('analysis_save_filter', '/trace/save_filter')
    config.add_route('analysis_apply_filter', '/trace/apply_filter')
    config.add_route('analysis_delete_saved_filter', '/trace/delete_saved_filter')
    config.add_route('analysis_csv_update', '/trace/csv_update')
    config.add_route('analysis_serve_csv','/trace/csv')

    # This lets the function 'add_base_template' tack the layout template into
    # the mystical universe of chameleon templating so that the other templates
    # can put themselves inside layout.pt like they're supposed to.
    config.add_subscriber('lemontest.views.add_helpers',
                        'pyramid.events.BeforeRender')
    config.scan()
    initialize_testers(settings["test_manifest"], settings["test_root"])
    return config.make_wsgi_app()

