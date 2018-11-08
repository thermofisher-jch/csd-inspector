from django.test import SimpleTestCase
from reports.diagnostics.common.inspector_utils import TemporaryDirectory
from main import get_chip_status, get_total_reads_message


class ChipStatusTestCase(SimpleTestCase):
    def test_get_chip_status_520_on_5_4(self):
        files = {
            "explog.txt":
                """S5 Release_version: 5.4
                ChipType:900
                ChipVersion: 520
                ChipGain:1.087188
                ChipNoise:53.594215
                """,
            "sigproc_results/analysis.bfmask.stats":
                "[global]\n"
                "Total Wells = 960000\n"
                "Bead Wells = 671106\n"
                "Excluded Wells = 0",
            "basecaller_results/ionstats_basecaller.json":
                """{"full":{"num_reads":2232}}""",
        }
        with TemporaryDirectory(files) as archive_path:
            message, report_level, context = get_chip_status(archive_path)
            self.assertEquals(message, "Loading 69.9% | Gain 1.09 | Noise 53.59 | Total Reads: Below Spec")

    def test_get_chip_status_520_on_5_6(self):
        # https://jira.amer.thermo.com/browse/IO-290
        files = {
            "explog.txt":
                """S5 Release_version: 5.6
                ChipType:900
                ChipVersion: 520
                ChipGain:1.087188
                ChipNoise:53.594215
                """,
            "sigproc_results/analysis.bfmask.stats":
                "[global]\n"
                "Total Wells = 960000\n"
                "Bead Wells = 671106\n"
                "Excluded Wells = 0",
            "basecaller_results/ionstats_basecaller.json":
                """{"full":{"num_reads":2232}}""",
        }
        with TemporaryDirectory(files) as archive_path:
            message, report_level, context = get_chip_status(archive_path)
            self.assertEquals(message, "Loading 69.9% | Gain 1.09 | Total Reads: Below Spec")

    def test_get_total_reads_message_below(self):
        files = {
            "basecaller_results/ionstats_basecaller.json":
                """{"full":{"num_reads":2232}}""",
        }
        with TemporaryDirectory(files) as archive_path:
            message, reads, spec = get_total_reads_message("314", archive_path)
            self.assertEquals(message, "Total Reads: Below Spec")
            self.assertEquals(reads, 2232)
            self.assertEquals(spec, 400000)

    def test_get_total_reads_message_near(self):
        files = {
            "basecaller_results/ionstats_basecaller.json":
                """{"full":{"num_reads":361385}}""",
        }
        with TemporaryDirectory(files) as archive_path:
            message, reads, spec = get_total_reads_message("PIV3", archive_path)
            self.assertEquals(message, "Total Reads: Near Spec")
            self.assertEquals(reads, 59989910)
            self.assertEquals(spec, 60000000)
