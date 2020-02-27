from django.test import SimpleTestCase

from reports.diagnostics.Genexus_Test_Fragments.main import get_tf_details


class TestTFDetail(SimpleTestCase):
    tf_stats = {"CF-1": {"Percent 50Q17": 89.798}}

    tf_stats_2 = {"CF-1": {"Percent 100Q17": 89.798}}

    basecaller_stats = {"BeadSummary": {"tf": {"valid": 78976}}}

    basecaller_stats_2 = {"BeadSummary": {"tf": {"no_valid": 78976}}}

    def test_get_tf_details(self):
        self.assertEqual(
            get_tf_details(self.tf_stats, self.basecaller_stats),
            "CF-1: 89.8% | Total Valid Reads: 78976",
        )

        self.assertEqual(
            get_tf_details(self.tf_stats_2, self.basecaller_stats_2),
            "CF-1: Unknown | Total Valid Reads: Unknown",
        )
