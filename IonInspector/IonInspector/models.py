"""
This will hold all of the data models for the inspector.
"""
from django.conf import settings
from django.db import models
from IonInspector.inspector_celery import app
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

TEST_MANIFEST = {
  PGM_RUN: [
    "Filter_Metrics",
    "Raw_Trace",
    "Version_Check",
    "ISP_Loading",
    "Chip_Temperature",
    "PGM_Temperature",
    "PGM_Pressure",
    "Chip_Noise",
    "Chip_Gain",
    "Auto_pH",
    "Seq_Kit",
    "Reference_Electrode",
    "Templating_Kit",
    "Sequencing_Kit",
    "Chip_Type"
  ],
  PROTON: [
    "Filter_Metrics",
    "Raw_Trace",
    "Version_Check",
    "ISP_Loading",
    "Chip_Noise",
    "Chip_Gain",
    "Proton_Pressure",
    "Auto_pH",
    "Seq_Kit",
    "Flow",
    "Templating_Kit",
    "Sequencing_Kit",
    "Chip_Type"
  ],
  RAPTOR_S5: [
    "Filter_Metrics",
    "Raw_Trace",
    "Version_Check",
    "ISP_Loading",
    "Chip_Noise",
    "Chip_Gain",
    "Seq_Kit",
    "S5_Pressure",
    "Version_Check",
    "Raw_Trace",
    "Flow",
    "Ion_S5_Reagent_Lots",
    "Templating_Kit",
    "Sequencing_Kit",
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


@app.task()
def dummy():
    return "I've got no strings to hold me down!"


@app.task()
def execute(diagnostic):
    """
    This will execute a diagnostic on an archive
    """

    try:
        # set the status
        diagnostic.status = Diagnostic.EXECUTING
        diagnostic.save()

        # do the process here...

    except Exception as exc:
        # record the exception in the details and rely on the finally statement to call save
        diagnostic.details = str(exc)

    finally:
        # attempt to set the status to completed no matter the issue
        try:
            diagnostic.status = Diagnostic.COMPLETED
            diagnostic.save()
        except:
            # swallow up any exceptions here
            pass

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
            diagnostic.save()
            execute.delay(diagnostic)


class Diagnostic(models.Model):
    """
    A test to run against an archive
    """

    UNEXECUTED = "Unexecuted"
    EXECUTING = "Executing"
    COMPLETED = "Completed"

    DIAGNOSTIC_STATUSES = (
        ('U', UNEXECUTED),
        ('E', EXECUTING),
        ('C', COMPLETED)
    )

    # model attributes
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=255, choices=DIAGNOSTIC_STATUSES, default=UNEXECUTED)
    details = models.CharField(max_length=2048)
    error = models.CharField(max_length=2048)
    html = models.CharField(max_length=255)

    # model relationships
    archive = models.ForeignKey(Archive, related_name="diagnostics", on_delete=models.CASCADE)


class Tag(models.Model):
    """
    A tag for an archive
    """

    # model attributes
    name = models.CharField(max_length=255)

    # model relationships
    archive = models.ForeignKey(Archive, related_name="tags")
