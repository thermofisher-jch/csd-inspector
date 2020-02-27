from django.test import SimpleTestCase

from reports.diagnostics.Run_Sequence_Details.main import parse_run_number_from_run_name


class ChefChipTestCase(SimpleTestCase):
    def test_parse_run_number_from_run_name(self):
        self.assertEqual(
            parse_run_number_from_run_name(
                run_name="S5-00499-57-CAP_proficiency_2017_NGSST_0424201",
                device_name="S5-00499",
            ),
            "57",
        )
        self.assertEqual(
            parse_run_number_from_run_name(
                run_name="MT00200216-56-OFA_SP16_517rep_sp2017_185rep_197_217_218_227_228",
                device_name="MT00200216",
            ),
            "56",
        )
        self.assertEqual(
            parse_run_number_from_run_name(
                run_name="GNXS-0080-2-PG-Seq_baseline_HX_852_2s_013120",
                device_name="GNXS-0080",
            ),
            "2",
        )
