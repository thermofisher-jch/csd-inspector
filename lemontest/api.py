

from pyramid.view import view_config
from lemontest.models import DBSession
from lemontest.models import Archive


@view_config(route_name="api_auto_name", renderer="json")
def auto_name(request):
	match = request.GET.get("name")
	names = DBSession.query(Archive.submitter_name).filter(Archive.submitter_name.contains(match)).distinct().limit(8)
	return [n[0] for n in names]