from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from reports.models import Archive
from reports.utils import PGM_RUN, PROTON, S5, OT_LOG, ION_CHEF  # Constants
from reports.models import Diagnostic
import os
import time
import shutil

DIAGNOSTIC_FAILURE_STATUSES = [
    Diagnostic.EXECUTING,
    Diagnostic.UNEXECUTED,
    Diagnostic.FAILED,
]


def get_archive(name):
    path = os.path.join("/opt/inspector/.local/test_archives/", name)
    if not os.path.exists(path):
        raise ValueError(
            "Could not find test archive '%s'! "
            "Place the test archives in a .local/test_data/ directory in the repo root."
            % name
        )
    return SimpleUploadedFile(name, open(path, "rb").read())


def get_diagnostic_debug_info(diagnostic):
    results_path = os.path.join(diagnostic.diagnostic_root, "results.html")
    return "\n".join(
        [
            "'%s' failed with status: %s"
            % (diagnostic.display_name, diagnostic.get_status_display()),
            "- directory " + diagnostic.diagnostic_root,
            "- results.html below\n" + open(results_path).read()
            if os.path.exists(results_path)
            else "<No results.html>",
        ]
    )


def delete_archive_root(archive):
    archive_root_path = os.path.join(
        settings.MEDIA_ROOT, "archive_files", str(archive.pk)
    )
    try:
        shutil.rmtree(archive_root_path)
    except OSError:
        pass


class PGMTestCase(TestCase):
    def setUp(self):
        self.archive_v1_0 = Archive(
            pk=1,
            identifier="PGM",
            site="PGM",
            time=timezone.now(),
            submitter_name="PGM",
            archive_type=PGM_RUN,
            taser_ticket_number=None,
        )
        self.archive_v1_0.save()
        delete_archive_root(self.archive_v1_0)
        self.archive_v1_0.doc_file = get_archive("pgm_1.0.zip")
        self.archive_v1_0.save()

        self.archive_v1_1 = Archive(
            pk=2,
            identifier="PGM",
            site="PGM",
            time=timezone.now(),
            submitter_name="PGM",
            archive_type=PGM_RUN,
            taser_ticket_number=None,
        )
        self.archive_v1_1.save()
        delete_archive_root(self.archive_v1_1)
        self.archive_v1_1.doc_file = get_archive("pgm_1.1.zip")
        self.archive_v1_1.save()

    def test_diagnostics_v1_0(self):
        self.archive_v1_0.execute_diagnostics(async=False)
        for diagnostic in self.archive_v1_0.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic),
            )
        self.assertEquals(
            self.archive_v1_0.search_tags,
            [
                "314 Chip",
                "PGM Sequencing 200 Kit v2",
                "PGM Template OT2 200 Kit",
                "SN: sn11c010302",
                "TS 5.2.0",
            ],
        )

    def test_diagnostics_v1_1(self):
        self.archive_v1_1.execute_diagnostics(async=False)
        for diagnostic in self.archive_v1_1.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic),
            )


class ProtonTestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            pk=3,
            identifier="PROTON",
            site="PROTON",
            time=timezone.now(),
            submitter_name="PROTON",
            archive_type=PROTON,
            taser_ticket_number=None,
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_archive("proton.zip")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic),
            )

        self.assertEquals(
            self.archive.search_tags,
            [
                "ChefRgt: 1767683",
                "ChefSln: 1767682",
                "P1 Chip",
                "PI Hi-Q Chef Kit",
                "PI Hi-Q Sequencing 200 Kit",
                "ProtonChip: QNS752",
                "SN: 2456487-0795",
                "TS 5.0.5",
            ],
        )


class S5TestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            pk=4,
            identifier="S5",
            site="S5",
            time=timezone.now(),
            submitter_name="S5",
            archive_type=S5,
            taser_ticket_number=None,
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_archive("s5.zip")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic),
            )
        self.assertEquals(
            self.archive.search_tags,
            [
                "520/530 Kit-OT2",
                "530 Chip",
                "S5 Sequencing Kit",
                "S5Chip: QNC284",
                "S5CleanSln: 013315",
                "S5SeqRgt: 013309",
                "S5WashSln: 013405",
                "SN: 245733000432",
                "TS 5.0.4",
            ],
        )


class S5WithChefTestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            pk=5,
            identifier="S5withChef",
            site="S5",
            time=timezone.now(),
            submitter_name="S5",
            archive_type=S5,
            taser_ticket_number=None,
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_archive("s5_with_chef.zip")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic),
            )


class OneTouchTestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            pk=6,
            identifier="OT",
            site="OT",
            time=timezone.now(),
            submitter_name="OT",
            archive_type=OT_LOG,
            taser_ticket_number=None,
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_archive("ot.log")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic),
            )


class ChefTestCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            pk=7,
            identifier="Chef",
            site="Chef",
            time=timezone.now(),
            submitter_name="Chef",
            archive_type=ION_CHEF,
            taser_ticket_number=None,
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_archive("chef.tar")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic),
            )
        self.assertEquals(
            self.archive.search_tags,
            [
                "ChefRgt: 1742721",
                "ChefSln: 1715371",
                "P1v3 Chip",
                "PI Hi-Q Chef Kit",
            ],
        )


class FieldSupportCase(TestCase):
    def setUp(self):
        self.archive = Archive(
            pk=8,
            identifier="FieldSupport",
            site="FieldSupport",
            time=timezone.now(),
            submitter_name="FieldSupport",
            archive_type=S5,
            taser_ticket_number=None,
        )
        self.archive.save()
        delete_archive_root(self.archive)
        self.archive.doc_file = get_archive("s5.FieldSupport.tar.xz")
        self.archive.save()

    def test_diagnostics(self):
        self.archive.execute_diagnostics(async=False)
        for diagnostic in self.archive.diagnostics.all():
            self.assertNotIn(
                diagnostic.get_status_display(),
                DIAGNOSTIC_FAILURE_STATUSES,
                get_diagnostic_debug_info(diagnostic),
            )
