from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from reports.models import Archive
from reports.models import PGM_RUN, PROTON, S5, OT_LOG, ION_CHEF  # Constants
from reports.models import Diagnostic
import os
import shutil

DIAGNOSTIC_FAILURE_STATUSES = [
    Diagnostic.EXECUTING,
    Diagnostic.UNEXECUTED,
    Diagnostic.FAILED
]


def get_test_archive(name):
    path = os.path.join("/opt/inspector/.local/test_archives/", name)
    if not os.path.exists(path):
        raise ValueError("Could not find test archive '%s'! "
                         "Place the test archives in a .local/test_data/ directory in the repo root." % name)
    return SimpleUploadedFile(name, open(path, 'rb').read())


def get_diagnostic_debug_info(diagnostic):
    results_path = os.path.join(diagnostic.diagnostic_root, "results.html")
    return "\n".join([
        "'%s' failed with status: %s" % (diagnostic.display_name, diagnostic.get_status_display()),
        "- directory " + diagnostic.diagnostic_root,
        "- stdout below\n" + open(os.path.join(diagnostic.diagnostic_root, "standard_output.log")).read(),
        "- stderr below\n" + open(os.path.join(diagnostic.diagnostic_root, "standard_error.log")).read(),
        "- results.html below\n" + open(results_path).read() if os.path.exists(results_path) else "<No results.html>"
    ])


def delete_archive_root(archive):
    archive_root_path = os.path.join(settings.MEDIA_ROOT, 'archive_files', str(archive.pk))
    if os.path.exists(archive_root_path):
        shutil.rmtree(archive_root_path)


class PGMTestCase(TestCase):
    def setUp(self):
        self.archive_v1_0 = Archive(
            identifier="PGM",
            site="PGM",
            time=timezone.now(),
            submitter_name="PGM",
            archive_type=PGM_RUN,
            taser_ticket_number=None
        )
        self.archive_v1_0.save()
        delete_archive_root(self.archive_v1_0)
        self.archive_v1_0.doc_file = get_test_archive("pgm_1.0.zip")
        self.archive_v1_0.save()

        self.archive_v1_1 = Archive(
            identifier="PGM",
            site="PGM",
            time=timezone.now(),
            submitter_name="PGM",
            archive_type=PGM_RUN,
            taser_ticket_number=None
        )
        self.archive_v1_1.save()
        delete_archive_root(self.archive_v1_1)
        self.archive_v1_1.doc_file = get_test_archive("pgm_1.1.zip")
        self.archive_v1_1.save()

    def test_diagnostics_v1_0(self):
        self.archive_v1_0.execute_diagnostics(async=False)
        for diagnostic in self.archive_v1_0.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic)
            )

    def test_diagnostics_v1_1(self):
        self.archive_v1_1.execute_diagnostics(async=False)
        for diagnostic in self.archive_v1_1.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic)
            )


class ProtonTestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            identifier="PROTON",
            site="PROTON",
            time=timezone.now(),
            submitter_name="PROTON",
            archive_type=PROTON,
            taser_ticket_number=None
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_test_archive("proton.zip")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic)
            )


class S5TestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            identifier="S5",
            site="S5",
            time=timezone.now(),
            submitter_name="S5",
            archive_type=S5,
            taser_ticket_number=None
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_test_archive("s5.zip")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic)
            )


class S5WithChefTestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            identifier="S5withChef",
            site="S5",
            time=timezone.now(),
            submitter_name="S5",
            archive_type=S5,
            taser_ticket_number=None
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_test_archive("s5_with_chef.zip")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic)
            )


class OneTouchTestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            identifier="OT",
            site="OT",
            time=timezone.now(),
            submitter_name="OT",
            archive_type=OT_LOG,
            taser_ticket_number=None
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_test_archive("ot.log")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic)
            )


class ChefTestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            identifier="Chef",
            site="Chef",
            time=timezone.now(),
            submitter_name="Chef",
            archive_type=ION_CHEF,
            taser_ticket_number=None
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_test_archive("chef.tar")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic)
            )


class FieldSupportCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            identifier="FieldSupport",
            site="FieldSupport",
            time=timezone.now(),
            submitter_name="FieldSupport",
            archive_type=S5,
            taser_ticket_number=None
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_test_archive("s5.FieldSupport.tar.xz")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic)
            )
