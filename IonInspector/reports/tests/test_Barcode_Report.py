from xml.etree import ElementTree

from django.test import SimpleTestCase

from reports.diagnostics.Barcode_Report.main import get_read_group_file_prefixes, get_read_groups


class BarcodeReportTestCase(SimpleTestCase):
    datasets_basecaller_object = {
        "datasets": [
            {
                "basecaller_bam": "nomatch_rawlib.basecaller.bam",
                "dataset_name": "none/No_barcode_match",
                "file_prefix": "nomatch_rawlib",
                "read_count": 160472,
                "read_groups": ["3CFN9.nomatch"]
            },
            {
                "basecaller_bam": "IonXpress_001_rawlib.basecaller.bam",
                "dataset_name": "none/IonXpress_001",
                "file_prefix": "IonXpress_001_rawlib",
                "read_count": 0,
                "read_groups": ["3CFN9.IonXpress_001"]
            }],
        "read_groups": {
            "3CFN9.IonXpress_001": {
                "Q20_bases": 0,
                "barcode_adapter": "GAT",
                "barcode_adapter_filtered": 6,
                "barcode_bias": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "barcode_distance_hist": [0, 0, 0, 0, 0],
                "barcode_errors_hist": [0, 0, 0],
                "barcode_match_filtered": 0,
                "barcode_name": "IonXpress_001",
                "barcode_sequence": "CTAAGGTAAC",
                "description": "sample24repeatchiplot1OT3",
                "filtered": True,
                "index": 1,
                "platform_unit": "proton/P2.2.2/IonXpress_001",
                "read_count": 0,
                "reference": "hg19",
                "sample": "none",
                "total_bases": 0
            },
            "3CFN9.nomatch": {
                "Q20_bases": 3366033,
                "description": "sample24repeatchiplot1OT3",
                "index": 0,
                "platform_unit": "proton/P2.2.2/nomatch",
                "read_count": 160472,
                "reference": "",
                "sample": "none",
                "total_bases": 27715310
            }
        }
    }

    def test_get_read_group_file_prefixes(self):
        prefixes = get_read_group_file_prefixes(self.datasets_basecaller_object)
        self.assertEqual(prefixes["3CFN9.nomatch"], "nomatch_rawlib")
        self.assertEqual(prefixes["3CFN9.IonXpress_001"], "IonXpress_001_rawlib")

    def test_get_read_groups(self):
        groups = get_read_groups(self.datasets_basecaller_object)
        self.assertEqual(groups[0],
                         {"group": "3CFN9.nomatch", "name": "No Barcode", "read_count": 160472, "index": 0,
                          "filtered": False})
        self.assertEqual(groups[1],
                         {"group": "3CFN9.IonXpress_001", "name": "IonXpress_001", "read_count": 0, "index": 1,
                          "filtered": True})
