from django.test import SimpleTestCase

from plots.key_trace import (
    parse_key_traces,
    get_nuc_flows,
    get_key_traces_dygraphs_data,
)
from plots.nuc_step import parse_nuc_step_lines

import json


class RawTraceAlphaTestCase(SimpleTestCase):
    test_nuc_step_lines = [
        "2	C	310.71",
        "0	T	304.93",
        "3	G	365.99",
        "1	A	378.95",
        "4	G	395.24",
    ]

    def test_parse_nuc_step(self):
        results = parse_nuc_step_lines(self.test_nuc_step_lines)
        # FLOW A C T G
        self.assertEquals(
            results,
            [
                [0, None, None, 304.93, None],
                [1, 378.95, None, None, None],
                [2, None, 310.71, None, None],
                [3, None, None, None, 365.99],
                [4, None, None, None, 395.24],
            ],
        )

    test_key_lines = [
        "1	A	100	150	400	450	189	-18 -18.348	-18.348",
        "3	G	100	150	400	450	189	-15	-12.761	-15.761",
        "0	T	100	150	400	450	189	-15	-13.173	-15.173",
        "2	A	100	150	400	450	189	-18 -18.348	-18.348",
        "4	G	100	150	400	450	189	-15	-12.761	-15.761",
        "6	T	100	150	400	450	189	-15	-13.173	-15.173",
        "7	C	100	150	400	450	189	-15	-13.173	-22",
        "8	A	100	150	400	450	189	-15	-13.173	-15.173",
        "5	G	100	150	400	450	189	-15	-13.173	-15.173",
    ]

    def test_parse_key_traces(self):
        results = parse_key_traces(self.test_key_lines)

        self.assertEquals(len(results), 8)

        # Check first element
        self.assertEquals(results[0][0], 0)
        self.assertEquals(results[0][1], "T")
        self.assertDictEqual(
            results[0][2],
            {"xmin": 100, "xmax": 150, "ymin": 400, "ymax": 450, "count": 189},
        )
        self.assertEquals(results[0][3], [-15.0, -13.173, -15.173])

        # Check last element
        self.assertEquals(results[7][0], 7)
        self.assertEquals(results[7][1], "C")
        self.assertDictEqual(
            results[7][2],
            {"xmin": 100, "xmax": 150, "ymin": 400, "ymax": 450, "count": 189},
        )
        self.assertEquals(results[7][3], [-15.0, -13.173, -22])

    def test_get_nuc_flows(self):
        # Should return the first flow where a specific nuc is incorporated and the first flow where it is not
        self.assertEquals(
            get_nuc_flows(
                "T", key="TCAG", flow_order="TACGTACGTCTGAGCATCGATCGATGTACAGC"
            ),
            (0, 4),
        )
        self.assertEquals(
            get_nuc_flows(
                "A", key="TCAG", flow_order="TACGTACGTCTGAGCATCGATCGATGTACAGC"
            ),
            (5, 1),
        )
        self.assertEquals(
            get_nuc_flows(
                "C", key="TCAG", flow_order="TACGTACGTCTGAGCATCGATCGATGTACAGC"
            ),
            (2, 6),
        )
        self.assertEquals(
            get_nuc_flows(
                "G", key="TCAG", flow_order="TACGTACGTCTGAGCATCGATCGATGTACAGC"
            ),
            (7, 3),
        )

    def test_key_trace_output(self):
        regions = [
            [
                "test",
                # bead
                [
                    "2	C	100	150	400	450	1592	0.938	0.938	0.938	0.938	0.938	0.938	0.938	0.938	0.938	-1.460",
                    "0	T	100	150	400	450	1592	-0.929	-0.929	-0.929	-0.929	-0.929	-0.929	-0.929	-0.929	-0.929	-2.070",
                    "3	G	100	150	400	450	1592	0.141	0.141	0.141	0.141	0.141	0.141	0.141	0.141	0.141	-2.812",
                    "1	A	100	150	400	450	1592	-2.072	-2.072	-2.072	-2.072	-2.072	-2.072	-2.072	-2.072	-2.072	-4.192",
                    "7	G	100	150	400	450	1592	-0.588	-0.588	-0.588	-0.588	-0.588	-0.588	-0.588	-0.588	-0.588	-3.634",
                    "4	T	100	150	400	450	1592	0.898	0.898	0.898	0.898	0.898	0.898	0.898	0.898	0.898	-1.859",
                    "6	C	100	150	400	450	1592	1.846	1.846	1.846	1.846	1.846	1.846	1.846	1.846	1.846	-1.082",
                    "5	A	100	150	400	450	1592	-2.808	-2.808	-2.808	-2.808	-2.808	-2.808	-2.808	-2.808	-2.808	-4.904",
                ],
                # empty
                [
                    "2	C	100	150	400	450	888	    0.578	0.578	0.578	0.578	0.578	0.578	0.578	0.578	0.578	-1.042",
                    "0	T	100	150	400	450	888	    -1.281	-1.281	-1.281	-1.281	-1.281	-1.281	-1.281	-1.281	-1.281	-2.281",
                    "1	A	100	150	400	450	888	    -2.220	-2.220	-2.220	-2.220	-2.220	-2.220	-2.220	-2.220	-2.220	-4.838",
                    "3	G	100	150	400	450	888	    -0.321	-0.321	-0.321	-0.321	-0.321	-0.321	-0.321	-0.321	-0.321	-3.183",
                    "7	G	100	150	400	450	888	    -0.780	-0.780	-0.780	-0.780	-0.780	-0.780	-0.780	-0.780	-0.780	-3.795",
                    "4	T	100	150	400	450	888	    0.566	0.566	0.566	0.566	0.566	0.566	0.566	0.566	0.566	-2.251",
                    "6	C	100	150	400	450	888	    1.610	1.610	1.610	1.610	1.610	1.610	1.610	1.610	1.610	-1.411",
                    "5	A	100	150	400	450	888	    -3.018	-3.018	-3.018	-3.018	-3.018	-3.018	-3.018	-3.018	-3.018	-5.165",
                ],
            ]
        ]
        frame_starts = [
            0,
            0.066,
            0.133,
            0.199,
            0.266,
            0.333,
            0.399,
            0.466,
            0.533,
            0.599,
        ]

        output_traces = get_key_traces_dygraphs_data(regions, frame_starts)[
            "dygraphs_key_trace_data"
        ][0]

        # Output data trace from original raw trace code
        legacy_traces = [
            [0, 0.02, 0.124, 0.062, -0.27],
            [0.066, 0.02, 0.124, 0.062, -0.27],
            [0.133, 0.02, 0.124, 0.062, -0.27],
            [0.199, 0.02, 0.124, 0.062, -0.27],
            [0.266, 0.02, 0.124, 0.062, -0.27],
            [0.333, 0.02, 0.124, 0.062, -0.27],
            [0.399, 0.02, 0.124, 0.062, -0.27],
            [0.466, 0.02, 0.124, 0.062, -0.27],
            [0.533, 0.02, 0.124, 0.062, -0.27],
            [0.599, -0.181, -0.747, -0.385, -0.21],
        ]

        self.assertEqual(output_traces, legacy_traces)
