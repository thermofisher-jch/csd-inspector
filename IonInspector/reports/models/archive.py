import os
import shutil
import logging
import zipfile
from subprocess import check_call, CalledProcessError

from cached_property import cached_property
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F, CharField, Value, ExpressionWrapper
from django.db.models.functions import Concat
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse

from IonInspector.celeryconfig import celery_app
from IonInspector.reports.diagnostics.common.inspector_utils import (
    read_explog,
    get_platform_and_systemtype,
)
from IonInspector.reports.utils import (
    force_symlink,
    is_likely_tar_file,
    ensure_all_diagnostics_namespace,
    ArchiveWorkspaceError,
)
from reports.utils import get_file_path
from IonInspector.reports.values import (
    ARCHIVE_TYPES,
    CATEGORY_LIBRARY_PREP,
    CATEGORY_SEQUENCING,
    CATEGORY_SAMPLE_PREP,
    PGM_RUN,
    PROTON,
    PURE,
    S5,
    OT_LOG,
    ION_CHEF,
    VALK,
    UNKNOWN_PLATFORM,
    TRI_STATE_SYMBOL_SELECT,
    RUN_REPORT_PDF,
    WELL_KNOWN_ARCHIVE,
    NOT_RUN_REPORT_LINK_TARGETS,
)
from IonInspector.reports.tags.chef import get_chef_tags
from IonInspector.reports.tags.pgm import get_pgm_tags
from IonInspector.reports.tags.proton import get_proton_tags
from IonInspector.reports.tags.purification import get_pure_tags
from IonInspector.reports.tags.s5 import get_s5_tags
from IonInspector.reports.tags.ot import get_ot_tags
from IonInspector.reports.tags.valkyrie import get_valk_tags

from .diagnostic import Diagnostic

# check to see if the settings are configured
if not settings.configured:
    settings.configure()

logger = logging.getLogger(__name__)

DIAGNOSTICS_SCRIPT_DIR = "/opt/inspector/IonInspector/reports/diagnostics"
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
        ("Run_Sequence_Details", CATEGORY_SEQUENCING),
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
        ("Run_Sequence_Details", CATEGORY_SEQUENCING),
    ],
    PURE: [
        ("Purification_Quant_Summary", CATEGORY_SAMPLE_PREP),
        ("Purification_Run_Log", CATEGORY_SAMPLE_PREP),
        ("Purification_Logged_Errors", CATEGORY_SAMPLE_PREP),
        # ("Genexus_Library_Prep_Log", CATEGORY_LIBRARY_PREP),
        # ("Genexus_Library_Details", CATEGORY_LIBRARY_PREP),
        # ("Genexus_Vacuum_Log", CATEGORY_LIBRARY_PREP),
        # ("Genexus_Reagent_Lot_Summary", CATEGORY_SEQUENCING),
        # ("Genexus_QC_Status", CATEGORY_SEQUENCING),
        # ("Genexus_Raw_Trace", CATEGORY_SEQUENCING),
        # ("Genexus_Instrument_Status", CATEGORY_SEQUENCING),
        # ("Genexus_Filter_Metrics", CATEGORY_SEQUENCING),
        # ("Chip_Status", CATEGORY_SEQUENCING),
        # ("Chip_Type", CATEGORY_SEQUENCING),
        # ("Genexus_Test_Fragments", CATEGORY_SEQUENCING),
        # # ("Pressure_And_Temperature", CATEGORY_SEQUENCING), #IO-413
        # ("Barcode_Report", CATEGORY_SEQUENCING),
        # ("Run_Sequence_Details", CATEGORY_SEQUENCING),
        # ("Run_Type", CATEGORY_SEQUENCING),
        # ("Genexus_Reagent_Lot_Summary", CATEGORY_SEQUENCING),
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
        ("Run_Sequence_Details", CATEGORY_SEQUENCING),
    ],
    VALK: [
        ("Genexus_Vacuum_Log", CATEGORY_LIBRARY_PREP),
        ("Genexus_Library_Prep_Log", CATEGORY_LIBRARY_PREP),
        ("Genexus_Library_Details", CATEGORY_LIBRARY_PREP),
        ("Purification_Quant_Summary", CATEGORY_SAMPLE_PREP),
        ("Purification_Run_Log", CATEGORY_SAMPLE_PREP),
        ("Purification_Logged_Errors", CATEGORY_SAMPLE_PREP),
        ("Genexus_QC_Status", CATEGORY_SEQUENCING),
        ("Genexus_Raw_Trace", CATEGORY_SEQUENCING),
        ("Genexus_Instrument_Status", CATEGORY_SEQUENCING),
        ("Genexus_Filter_Metrics", CATEGORY_SEQUENCING),
        ("Genexus_Lane_Activity", CATEGORY_SEQUENCING),
        ("Chip_Status", CATEGORY_SEQUENCING),
        ("Chip_Type", CATEGORY_SEQUENCING),
        ("Genexus_Test_Fragments", CATEGORY_SEQUENCING),
        # ("Pressure_And_Temperature", CATEGORY_SEQUENCING), #IO-413
        ("Experiment_Errors", CATEGORY_SEQUENCING),
        ("Barcode_Report", CATEGORY_SEQUENCING),
        ("Run_Sequence_Details", CATEGORY_SEQUENCING),
        ("Run_Type", CATEGORY_SEQUENCING),
        ("Genexus_Reagent_Lot_Summary", CATEGORY_SEQUENCING),
        ("Genexus_TroubleShooter", CATEGORY_SEQUENCING),
    ],
    OT_LOG: [
        ("OT_Plots", CATEGORY_SAMPLE_PREP),
        ("Sample_Pump", CATEGORY_SAMPLE_PREP),
        ("Oil_Pump", CATEGORY_SAMPLE_PREP),
        ("OT_Script", CATEGORY_SAMPLE_PREP),
        ("Flowmeter", CATEGORY_SAMPLE_PREP),
    ],
    ION_CHEF: [
        ("Chef_Flexible_Workflow", CATEGORY_SAMPLE_PREP),
        ("Chef_Notifications", CATEGORY_SAMPLE_PREP),
        ("Chef_Kit_Details", CATEGORY_SAMPLE_PREP),
        ("Chef_Timer", CATEGORY_SAMPLE_PREP),
        ("Chef_Version", CATEGORY_SAMPLE_PREP),
        ("Chef_Run_Details", CATEGORY_SAMPLE_PREP),
        ("Chef_Run_Log", CATEGORY_SAMPLE_PREP),
        ("Integrity_Check", CATEGORY_SAMPLE_PREP),
    ],
}


class ArchiveQuerySet(models.QuerySet):
    def with_serial_number(self):
        return self.annotate(
            serial_number=ExpressionWrapper(
                F("as_valkyrie__instrument__serial_number"),
                output_field=CharField(max_length=255),
            )
        )

    def with_taser_ticket_url(self):
        return self.annotate(
            taser_ticket_url=ExpressionWrapper(
                Concat(
                    Value("https://jira.amer.thermo.com/browse/FST-"),
                    F("taser_ticket_number"),
                ),
                output_field=CharField(max_length=255),
            )
        )


class ArchiveManager(models.Manager.from_queryset(ArchiveQuerySet)):
    pass
    # def get_queryset(self):
    #     return ArchiveQuerySet(model=self.model, using=self._db, hints=self._hints)
    #
    # def with_serial_number(self):
    #     return self.get_queryset().with_serial_number()
    #
    # def with_taser_ticket_url(self):
    #     return self.get_queryset().with_taser_ticket_url()


class Archive(models.Model):
    """An archive sample"""

    objects = ArchiveManager()

    # user-provided label on upload
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
    failure_mode = models.TextField(unique=False, default=u"", blank=False, null=True)

    # Three-stage flag for categorizing a case as known good, known issue, or not yet known.
    is_known_good = models.CharField(
        max_length=4, unique=False, choices=TRI_STATE_SYMBOL_SELECT, null=False
    )

    # an optional taser ticket reference
    taser_ticket_number = models.IntegerField(null=True)

    # use the get_file_path method to direct the file field on where to store the zip file
    doc_file = models.FileField(
        upload_to=get_file_path, blank=True, null=True, max_length=1000
    )

    sha1_hash = models.CharField(
        max_length=27, unique=False, null=True, blank=False, db_index=False
    )
    md5_hash = models.CharField(
        max_length=22, unique=False, null=True, blank=False, db_index=False
    )
    crc32_sum = models.CharField(
        max_length=6, unique=False, null=True, blank=False, db_index=False
    )

    # used to search the runs for tags
    search_tags = ArrayField(
        models.CharField(max_length=255),
        default=list,
        db_index=True,
        unique=False,
        null=False,
    )

    # model relationships
    # diagnostics : Foreign Key from diagnostic class

    def detect_archive_type(self):
        """This will attempt to auto detect the archive type"""

        # if the base archive is a simple log or csv then this is a one touch
        if self.doc_file.path.endswith(".log") or self.doc_file.path.endswith(".csv"):
            archive_dir = os.path.dirname(self.doc_file.path)
            target_path = os.path.join(archive_dir, "onetouch.log")
            if not os.path.exists(target_path):
                shutil.copy(self.doc_file.path, target_path)
            return OT_LOG

        # everything else needs the archive to be extracted
        archive_dir = os.path.dirname(self.doc_file.path)
        self.extract_archive()

        try:
            explog = read_explog(archive_dir)
            platform, _ = get_platform_and_systemtype(explog)

            # do not return when it is undetermined.
            # unknown platform is considered as error condition
            if platform != UNKNOWN_PLATFORM:
                return platform

        except Exception as e:
            logger.exception(e)

        # if the extracted files has a var directory then this is a ion chef
        if os.path.exists(os.path.join(archive_dir, "var")):
            return ION_CHEF

        # if we have gotten to this point then we really have no idea what kind of archive this is and this
        # should be considered an error condition
        raise Exception("Cannot determine the archive type.")

    def extract_archive(self):
        """
        Extract all content from archive to the root archive folder, which also same folder holding
        archive file.  If archive's contents are all nested within a single subdirectory, pull all
        that content up to its parent, the root archive folder and eliminate the nested
        subdirectory.
        """
        # if the file is not there then there is nothing we can do
        if not os.path.exists(self.doc_file.path):
            raise ArchiveWorkspaceError(
                "The archive file is not present at: " + self.doc_file.path
            )

        well_known_archive = os.path.join(self.archive_root, WELL_KNOWN_ARCHIVE)
        if not os.path.exists(well_known_archive):
            next_archive = self.doc_file.path
            last_archive = next_archive
            previous_archives = set()
            while next_archive is not None and len(previous_archives) < 5:
                if next_archive.endswith(".zip"):
                    self.extract_zip_fallback_tar(next_archive)
                elif is_likely_tar_file(self.doc_file.path):
                    self.extract_tar_fallback_zip(next_archive)
                self.attempt_root_directory_uplift(next_archive)
                last_archive = next_archive
                next_archive = self.check_for_nested_packing(
                    next_archive, previous_archives
                )
            if next_archive is not None:
                logger.error(
                    "{} contains more than 5 layers of nested archives".format(
                        self.doc_file.path
                    )
                )
            self.cleanup_intermediate_archives(last_archive, previous_archives)
        self.check_for_run_report()

    def cleanup_intermediate_archives(self, last_archive, previous_archives):
        # Clean up intermediate archives, if any, for space efficiency
        previous_archives.discard(os.path.basename(self.doc_file.path))
        if last_archive is not None:
            previous_archives.discard(last_archive)
            try:
                force_symlink(
                    last_archive, os.path.join(self.archive_root, WELL_KNOWN_ARCHIVE)
                )
            except OSError as exp:
                # Don't fail archive import just because we failed to link
                # its nested archive.
                logger.exception(
                    "Nested archive {} unpacked, but failed to symlink for later ".format(
                        last_archive
                    ),
                    exc_info=exp,
                )
        for temp_archive in previous_archives:
            os.remove(os.path.join(self.archive_root, temp_archive))

    def attempt_zip_extraction(self, file_path):
        with zipfile.ZipFile(file_path) as doc_archive:
            doc_archive.extractall(path=self.archive_root)
            doc_archive.close()

    def attempt_tar_extraction(self, file_path):
        # Some chef archives contains files with no read permission. This seems to kill the
        # python tar library.  So instead we are using a subprocess to extract then chmod
        check_call(["tar", "-xf", file_path, "--directory", self.archive_root])
        check_call(
            [
                "chmod",
                "-R",
                "u=r,u+w,u-x,g=r,g+w,g-x,g+s,o+r,o-w,o-x,a+X",
                self.archive_root,
            ]
        )

    def attempt_root_directory_uplift(self, file_path):
        base_filename = os.path.basename(file_path)
        file_root = os.path.splitext(base_filename)
        while file_root[1] > "":
            file_root = os.path.splitext(file_root[0])
        full_candidate = os.path.join(self.archive_root, file_root[0])
        if os.path.isdir(full_candidate):
            for nested_child in os.listdir(full_candidate):
                shutil.move(
                    os.path.join(full_candidate, nested_child),
                    os.path.join(self.archive_root, nested_child),
                )
            os.rmdir(full_candidate)

    def extract_tar_fallback_zip(self, file_path):
        try:
            self.attempt_tar_extraction(file_path)
        except CalledProcessError as err1:
            try:
                self.attempt_zip_extraction(file_path)
            except Exception as err2:
                logger.exception("Initial tar archive unpack error", exc_info=err1)
                logger.exception("Fallback zip archive unpack error", exc_info=err2)
                raise err1

    def extract_zip_fallback_tar(self, file_path):
        try:
            self.attempt_zip_extraction(file_path)
        except Exception as err1:
            try:
                self.attempt_tar_extraction(file_path)
            except CalledProcessError as err2:
                # Log both exceptions, but re-raise the first one as this second one was a
                # last resort attempt.
                logger.exception("Initial zip archive unpack error", exc_info=err1)
                logger.exception("Fallback tar archive unpack error", exc_info=err2)
                raise err1

    def execute_diagnostics(self, async=True, skip_extraction=False):
        """this method will execute all of the diagnostics"""

        if not skip_extraction:
            self.extract_archive()

        self.generate_tags()

    def check_for_run_report(self):
        report_pdf = None
        for child_path in os.listdir(self.archive_root):
            if (
                child_path.endswith(".pdf")
                and child_path not in NOT_RUN_REPORT_LINK_TARGETS
            ):
                if report_pdf is None:
                    report_pdf = os.path.join(self.archive_root, child_path)
                else:
                    logger.warning(
                        "{} contains too many PDFs to identify a run report".format(
                            self.doc_file.path
                        )
                    )
                    report_pdf = None
                    break
        if report_pdf is not None:
            logger.info(self.doc_file.path + " contained a run report PDF to symlink")
            try:
                force_symlink(
                    report_pdf, os.path.join(self.archive_root, RUN_REPORT_PDF)
                )
            except OSError as exp:
                # Don't fail archive import just because we failed to link
                # its report PDF.
                logger.warning(
                    "Failed to symlink report PDF {} at well-known path".format(
                        report_pdf
                    )
                )

    def check_for_nested_packing(self, file_path, previous_archives):
        """Check whether we unpacked fewer than 6 files.  If so, look for another nested archive
        file and a run report PDF file.  If found, this is a Genexus 6.6 archive with
        RunReport PDF and a nested pre-6.6 format CSA archive.  In that case, we must also
        unpack the nested archive to achieve an end state consistent with earlier versions
        and we symlink the run report with a well defined name for easier access by reports."""
        chef_marker = os.path.join(self.archive_root, "var")
        csa_marker = os.path.join(self.archive_root, "CSA")
        if os.path.isdir(chef_marker) or os.path.isdir(csa_marker):
            return None
        nested_archive = None
        previous_archives.add(os.path.basename(file_path))
        for child_path in os.listdir(self.archive_root):
            if is_likely_tar_file(child_path) and child_path not in previous_archives:
                if nested_archive is None:
                    nested_archive = os.path.join(self.archive_root, child_path)
                else:
                    logger.error(
                        "{} contained too many nested archives to proceed unambiguously".format(
                            file_path
                        )
                    )
                    nested_archive = None
                    break
        return nested_archive

    def execute_diagnostics(self, async=True, skip_extraction=False):
        """this method will execute all of the diagnostics"""

        if not skip_extraction:
            self.extract_archive()

        self.generate_tags()

        # handle coverage analysis specific workarounds here
        archive_dir = os.path.dirname(self.doc_file.path)
        coverage_analysis_path = os.path.join(archive_dir, "coverageAnalysis")
        if os.path.exists(coverage_analysis_path):
            # we are assuming any subdirectories here will be barcoded subdirectories since the pattern when creating the CSA only specifies content which is indicative of a barcode
            for subdir in [
                name
                for name in os.listdir(coverage_analysis_path)
                if os.path.isdir(os.path.join(coverage_analysis_path, name))
            ]:
                force_symlink(
                    os.path.join(
                        settings.STATICFILES_DIRS[0], "coverageAnalysis", "flot"
                    ),
                    os.path.join(coverage_analysis_path, subdir, "flot"),
                )
                force_symlink(
                    os.path.join(
                        settings.STATICFILES_DIRS[0], "coverageAnalysis", "lifechart"
                    ),
                    os.path.join(coverage_analysis_path, subdir, "lifechart"),
                )

        # delete all other diagnostics first
        # tests = Diagnostic.objects.filter(archive=self)
        # for run_test in tests:
        #     run_test.delete()
        Diagnostic.objects.filter(archive=self).delete()

        # get all of the diagnostics to be run on this type of archive
        archive_type = str(self.archive_type)
        diagnostic_list = TEST_MANIFEST[archive_type][:]

        # if this is a sequencer CSA/FSA with chef information it would
        # make sense to optionally add all of the chef tests
        if archive_type in [S5, PGM_RUN, PROTON] and os.path.exists(
            os.path.join(archive_dir, "var")
        ):
            diagnostic_list += TEST_MANIFEST[ION_CHEF]

        # make tests folder
        test_folder = ensure_all_diagnostics_namespace(self.archive_root)

        for diagnostic_name, diagnostic_category in diagnostic_list:
            diagnostic = Diagnostic(
                name=diagnostic_name, archive=self, category=diagnostic_category
            )
            diagnostic.save()
            if async:
                celery_app.send_task(
                    "reports.tasks.execute_diagnostic", (diagnostic.id,)
                )
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
        elif self.archive_type == VALK:
            search_tags = get_valk_tags(self.archive_root)
        elif self.archive_type == PURE:
            search_tags = get_pure_tags(self.archive_root)
        else:
            search_tags = []
        self.search_tags = sorted(list(set([tag.strip() for tag in search_tags])))
        self.save()

    @cached_property
    def archive_root(self):
        """The archive root path"""
        return os.path.dirname(self.doc_file.path)

    def is_sequencer(self):
        return self.archive_type in [S5, PROTON, PGM_RUN, VALK]

    class Meta:
        app_label = "reports"

    def get_absolute_url(self):
        return reverse("report", args=[self.id])


# TODO: Receivers should not be imported from a model file as this can
#       lead to them registering for the same events multiple times.
@receiver(pre_delete, sender=Archive, dispatch_uid="delete_archive")
def on_archive_delete(sender, instance, **kwargs):
    """Triggered when the archives are deleted"""

    archive_root = os.path.join(settings.MEDIA_ROOT, "archive_files", str(instance.pk))
    try:
        shutil.rmtree(archive_root)
    except:
        # do nothing here as this is just a clean up
        pass
