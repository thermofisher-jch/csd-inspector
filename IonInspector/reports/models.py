"""
This will hold all of the data models for the inspector.
"""
import errno
import importlib
import zipfile
from subprocess import *

from cached_property import cached_property
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField

from IonInspector.reports.diagnostics.common.inspector_utils import *
from celeryconfig import celery_app
from reports.utils import force_symlink

from reports.tags.chef import get_chef_tags
from reports.tags.pgm import get_pgm_tags
from reports.tags.proton import get_proton_tags
from reports.tags.s5 import get_s5_tags
from reports.tags.ot import get_ot_tags

# check to see if the settings are configured
if not settings.configured:
    settings.configure()

# define constants
PGM_RUN = "PGM_Run"
PROTON = "Proton"
S5 = "S5"
OT_LOG = "OT_Log"
ION_CHEF = "Ion_Chef"
VALK = "Valkyrie"

CATEGORY_SEQUENCING = "SEQ"
CATEGORY_SAMPLE_PREP = "PRE"

DIAGNOSTICS_SCRIPT_DIR = '/opt/inspector/IonInspector/reports/diagnostics'
TEST_MANIFEST = {
    PGM_RUN: [
        ("Filter_Metrics", CATEGORY_SEQUENCING),
        ("Raw_Trace", CATEGORY_SEQUENCING),
        ("Chip_Status", CATEGORY_SEQUENCING),
        ("Run_Chef_Details", CATEGORY_SEQUENCING),
        ("Auto_pH", CATEGORY_SEQUENCING),
        ("Run_Kit_Details", CATEGORY_SEQUENCING),
        ("Chip_Type", CATEGORY_SEQUENCING),
        ("Test_Fragments", CATEGORY_SEQUENCING),
        ("Pressure_And_Temperature", CATEGORY_SEQUENCING),
        ("Barcode_Report", CATEGORY_SEQUENCING),
        ("Run_Sequence_Details", CATEGORY_SEQUENCING)
    ],
    PROTON: [
        ("Filter_Metrics", CATEGORY_SEQUENCING),
        ("Raw_Trace", CATEGORY_SEQUENCING),
        ("Chip_Status", CATEGORY_SEQUENCING),
        ("Run_Chef_Details", CATEGORY_SEQUENCING),
        ("Auto_pH", CATEGORY_SEQUENCING),
        ("Run_Kit_Details", CATEGORY_SEQUENCING),
        ("Chip_Type", CATEGORY_SEQUENCING),
        ("Test_Fragments", CATEGORY_SEQUENCING),
        ("Pressure_And_Temperature", CATEGORY_SEQUENCING),
        ("Experiment_Errors", CATEGORY_SEQUENCING),
        ("Barcode_Report", CATEGORY_SEQUENCING),
        ("Run_Sequence_Details", CATEGORY_SEQUENCING)
    ],
    S5: [
        ("Filter_Metrics", CATEGORY_SEQUENCING),
        ("Raw_Trace", CATEGORY_SEQUENCING),
        # ("Raw_Trace_Preview", CATEGORY_SEQUENCING),
        ("Chip_Status", CATEGORY_SEQUENCING),
        ("Run_Chef_Details", CATEGORY_SEQUENCING),
        ("S5_Reagents", CATEGORY_SEQUENCING),
        ("Run_Kit_Details", CATEGORY_SEQUENCING),
        ("Chip_Type", CATEGORY_SEQUENCING),
        ("Test_Fragments", CATEGORY_SEQUENCING),
        ("Pressure_And_Temperature", CATEGORY_SEQUENCING),
        ("Experiment_Errors", CATEGORY_SEQUENCING),
        ("Barcode_Report", CATEGORY_SEQUENCING),
        ("Run_Sequence_Details", CATEGORY_SEQUENCING)
    ],
    VALK: [
        #("Filter_Metrics", CATEGORY_SEQUENCING),
        #("Raw_Trace", CATEGORY_SEQUENCING),
        # ("Raw_Trace_Preview", CATEGORY_SEQUENCING),
        ("Chip_Status", CATEGORY_SEQUENCING),
        #("Run_Chef_Details", CATEGORY_SEQUENCING),
        ("S5_Reagents", CATEGORY_SEQUENCING),
        #("Run_Kit_Details", CATEGORY_SEQUENCING),
        ("Chip_Type", CATEGORY_SEQUENCING),
        #("Test_Fragments", CATEGORY_SEQUENCING),
        #("Pressure_And_Temperature", CATEGORY_SEQUENCING),
        ("Experiment_Errors", CATEGORY_SEQUENCING),
        ("Barcode_Report", CATEGORY_SEQUENCING),
        #("Run_Sequence_Details", CATEGORY_SEQUENCING)
    ],
    OT_LOG: [
        ("OT_Plots", CATEGORY_SAMPLE_PREP),
        ("Sample_Pump", CATEGORY_SAMPLE_PREP),
        ("Oil_Pump", CATEGORY_SAMPLE_PREP),
        ("OT_Script", CATEGORY_SAMPLE_PREP),
        ("Flowmeter", CATEGORY_SAMPLE_PREP)
    ],
    ION_CHEF: [
        ("Chef_Flexible_Workflow", CATEGORY_SAMPLE_PREP),
        ("Chef_Notifications", CATEGORY_SAMPLE_PREP),
        ("Chef_Kit_Details", CATEGORY_SAMPLE_PREP),
        ("Chef_Timer", CATEGORY_SAMPLE_PREP),
        ("Chef_Version", CATEGORY_SAMPLE_PREP),
        ("Chef_Run_Details", CATEGORY_SAMPLE_PREP),
        ("Chef_Run_Log", CATEGORY_SAMPLE_PREP),
        ("Integrity_Check", CATEGORY_SAMPLE_PREP)
    ]
}


def get_file_path(instance, filename):
    """
    Used for determining a path for the file to be saved to
    :param instance: This archive instance
    :param filename: The name of the file to be saved
    :return: The path to save the archive file to
    """

    media_dir = settings.MEDIA_ROOT
    if not os.path.exists(media_dir):
        os.mkdir(media_dir, 0777)
        os.chmod(media_dir, 0777)

    archive_dirs = os.path.join(media_dir, 'archive_files')
    if not os.path.exists(archive_dirs):
        os.mkdir(archive_dirs)
    os.chmod(archive_dirs, 0777)

    instance_dir = os.path.join(archive_dirs, str(instance.pk))
    if not os.path.exists(instance_dir):
        os.mkdir(instance_dir, 0777)
    os.chmod(instance_dir, 0777)

    return os.path.join('archive_files', str(instance.pk), filename)


class Archive(models.Model):
    """An archive sample"""

    # define a list of archive types
    ARCHIVE_TYPES = (
        (PGM_RUN, 'PGM'),
        (PROTON, 'PROTON'),
        (S5, 'S5'),
        (VALK, 'VALK'),
        (OT_LOG, 'OT'),
        (ION_CHEF, 'CHEF')
    )

    # model attributes
    identifier = models.CharField(max_length=255)

    # the site from which the archive was found
    site = models.CharField(max_length=255, db_index=True)

    # the time that it was submitted
    time = models.DateTimeField()

    # the name of the person who submitted it
    submitter_name = models.CharField(max_length=255, db_index=True)

    # the type of archive which this is
    archive_type = models.CharField(max_length=255, choices=ARCHIVE_TYPES, null=True)

    # any summary information
    summary = models.CharField(max_length=255, default=u"")

    # an optional taser ticket reference
    taser_ticket_number = models.IntegerField(null=True)

    # use the get_file_path method to direct the file field on where to store the zip file
    doc_file = models.FileField(upload_to=get_file_path, blank=True, null=True, max_length=1000)

    # used to search the runs for tags
    search_tags = ArrayField(models.CharField(max_length=255), default=list, db_index=True)

    # model relationships
    # diagnostics : Foreign Key from diagnostic class

    def detect_archive_type(self):
        """This will attempt to auto detect the archive type"""

        # if the base archive is a simple log or csv then this is a one touch
        if self.doc_file.path.endswith('.log') or self.doc_file.path.endswith('.csv'):
            return OT_LOG

        # everything else needs the archive to be extracted
        archive_dir = os.path.dirname(self.doc_file.path)
        self.extract_archive()

        # if the explog has the PGM HW key, then this is a PGM
        try:
            explog = read_explog(archive_dir)
            if 'PGM HW' in explog:
                return PGM_RUN

            # by reading the explog entry "platform" we should be able to differentiate between proton and S5
            platform = explog.get('Platform', '')
            if platform == 'proton':
                return PROTON

            if platform == 'S5':
                return S5

            if platform == 'Valkyrie':
                return VALK

        except Exception as e:
            pass

        # if the extracted files has a var directory then this is a ion chef
        if os.path.exists(os.path.join(archive_dir, 'var')):
            return ION_CHEF

        # if we have gotten to this point then we really have no idea what kind of archive this is and this
        # should be considered an error condition
        raise Exception('Cannot determine the archive type.')

    def extract_archive(self):
        """This will extract all of the data from the archive to the folder for evaluation"""
        # if the file is not there then there is nothing we can do
        if not os.path.exists(self.doc_file.path):
            raise Exception("The archive file is not present at: " + self.doc_file.path)

        archive_dir = os.path.dirname(self.doc_file.path)
        if self.doc_file.path.endswith('.zip'):
            doc_archive = zipfile.ZipFile(self.doc_file.path)
            doc_archive.extractall(path=archive_dir)
            doc_archive.close()

        # Some chef archives contains files with no read permission. This seems to kill the python tar library. So
        # instead we are using a subprocess to extract then chmod
        elif self.doc_file.path.endswith('.tar') or self.doc_file.path.endswith(
                '.tar.gz') or self.doc_file.path.endswith('.tar.xz'):
            check_call(["tar", "-xf", self.doc_file.path, "--directory", archive_dir])
            check_call(["chmod", "755", "-R", archive_dir])

        # Watch out. Some ot logs are are .log and some are .csv
        elif self.doc_file.path.endswith('.log') or self.doc_file.path.endswith('.csv'):  # One Touch
            target_path = os.path.join(archive_dir, "onetouch.log")
            if not os.path.exists(target_path):
                shutil.copy(self.doc_file.path, target_path)

    def execute_diagnostics(self, async=True):
        """this method will execute all of the diagnostics"""

        self.extract_archive()
        self.generate_tags()

        # handle coverage analysis specific workarounds here
        archive_dir = os.path.dirname(self.doc_file.path)
        coverage_analysis_path = os.path.join(archive_dir, 'coverageAnalysis')
        if os.path.exists(coverage_analysis_path):
            # we are assuming any subdirectories here will be barcoded subdirectories since the pattern when creating the CSA only specifies content which is indicative of a barcode
            for subdir in [name for name in os.listdir(coverage_analysis_path) if
                           os.path.isdir(os.path.join(coverage_analysis_path, name))]:
                force_symlink(os.path.join(settings.STATICFILES_DIRS[0], 'coverageAnalysis', 'flot'),
                              os.path.join(coverage_analysis_path, subdir, 'flot'))
                force_symlink(os.path.join(settings.STATICFILES_DIRS[0], 'coverageAnalysis', 'lifechart'),
                              os.path.join(coverage_analysis_path, subdir, 'lifechart'))

        # delete all other diagnostics first
        tests = Diagnostic.objects.filter(archive=self)
        for run_test in tests:
            run_test.delete()

        # get all of the diagnostics to be run on this type of archive
        archive_type = str(self.archive_type)
        diagnostic_list = TEST_MANIFEST[archive_type][:]

        # if this is a sequencer CSA/FSA with chef information it would
        # make sense to optionally add all of the chef tests
        if archive_type in [S5, PGM_RUN, PROTON] and os.path.exists(os.path.join(archive_dir, 'var')):
            diagnostic_list += TEST_MANIFEST[ION_CHEF]

        # make tests folder
        test_folder = os.path.join(self.archive_root, 'test_results')
        if not os.path.exists(test_folder):
            os.mkdir(test_folder)
            os.chmod(test_folder, 0777)

        for diagnostic_name, diagnostic_category in diagnostic_list:
            diagnostic = Diagnostic(name=diagnostic_name, archive=self, category=diagnostic_category)
            diagnostic.save()
            if async:
                celery_app.send_task('reports.tasks.execute_diagnostic', (diagnostic.id,))
            else:
                diagnostic.execute()

    def generate_tags(self):
        if self.archive_type == OT_LOG:
            search_tags = get_ot_tags(self.archive_root)
        elif self.archive_type == ION_CHEF:
            search_tags = get_chef_tags(self.archive_root)
        elif self.archive_type == PGM_RUN:
            search_tags = get_pgm_tags(self.archive_root)
        elif self.archive_type == PROTON:
            search_tags = get_proton_tags(self.archive_root)
        elif self.archive_type == S5:
            search_tags = get_s5_tags(self.archive_root)
        else:
            search_tags = []
        self.search_tags = list(set([tag.strip() for tag in search_tags]))
        self.save()

    @cached_property
    def archive_root(self):
        """The archive root path"""
        return os.path.dirname(self.doc_file.path)

    def is_sequencer(self):
        return self.archive_type in [S5, PROTON, PGM_RUN, VALK]


@receiver(pre_delete, sender=Archive, dispatch_uid="delete_archive")
def on_archive_delete(sender, instance, **kwargs):
    """Triggered when the archives are deleted"""

    archive_root = os.path.join(settings.MEDIA_ROOT, 'archive_files', str(instance.pk))
    try:
        shutil.rmtree(archive_root)
    except:
        # do nothing here as this is just a clean up
        pass


class Diagnostic(models.Model):
    """A test to run against an archive"""

    UNEXECUTED = "Unexecuted"
    EXECUTING = "Executing"
    ALERT = "Alert"
    INFO = "Info"
    WARNING = "Warning"
    OK = "OK"
    NA = "NA"
    FAILED = "Failed"
    DIAGNOSTIC_STATUSES = (
        ('U', UNEXECUTED),
        ('E', EXECUTING),
        ('A', ALERT),
        ('I', INFO),
        ('W', WARNING),
        ('O', OK),
        ('N', NA),
        ('F', FAILED)
    )

    class Meta:
        ordering = ['name']

    # model attributes
    name = models.CharField(max_length=255, default="")
    status = models.CharField(max_length=255, choices=DIAGNOSTIC_STATUSES, default=UNEXECUTED)
    details = models.CharField(max_length=2048, default="")
    error = models.CharField(max_length=2048, default="")
    html = models.CharField(max_length=255, default="")
    priority = models.IntegerField(default=0)
    start_execute = models.DateTimeField(null=True)

    CATEGORY_CHOICES = (
        (CATEGORY_SEQUENCING, "SEQUENCING"),
        (CATEGORY_SAMPLE_PREP, "SAMPLE_PREP")
    )

    category = models.CharField(max_length=3, default=CATEGORY_SEQUENCING, choices=CATEGORY_CHOICES)

    # model relationships
    archive = models.ForeignKey(Archive, related_name="diagnostics", on_delete=models.CASCADE)

    @cached_property
    def display_name(self):
        return self.name.replace("_", " ").title()

    @cached_property
    def diagnostic_root(self):
        """returns the root of the files used in the diagnostic"""
        test_folder = os.path.join(self.archive.archive_root, 'test_results')
        results_folder = os.path.join(test_folder, self.name)
        if not os.path.exists(results_folder):
            # other workers may have already made the folder
            try:
                os.mkdir(results_folder)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        return results_folder

    @cached_property
    def readme(self):
        return os.path.exists(
            os.path.join(settings.SITE_ROOT, 'IonInspector', 'reports', 'diagnostics', self.name, 'README'))

    def execute(self):
        """This will execute the this diagnostic"""

        try:
            # set the status
            self.status = self.EXECUTING
            self.start_execute = timezone.now()
            self.save()

            # execute the script
            diagnostic_module = importlib.import_module(
                'IonInspector.reports.diagnostics.' + self.name.replace(' ', '_') + '.main')
            if settings.DEBUG:
                reload(diagnostic_module)
            diagnostic_results = diagnostic_module.execute(self.archive.archive_root, self.diagnostic_root,
                                                           self.archive.archive_type)
            assert not isinstance(diagnostic_results, type(None)), "Diagnostic is broken (Returned None)"
            self.status, self.priority, self.details = diagnostic_results

            html_path = os.path.join(self.diagnostic_root, "results.html")
            if os.path.exists(html_path):
                self.html = os.path.basename(html_path)

        except Exception as exc:
            self.details = str(exc)
            # record the exception in the details and rely on the finally statement to call save
            write_error_html(self.diagnostic_root)
            self.status = Diagnostic.FAILED

        # constrain the length of the details to 140 (one tweet)
        self.details = self.details[:140]
        self.save()


@receiver(pre_delete, sender=Diagnostic, dispatch_uid="delete_diagnostic")
def on_diagnostic_delete(sender, instance, **kwargs):
    """Triggered when the diagnostic are deleted"""
    if os.path.exists(instance.diagnostic_root):
        shutil.rmtree(instance.diagnostic_root)
