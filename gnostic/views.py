from gnostic.models import DBSession
from gnostic.models import MyModel
from pyramid.view import view_config
import datetime

@view_config(route_name="home", renderer="templates/index.pt")
def index(request):
    #dbsession = DBSession()
    #root = dbsession.query(MyModel).filter(MyModel.name==u'root').first()
    now = datetime.datetime.now()
    label = now.strftime("%Y-%m-%d_%H-%M-%S")
    return {'label':label}
