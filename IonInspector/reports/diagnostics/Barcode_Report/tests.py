from xml.etree import ElementTree

from django.test import SimpleTestCase

from reports.diagnostics.Barcode_Report.main import (
    get_read_group_file_prefixes,
    get_read_groups,
)


class BarcodeReportTestCase(SimpleTestCase):
    datasets_basecaller_object = {
        "datasets": [
            {
                "basecaller_bam": "nomatch_rawlib.basecaller.bam",
                "dataset_name": "none/No_barcode_match",
                "file_prefix": "nomatch_rawlib",
                "read_count": 160472,
                "read_groups": ["3CFN9.nomatch"],
            },
            {
                "basecaller_bam": "IonXpress_001_rawlib.basecaller.bam",
                "dataset_name": "none/IonXpress_001",
                "file_prefix": "IonXpress_001_rawlib",
                "read_count": 0,
                "read_groups": ["3CFN9.IonXpress_001"],
            },
        ],
        "read_groups": {
            "3CFN9.IonXpress_001": {
                "Q20_bases": 0,
                "barcode_adapter": "GAT",
                "barcode_adapter_filtered": 6,
                "barcode_bias": [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
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
                "sample": "first sample",
                "total_bases": 0,
            },
            "PS1F0.IonDual_0101": {
                "index": 101,
                "barcode_name": "IonDual_0101",
                "description": "",
                "reference": "hg19",
                "end_barcode": {
                    "barcode_name": "IonDual_0101",
                    "analyze_as_single": True,
                    "barcode_adapter": "CTGAG",
                    "barcode_sequence": "TGACTCTATTCG",
                    "barcode_filtered": 10,
                    "adapter_filtered": 0,
                    "barcode_errors_hist": [3631, 315, 0, 0],
                    "no_bead_adapter": 0,
                },
                "nucleotide_type": "",
                "barcode": {
                    "barcode_name": "IonDual_0101",
                    "barcode_bias": [
                        0.053637191177676735,
                        0.053648410891852835,
                        -0.1401619380152232,
                        -0.04387089067349008,
                        0.006179434335515678,
                        -0.02643830058674247,
                        -0.14374397079643714,
                        0.0169807513840535,
                        0.029077873758452194,
                        -0.06139736418043803,
                        -0.0127854147674395,
                        0.024590281945734763,
                        -0.04911393494010767,
                        0.025691993109119318,
                        -0.020138160092527273,
                    ],
                    "barcode_adapter": "GGTGAT",
                    "barcode_distance_hist": [193540, 70877, 39534, 25217, 17719],
                    "barcode_adapter_filtered": 797,
                    "barcode_sequence": "CTAAGGTAAC",
                    "barcode_match_filtered": 8246,
                    "barcode_errors_hist": [317141, 27817, 1929],
                },
                "read_count": 346887,
                "sample": "NTC2_OCAv3",
                "Q20_bases": 11505028,
                "filtered": False,
                "platform_unit": "Valkyrie/GX5/Q0PH46/05/21DAFJ01369241GX5/IonDual_0101",
                "total_bases": 13547532,
            },
            "PS1F0.IonDual_0109-IonDual_0113": {
                "read_count": 609591,
                "reference": "OCAv3_designs_022619_Reference",
                "total_bases": 26244834,
                "barcode": {
                    "barcode_distance_hist": [454717, 96550, 32533, 13687, 12104],
                    "barcode_errors_hist": [590666, 18398, 527],
                    "barcode_bias": [
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    ],
                    "barcode_match_filtered": 2407,
                },
                "Q20_bases": 23558356,
                "filtered": False,
            },
            "3CFN9.nomatch": {
                "Q20_bases": 3366033,
                "description": "sample24repeatchiplot1OT3",
                "index": 0,
                "platform_unit": "proton/P2.2.2/nomatch",
                "read_count": 160472,
                "reference": "",
                "sample": "none",
                "total_bases": 27715310,
            },
        },
    }

    def test_get_read_group_file_prefixes(self):
        prefixes = get_read_group_file_prefixes(self.datasets_basecaller_object)
        self.assertEqual(prefixes["3CFN9.nomatch"], "nomatch_rawlib")
        self.assertEqual(prefixes["3CFN9.IonXpress_001"], "IonXpress_001_rawlib")

    def test_get_read_groups(self):
        groups = get_read_groups(self.datasets_basecaller_object)
        self.assertEqual(
            groups[0],
            {
                "group": "PS1F0.IonDual_0109-IonDual_0113",
                "sample_name": "N/A",
                "name": "IonDual_0109-IonDual_0113",
                "end_barcode": "",
                "read_count": 609591,
                "index": -1,
                "filtered": False,
                "nuc_type": "",
            },
        )
        self.assertEqual(
            groups[1],
            {
                "group": "3CFN9.nomatch",
                "sample_name": "none",
                "name": "nomatch",
                "end_barcode": "",
                "read_count": 160472,
                "index": 0,
                "filtered": True,
                "nuc_type": "",
            },
        )
        self.assertEqual(
            groups[2],
            {
                "group": "3CFN9.IonXpress_001",
                "sample_name": "first sample",
                "name": "IonXpress_001",
                "end_barcode": "",
                "read_count": 0,
                "index": 1,
                "filtered": True,
                "nuc_type": "",
            },
        )
        self.assertEqual(
            groups[3],
            {
                "group": "PS1F0.IonDual_0101",
                "sample_name": "NTC2_OCAv3",
                "name": "IonDual_0101",
                "end_barcode": "IonDual_0101",
                "read_count": 346887,
                "index": 101,
                "filtered": False,
                "nuc_type": "",
            },
        )
