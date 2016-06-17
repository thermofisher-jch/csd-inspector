"""
This will hold all of the data models for the inspector.
"""
from cached_property import cached_property
from django.conf import settings
from django.db import models
from celery.contrib.methods import task
from subprocess import *
import zipfile
import os

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
    "Version_Check",
    "ISP_Loading",
    "Chip_Temperature",
    "PGM_Temperature",
    "PGM_Pressure",
    "Chip_Status",
    "Auto_pH",
    "Sequencing_Details",
    "Chip_Type"
  ],
  PROTON: [
    "Filter_Metrics",
    "Raw_Trace",
    "Version_Check",
    "ISP_Loading",
    "Chip_Status",
    "Proton_Pressure",
    "Auto_pH",
    "Flow",
    "Sequencing_Details",
    "Chip_Type"
  ],
  RAPTOR_S5: [
    "Filter_Metrics",
    "Raw_Trace",
    "Version_Check",
    "ISP_Loading",
    "Chip_Status",
    "S5_Pressure",
    "Version_Check",
    "Raw_Trace",
    "Flow",
    "Ion_S5_Reagent_Lots",
    "Sequencing_Details",
    "Chip_Type"
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
    "Chef_Kit",
    "Chef_Chip",
    "Chef_Timer",
    "Chef_Version",
    "Flow",
    "Run_Type",
    "Fans"
  ]
}


def get_file_path(instance, filename):
    """
    Used for determining a path for the file to be saved to
    :param instance: This archive instance
    :param filename: The name of the file to be saved
    :return: The path to save the archive file to
    """

    return os.path.join('archive_files', str(instance.pk), filename)


class Archive(models.Model):
    """
    An archive sample
    """

    # define a list of archive types
    ARCHIVE_TYPES = (
        ('PGM', PGM_RUN),
        ('PROTON', PROTON),
        ('RAPTOR', RAPTOR_S5),
        ('OT', OT_LOG),
        ('CHEF', ION_CHEF)
    )

    # model attributes
    label = models.CharField(max_length=255)
    site = models.CharField(max_length=255)
    time = models.DateTimeField()
    submitter_name = models.CharField(max_length=255)
    archive_type = models.CharField(max_length=255, choices=ARCHIVE_TYPES)
    summary = models.CharField(max_length=255, default=u"")

    # use the get_file_path method to direct the file field on where to store the zip file
    doc_file = models.FileField(upload_to=get_file_path)

    # model relationships
    # diagnostics : Foreign Key from diagnostic class
    # tags : Foreign Key from tag class

    def execute_diagnostics(self):
        """
        this method will execute all of the diagnostics
        """

        # if the file is not there then there is nothing we can do
        if not os.path.exists(self.doc_file.path):
            raise Exception("The archive file is not present at: " + self.doc_file.path)

        doc_folder = os.path.dirname(self.doc_file.path)
        doc_archive = zipfile.ZipFile(self.doc_file.path)
        doc_archive.extractall(path=doc_folder)

        # get all of the diagnostics to be run on this type of archive
        diagnostic_list = TEST_MANIFEST[self.archive_type]
        for diagnostic_name in diagnostic_list:
            diagnostic = Diagnostic(name=diagnostic_name, archive=self)
            readme_file = os.path.join(settings.SITE_ROOT, 'lemontest', 'diagnostics', diagnostic_name, 'README')
            if os.path.exists(readme_file):
                diagnostic.readme = os.path.basename(readme_file)
            diagnostic.save()
            diagnostic.execute()


class Diagnostic(models.Model):
    """
    A test to run against an archive
    """

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

    # model attributes
    name = models.CharField(max_length=255, default="")
    status = models.CharField(max_length=255, choices=DIAGNOSTIC_STATUSES, default=UNEXECUTED)
    details = models.CharField(max_length=2048, default="")
    error = models.CharField(max_length=2048, default="")
    html = models.CharField(max_length=255, default="")
    priority = models.IntegerField(default=0)

    # model relationships
    archive = models.ForeignKey(Archive, related_name="diagnostics", on_delete=models.CASCADE)

    @cached_property
    def readme(self):
        return os.path.exists(os.path.join(settings.SITE_ROOT, 'lemontest', 'diagnostics', self.name, 'README'))

    @task()
    def execute(self):
        """
        This will execute the this diagnostic
        """

        try:
            # set the status
            self.status = self.EXECUTING
            self.save()

            # fire off the diagnostic executable
            # create results directory
            archive_folder = os.path.dirname(self.archive.doc_file.path)
            test_folder = os.path.join(archive_folder, 'test_results')
            if not os.path.exists(test_folder):
                os.mkdir(test_folder)
            results_folder = os.path.join(test_folder, self.name)
            if not os.path.exists(results_folder):
                os.mkdir(results_folder)

            # find the executable to use
            script_folder = os.path.join(DIAGNOSTICS_SCRIPT_DIR, self.name)
            script = os.path.join(script_folder, 'main.py')
            if not os.path.exists(script):
                script = os.path.join(script_folder, 'main.sh')

            # execute the script
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.join('/', 'opt', 'inspector')
            cmd = [script, archive_folder, results_folder, self.archive.archive_type]
            test_process = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=script_folder, env=env)
            stdout, self.error = test_process.communicate()

            # deal with the output
            open(os.path.join(results_folder, "standard_output.log"), 'wb').write(stdout)
            open(os.path.join(results_folder, "standard_error.log"), 'wb').write(self.error)
            output = stdout.splitlines()
            self.priority = 0
            self.status = Diagnostic.FAILED
            if stdout:
                for short_name, long_name in Diagnostic.DIAGNOSTIC_STATUSES:
                    if output[0] == long_name:
                        self.status = long_name
                self.priority = int(output[1])

            self.details = self.error if self.error else u"<br />".join(output[2:]).rstrip()
            html_path = os.path.join(results_folder, "results.html")
            if os.path.exists(html_path):
                self.html = os.path.basename(html_path)

        except Exception as exc:
            # record the exception in the details and rely on the finally statement to call save
            self.details = str(exc)
            self.status = Diagnostic.FAILED

        self.save()


class Tag(models.Model):
    """
    A tag for an archive
    """

    # model attributes
    name = models.CharField(max_length=255)

    # model relationships
    archive = models.ForeignKey(Archive, related_name="tags")
