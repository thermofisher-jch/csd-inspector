import datetime
import json
import shutil
import transaction
import logging
import os.path
import math

from decimal import Decimal

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import DateTime
from sqlalchemy import Text
from sqlalchemy import UnicodeText
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import orm
from sqlalchemy import inspect

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.orm import joinedload

from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.schema import Column
from sqlalchemy.types import Time, Numeric

logger = logging.getLogger(__name__)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()
testers = dict()


archive_tags = Table('archive_tags', Base.metadata,
    Column('archive_id', Integer, ForeignKey('archives.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)


class ArchiveType(Base):
    __tablename__ = 'archivetypes'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))


class Archive(Base):
    __tablename__ = 'archives'
    id = Column(Integer, primary_key=True)
    label = Column(Unicode(255))
    site = Column(Unicode(255))
    path = Column(Unicode(255))
    time = Column(DateTime)
    status = Column(Unicode(255))
    submitter_name = Column(Unicode(255))
    archive_type = Column(Unicode(255))
    summary = Column(Unicode(30), default=u"")

    diagnostics = relationship("Diagnostic", order_by="(Diagnostic.priority.desc(), Diagnostic.name.asc())", cascade='all')

    tags = relationship("Tag", secondary=archive_tags, backref="archives")

    def __init__(self, submitter_name, label, site, archive_type, path=""):
        self.submitter_name = submitter_name
        self.label = label
        self.site = site
        self.archive_type = archive_type
        self.path = path
        self.time = datetime.datetime.now()
        self.status = u"Processing newly uploaded archive."

    # useful when trying to see what is in the DB
    def inspect(self):
        mapper = inspect(type(self))
        return mapper.attrs

    def delete_tests(self):
        for diagnostic in self.diagnostics:
            out = diagnostic.get_output_path()
            if os.path.exists(out):
                shutil.rmtree(out)
            DBSession.delete(diagnostic)


class Diagnostic(Base):
    __tablename__ = 'diagnostics'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    status = Column(Unicode(255))
    priority = Column(Integer)
    details = Column(Text)
    html = Column(Unicode(255))
    archive_id = Column(Integer, ForeignKey('archives.id'))

    archive = relationship("Archive")
    readme = None

    def __init__(self, name, archive=None):
        self.name = name
        self.archive = archive
        if archive is not None:
            self.archive_id = archive.id
            self.archive.diagnostics.append(self)
        self.status = u"Queued"
        self.priority = 0
        self.details = u""
        self.html = None
        self.readme = None

    def get_output_path(self):
        return os.path.join(self.archive.path, "test_results", self.name)

    def get_readme_path(self):
        try:
            self.readme = testers[self.archive.archive_type][self.name].readme
        except KeyError:
            self.readme = None
        return self.readme

'''
    Task: Saved user filters
'''
class SavedFilters(Base):
    __tablename__ = 'saved_filters'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    metric_type = Column(Unicode(255))
    numeric_filters = Column(Text)
    categorical_filters = Column(Text)
    type = Column(Unicode(255))

    '''
        Task: Saved user filters
        @param    metric_type:                 pmg || proton || otlog depending on metric object type it represents
        @param    numeric_filters:             numeric filters for metric object type it represents
        @param    categorical_filters:         categorical filters for metric object type it represents
        @var      numeric_filters_json:        json representation of numeric_filters
        @var      categorical_filters_json:    json representation of categorical_filters
    '''
    def __init__(self, name, metric_type, numeric_filters, categorical_filters):
        self.name = name
        self.metric_type = metric_type
        self.numeric_filters = numeric_filters
        self.categorical_filters = categorical_filters
        self.numeric_filters_json = json.loads(numeric_filters)
        self.categorical_filters_json = json.loads(categorical_filters)
        self.mapping = {
           }

    '''
        Task: reload json representations when loading object from DB, and a mapping from metric_type to metric object type
    '''
    @orm.reconstructor
    def do_onload(self):
        self.numeric_filters_json = json.loads(self.numeric_filters)
        self.categorical_filters_json = json.loads(self.categorical_filters)
        self.mapping = {
           }

    '''useful when trying to see what is in the DB'''
    def inspect(self):
        mapper = inspect(type(self))
        return mapper.attrs

    '''
        Task: creates query object from its own numerical and categorical filters
        @return    metrics_query    the SQLAlchemy query object that defines a metric data set
    '''
    def get_query(self):
        metric_object_type = self.mapping[self.metric_type]

        metrics_query = DBSession.query(metric_object_type).options(joinedload('archive')).join(Archive)

        for num_filter, params in self.numeric_filters_json.items():
            if num_filter != 'extra_filters':
                if params['max']:
                    metrics_query = metrics_query.filter(metric_object_type.get_column(params['type']) <= float(params['max']))
                if params['min']:
                    metrics_query = metrics_query.filter(metric_object_type.get_column(params['type']) >= float(params['min']))
        for cat_filter, value in self.categorical_filters_json.items():
            if value == 'None':
                metrics_query = metrics_query.filter(metric_object_type.get_column(cat_filter) == None)
            else:
                metrics_query = metrics_query.filter(metric_object_type.get_column(cat_filter) == value)

        return metrics_query

'''
    Task: Stores status information on processes such as: CSV file creation, Plot creation, Metric Report creation, Metric Report Cache creation
'''
class FileProgress(Base):
    __tablename__ = 'fileprogress'
    id = Column(Integer, primary_key=True)
    celery_id = Column(Unicode(255))
    file_type = Column(Unicode(255))
    status = Column(Unicode(255))
    progress = Column(Unicode(255))
    path = Column(Unicode(255))
    time = Column(DateTime)

    '''one to one relationship between Graph models'''
    graph = relationship('Graph', uselist=False, backref='fileprogress')

    # useful when trying to see what is in the DB
    def inspect(self):
        mapper = inspect(type(self))
        return mapper.attrs

    '''always created with a status of Queued'''
    def __init__(self, file_type):
        self.file_type = file_type
        self.status = "Queued"
        self.time = datetime.datetime.now()

'''
    Task: Graphic representation of metric data set in either a boxplot or histogram
'''
class Graph(Base):
    __tablename__ = 'graph'
    id = Column(Integer, primary_key=True)
    file_progress_id = Column(Integer, ForeignKey('fileprogress.id'))
    graph_type = Column(Unicode(255))
    column_name = Column(Unicode(255))
    title = Column(Unicode(255))
    label_x = Column(Unicode(255))
    label_y = Column(Unicode(255))
    x_axis_min = Column(Numeric(24))
    x_axis_max = Column(Numeric(24))
    y_axis_min = Column(Numeric(24))
    y_axis_max = Column(Numeric(24))

    '''useful when trying to see what is in the DB'''
    def inspect(self):
        mapper = inspect(type(self))
        return mapper.attrs

    '''
        Task: initialize this DB object
        @param    graph_type:          graph type; boxplot || histogram
        @param    column_name:         metric column that is being represented
        @param    file_progress_id:    FileProgress DB object id
    '''
    def __init__(self, graph_type, column_name, file_progress_id):
        self.file_progress_id = file_progress_id
        self.graph_type = graph_type
        self.column_name = column_name

    '''reloads definition of large numbered columns'''
    @orm.reconstructor
    def on_load(self):
        self.large_units = [
                       'ISP Wells',
                       'Live Wells',
                       'Test Fragment',
                       'Lib Wells',
                       'Polyclonal',
                       'Primer Dimer',
                       'Low Quality',
                       'Usable Reads',
                       'Cycles',
                       'Flows',
                       'Total Bases',
                       'Total Reads',
                       ]

    '''formats small numbers'''
    def format_units_small(self, quantity, sig_figs=3):
        if quantity:
            quantity = Decimal(quantity)
            return round(quantity, -int(math.floor(math.log10(abs(quantity))) - (sig_figs - 1)))
        else:
            return None

    '''all 'large' numbers do not have decimal places, to we truncate them for UI'''
    def truncate_large_numbers(self, number):
        if number:
            return int(number)
        else:
            return None

    '''gets a representation of the specifications that make up this plot for plot support'''
    def get_specs(self):
        specs = {
                 self.graph_type + '_title': self.title,
                 self.graph_type + '_label_y': self.label_y,
                 self.graph_type + '_y_axis_min': float(self.y_axis_min),
                 self.graph_type + '_y_axis_max': float(self.y_axis_max),
                 }
        if self.graph_type == 'histogram':
            specs[self.graph_type + '_label_x'] = self.label_x
            specs[self.graph_type + '_x_axis_min'] = float(self.x_axis_min)
            specs[self.graph_type + '_x_axis_max'] = float(self.x_axis_max)
        else:
            specs[self.graph_type + '_label_x'] = None
            specs[self.graph_type + '_x_axis_min'] = None
            specs[self.graph_type + '_x_axis_max'] = None
        return specs

    '''gets a representation of the specifications that make up this plot for UI'''
    def get_details(self):
        details = {
                   'title': str(self.title),
                   'label_x': str(self.label_x),
                   'label_y': str(self.label_y),
                   'column': str(self.column_name),
                   }
        if self.column_name in self.large_units:
            details['x_axis_min'] = self.truncate_large_numbers(self.x_axis_min)
            details['x_axis_max'] = self.truncate_large_numbers(self.x_axis_max)
            details['y_axis_min'] = self.truncate_large_numbers(self.y_axis_min)
            details['y_axis_max'] = self.truncate_large_numbers(self.y_axis_max)
        else:
            details['x_axis_min'] = self.format_units_small(self.x_axis_min)
            details['x_axis_max'] = self.format_units_small(self.x_axis_max)
            details['y_axis_min'] = self.format_units_small(self.y_axis_min)
            details['y_axis_max'] = self.format_units_small(self.y_axis_max)

        return details


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True)
    first_name = Column(Unicode(255))
    last_name = Column(Unicode(255))

def populate():
    session = DBSession()
    model = Archive(label=u'example_label', path=u"/home/bakennedy/Projects/lemontest_env/files/example")
    test1 = Diagnostic("Test One", model)
    test2 = Diagnostic("Test Two", model)
    session.add(model)
    transaction.commit()

def initialize_sql(engine):
    DBSession.configure(bind=engine, expire_on_commit=False)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

def initialize_testers(test_manifest, test_directory):
    import diagnostic
    global testers
    with open(test_manifest) as manifest_file:
        tests = json.load(manifest_file)
    logger.debug("Loaded Test Manifest, %s" % test_manifest)
    for archive_type, test_names in sorted(tests.items()):
        logger.debug("Archive Type %s has tests %s" % (archive_type, ", ".join(test_names)))
    testers.update(diagnostic.get_testers(tests, test_directory))
