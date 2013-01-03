

from pyramid.view import view_config
from lemontest.models import DBSession
from lemontest.models import Archive


@view_config(route_name="api_auto_complete", renderer="json")
def auto_name(request):
    what = request.GET.get("what")
    match = '%%%s%%' % request.GET.get("match")
    objects = {
        "name": Archive.submitter_name,
        "site": Archive.site
    }
    field = objects.get(what)
    matches = DBSession.query(field).filter(field.ilike(match)).distinct().limit(8)
    return [m[0] for m in matches]

