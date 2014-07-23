import datetime
import json
import transaction
import logging
import os.path

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import DateTime
from sqlalchemy import Text
from sqlalchemy import UnicodeText
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import orm

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref

from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.dialects.drizzle.base import NUMERIC
from sqlalchemy.schema import Column

logger = logging.getLogger(__name__)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()
testers = dict()


archive_tags = Table('archive_tags', Base.metadata,
    Column('archive_id', Integer, ForeignKey('archives.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

# Author: Anthony Rodriguez
# Last Modified: 16 July 2014
class PrettyFormatter(object):

    def get_value(self, key):
        return getattr(self, type(self).columns[key])

    def get_formatted(self, key):

        if key in self.pretty_columns:
            return self.pretty_columns[key](self.get_value(key))
        else:
            return self.get_value(key)

    @classmethod
    def get_column(cls, key):
        return getattr(cls, cls.columns[key])

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

    metrics_pgm = relationship("MetricsPGM", uselist=False, backref="archive")

    metrics_proton = relationship("MetricsProton", uselist=False, backref="archive")

    tags = relationship("Tag", secondary=archive_tags, backref="archives")

    def __init__(self, submitter_name, label, site, archive_type, path=""):
        self.submitter_name = submitter_name
        self.label = label
        self.site = site
        self.archive_type = archive_type
        self.path = path
        self.time = datetime.datetime.now()
        self.status = u"Processing newly uploaded archive."

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

# Author: Anthony Rodriguez
# Last Modified: 17 July 2014
class MetricsPGM(Base, PrettyFormatter):
    __tablename__ = "metrics_pgm"
    id = Column(Integer, primary_key=True)
    archive_id = Column(Integer, ForeignKey('archives.id'))
    pgm_temperature = Column(NUMERIC(5, 2))
    pgm_pressure = Column(NUMERIC(5, 2))
    chip_temperature = Column(NUMERIC(5, 2))
    chip_noise = Column(NUMERIC(5, 2))
    system_snr = Column(NUMERIC(5, 2))
    gain = Column(NUMERIC(5, 3))
    test_fragment = Column(NUMERIC(20, 0))
    total_bases = Column(NUMERIC(20, 20))
    total_reads = Column(NUMERIC(20, 0))
    mean_read_length = Column(NUMERIC(10, 0))
    isp_wells = Column(NUMERIC(20, 0))
    live_wells = Column(NUMERIC(20, 0))
    library_wells = Column(NUMERIC(20, 0))
    isp_loading = Column(NUMERIC(3, 1))
    low_quality = Column(NUMERIC(3, 0))
    polyclonal = Column(NUMERIC(4, 2))
    primer_dimer = Column(NUMERIC(4, 2))
    usable_reads = Column(NUMERIC(4, 2))
    _50q17 = Column(NUMERIC(4, 2))
    start_ph = Column(NUMERIC(4, 2))
    end_ph = Column(NUMERIC(4, 2))
    w1_added = Column(NUMERIC(4, 2))
    barcode_set = Column(Unicode(255))
    run_type = Column(Unicode(255))
    chip_type = Column(Unicode(255))
    tss_version = Column(Unicode(255))
    seq_kit = Column(Unicode(255))
    seq_kit_lot = Column(Unicode(255))

    ordered_columns = [
                       ("PGM Temp", "pgm_temperature"),
                       ("PGM Pres", "pgm_pressure"),
                       ("Chip Temp", "chip_temperature"),
                       ("Chip Noise", "chip_noise"),
                       ("SNR", "system_snr"),
                       ("Gain", "gain"),
                       ("Test Fragment", "test_fragment"),
                       ("Total Bases", "total_bases"),
                       ("Total Reads", "total_reads"),
                       ("Mean Read Len", "mean_read_length"),
                       ("ISP Wells", "isp_wells"),
                       ("Live Wells", "live_wells"),
                       ("Lib Wells", "library_wells"),
                       ("ISP Loading (%)", "isp_loading"),
                       ("Low Quality (%)", "low_quality"),
                       ("Polyclonal (%)", "polyclonal"),
                       ("Primer Dimer (%)", "primer_dimer"),
                       ("Usable Reads (%)", "usable_reads"),
                       ("50Q17 (%)", "_50q17"),
                       ("Starting pH", "start_ph"),
                       ("Ending pH", "end_ph"),
                       ("W1 Added", "w1_added"),
                       ("Barcode Set", "barcode_set"),
                       ("Run Type", "run_type"),
                       ("Chip Type", "chip_type"),
                       ("TSS Version", "tss_version"),
                       ("Seq Kit", "seq_kit"),
                       ("Seq Kit Lot", "seq_kit_lot")
                       ]

    ordered_kits = [
                    ("(100bp) Ion Sequencing Kit", "PGM Seq 100"),
                    ("(200bp) Ion PGM(tm) 200 Sequencing Kit", "PGM Seq 200"),
                    ("Ion PGM IC 200 Sequencing Kit", "PGM Seq 200 IC"),
                    ("Ion PGM Sequencing 200 Kit v2", "PGM Seq 200 v2"),
                    ("Ion PGM Sequencing 300 Kit", "PGM Seq 300"),
                    ("Ion PGM Sequencing 400 Kit", "PGM Seq 400"),
                    ("Ion PGM Hi-Q Tech Access Kit", "PGM Seq Hi-Q TA")
                    ]

    chip_types = [
                  "314 V1",
                  "314 V2",
                  "316 V1",
                  "316 V2",
                  "318 V1",
                  "318 V2"
                  ]

    numeric_columns = ordered_columns[0:22]

    columns = dict(ordered_columns)

    kits = dict(ordered_kits)

    @orm.reconstructor
    def do_onload(self):
        self.pretty_columns = {
                               "Seq Kit": self.format_seq_kit,
                               "Chip Type": self.format_chip_type,
                               "Seq Kit Lot": self.format_seq_kit_lot,
                               "Total Bases": self.format_total_bases,
                               }

    # pretty format seq kits
    def format_seq_kit(self, raw_seq_kit):
        if raw_seq_kit:
            return self.kits[raw_seq_kit]

    # pretty format chip type
    def format_chip_type(self, raw_chip_type):
        if self.gain:
            if self.gain >= 0.65:
                return str(self.chip_type) + " V2"
            else:
                return str(self.chip_type) + " V1"

    # pretty format seq kit lot
    def format_seq_kit_lot(self, raw_seq_kit_lot):
        if raw_seq_kit_lot:
            return str(raw_seq_kit_lot).upper()
        else:
            return None

    # pretty format total bases
    def format_total_bases(self, raw_bases):
        if raw_bases and int(raw_bases) > 1000000:
            return str(int(raw_bases) / 1000000) + " M"
        elif raw_bases and int(raw_bases) < 1000000:
            return str(int(raw_bases))
        else:
            return None

# Author: Anthony Rodriguez
# Last Modified: 17 July 2014
class MetricsProton(Base, PrettyFormatter):
    __tablename__ = "metrics_proton"
    id = Column(Integer, primary_key=True)
    archive_id = Column(Integer, ForeignKey('archives.id'))
    proton_pressure = Column(NUMERIC(5, 2))
    target_pressure = Column(NUMERIC(5, 2))
    chip_noise = Column(NUMERIC(5, 2))
    isp_loading = Column(NUMERIC(3, 1))
    seq_kit = Column(Unicode(255))
    version = Column(Unicode(255))

    ordered_columns = [
                       ("Proton Pressure", "proton_pressure"),
                       ("Target Pressure", "target_pressure"),
                       ("Chip Noise", "chip_noise"),
                       ("ISP Loading", "isp_loading"),
                       ("Seq Kit", "seq_kit"),
                       ("Version", "version")
                       ]

    ordered_kits = []

    chip_types = []

    numeric_columns = ordered_columns[2:6]

    columns = dict(ordered_columns)

    kits = dict(ordered_kits)

    # pretty format seq kits
    def format_seq_kit(self, raw_seq_kit):
        if raw_seq_kit:
            return self.kits[raw_seq_kit]

    @orm.reconstructor
    def do_onload(self):
        self.pretty_columns = {
                               "Seq Kit": self.format_seq_kit,
                               }

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