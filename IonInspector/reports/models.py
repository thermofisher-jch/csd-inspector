"""
This will hold all of the data models for the inspector.
"""
import contextlib
import lzma
import shutil
import tarfile
import zipfile
import os
from subprocess import *

from cached_property import cached_property
from celery.contrib.methods import task
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone

from lemontest.diagnostics.common.inspector_utils import *
from reports.utils import check_for_dx_zip, force_symlink

# check to see if the settings are configured
if not settings.configured:
    settings.configure()

# define constants
PGM_RUN = "PGM_Run"
PROTON = "Proton"
RAPTOR_S5 = "Raptor_S5"
OT_LOG = "OT_Log"
ION_CHEF = "Ion_Chef"

DIAGNOSTICS_SCRIPT_DIR = '/opt/inspector/lemontest/diagnostics'
TEST_MANIFEST = {
  PGM_RUN: [
    "Filter_Metrics",
    "Raw_Trace",
    "Run_Details",
    "Chip_Temperature",
    "Chip_Status",
    "Auto_pH",
    "Sequencing_Details",
    "Chip_Type",
    "Test_Fragments",
    "Pressure_And_Temperature",
    "Experiment_Errors",
    "Barcode_Report"
  ],
  PROTON: [
    "Filter_Metrics",
    "Raw_Trace",
    "Run_Details",
    "Chip_Status",
    "Auto_pH",
    "Flow_Error",
    "Sequencing_Details",
    "Chip_Type",
    "Test_Fragments",
    "Pressure_And_Temperature",
    "Experiment_Errors",
    "Barcode_Report"
  ],
  RAPTOR_S5: [
    "Filter_Metrics",
    "Raw_Trace",
    "Chip_Status",
    "Run_Details",
    "Flow_Error",
    "S5_Reagents",
    "Sequencing_Details",
    "Chip_Type",
    "Test_Fragments",
    "Pressure_And_Temperature",
    "Experiment_Errors",
    "Barcode_Report"
  ],
  OT_LOG: [
    "Plots",
    "Sample_Pump",
    "Oil_Pump",
    "OT_Script"
  ],
  ION_CHEF: [
    "Alarms",
    "Notifications",
    "Kit_Details",
    "Chef_Timer",
    "Chef_Version",
    # "Flow", Now plotted by Chef_Run_Log
    "Chef_Run_Details",
    # "Fans", Now plotted by Chef_Run_Log
    "Chef_Run_Log",
    "Integrity_Check"
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
        (RAPTOR_S5, 'RAPTOR'),
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
    archive_type = models.CharField(max_length=255, choices=ARCHIVE_TYPES)

    # any summary information
    summary = models.CharField(max_length=255, default=u"")

    # an optional taser ticket reference
    taser_ticket_number = models.IntegerField(null=True)

    # use the get_file_path method to direct the file field on where to store the zip file
    doc_file = models.FileField(upload_to=get_file_path, blank=True, null=True, max_length=1000)

    # model relationships
    # diagnostics : Foreign Key from diagnostic class
    # tags : Foreign Key from tag class

    def execute_diagnostics(self, async=True):
        """this method will execute all of the diagnostics"""

        def get_immediate_subdirectories(a_dir):
            return

        # if the file is not there then there is nothing we can do
        if not os.path.exists(self.doc_file.path):
            raise Exception("The archive file is not present at: " + self.doc_file.path)

        archive_dir = os.path.dirname(self.doc_file.path)
        if self.doc_file.path.endswith('.zip'):
            if check_for_dx_zip(self.doc_file.path):
                raise Exception("This is a Dx package which is not allowed to be submitted in inspector.")
            doc_archive = zipfile.ZipFile(self.doc_file.path)
            doc_archive.extractall(path=archive_dir)
        # Watch out. Some chef archives are .tar but are really .tar.gz
        elif self.doc_file.path.endswith('.tar') or self.doc_file.path.endswith('.tar.gz'):
            tar = tarfile.open(self.doc_file.path, "r")
            tar.extractall(path=archive_dir)
            tar.close()
        # Python 2.7 requires the use of lzma for tar.xz
        elif self.doc_file.path.endswith('.tar.xz'):
            with contextlib.closing(lzma.LZMAFile(self.doc_file.path)) as xz:
                tar = tarfile.open(fileobj=xz)
                tar.extractall(path=archive_dir)
                tar.close()
        # Watch out. Some ot logs are are .log and some are .csv
        elif self.doc_file.path.endswith('.log') or self.doc_file.path.endswith('.csv'):  # One Touch
            target_path = os.path.join(archive_dir, "onetouch.log")
            if not os.path.exists(target_path):
                shutil.copy(self.doc_file.path, target_path)

        # handle coverage analysis specific workarounds here
        coverage_analysis_path = os.path.join(archive_dir, 'coverageAnalysis')
        if os.path.exists(coverage_analysis_path):
            # we are assuming any subdirectories here will be barcoded subdirectories since the pattern when creating the CSA only specifies content which is indicative of a barcode
            for subdir in [name for name in os.listdir(coverage_analysis_path) if os.path.isdir(os.path.join(coverage_analysis_path, name))]:
                force_symlink(os.path.join(settings.STATICFILES_DIRS[0], 'coverageAnalysis', 'flot'), os.path.join(coverage_analysis_path, subdir, 'flot'))
                force_symlink(os.path.join(settings.STATICFILES_DIRS[0], 'coverageAnalysis', 'lifechart'), os.path.join(coverage_analysis_path, subdir, 'lifechart'))

        # delete all other diagnostics first
        tests = Diagnostic.objects.filter(archive=self)
        for run_test in tests:
            run_test.delete()

        # get all of the diagnostics to be run on this type of archive
        diagnostic_list = TEST_MANIFEST[str(self.archive_type)]
        for diagnostic_name in diagnostic_list:
            diagnostic = Diagnostic(name=diagnostic_name, archive=self)
            readme_file = os.path.join(settings.SITE_ROOT, 'lemontest', 'diagnostics', diagnostic_name, 'README')
            if os.path.exists(readme_file):
                diagnostic.readme = os.path.basename(readme_file)
            diagnostic.save()
            if async:
                diagnostic.execute.delay()
            else:
                diagnostic.execute.apply()

    @cached_property
    def archive_root(self):
        """The archive root path"""
        return os.path.dirname(self.doc_file.path)


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

    # model relationships
    archive = models.ForeignKey(Archive, related_name="diagnostics", on_delete=models.CASCADE)

    @cached_property
    def display_name(self):
        return self.name.replace("_", " ").title()

    @cached_property
    def diagnostic_root(self):
        """returns the root of the files used in the diagnostic"""
        test_folder = os.path.join(self.archive.archive_root, 'test_results')
        if not os.path.exists(test_folder):
            os.mkdir(test_folder)

        os.chmod(test_folder, 0777)

        results_folder = os.path.join(test_folder, self.name)
        if not os.path.exists(results_folder):
            os.mkdir(results_folder)
        return results_folder

    @cached_property
    def readme(self):
        return os.path.exists(os.path.join(settings.SITE_ROOT, 'lemontest', 'diagnostics', self.name, 'README'))

    @task()
    def execute(self):
        """This will execute the this diagnostic"""

        try:
            # set the status
            self.status = self.EXECUTING
            self.start_execute = timezone.now()
            self.save()

            # find the executable to use
            script_folder = os.path.join(DIAGNOSTICS_SCRIPT_DIR, self.name)
            script = os.path.join(script_folder, 'main.py')

            # execute the script
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.join('/', 'opt', 'inspector')
            env['DJANGO_SETTINGS_MODULE'] = 'IonInspector.settings'
            cmd = [script, self.archive.archive_root, self.diagnostic_root, self.archive.archive_type]
            test_process = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=script_folder, env=env)
            stdout, self.error = test_process.communicate()

            # deal with the output
            open(os.path.join(self.diagnostic_root, "standard_output.log"), 'wb').write(stdout)
            open(os.path.join(self.diagnostic_root, "standard_error.log"), 'wb').write(self.error)
            output = stdout.splitlines()
            self.priority = 0
            self.status = Diagnostic.FAILED
            if stdout:
                for short_name, long_name in Diagnostic.DIAGNOSTIC_STATUSES:
                    if output[0] == long_name:
                        self.status = long_name
                self.priority = int(output[1])

            self.details = self.error if self.error else "<br />".join(output[2:]).rstrip()
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


class Tag(models.Model):
    """A tag for an archive"""

    # model attributes
    name = models.CharField(max_length=255)

    # model relationships
    archive = models.ForeignKey(Archive, related_name="tags")
