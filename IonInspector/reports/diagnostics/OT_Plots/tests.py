from django.test import SimpleTestCase

from reports.diagnostics.OT_Plots.main import parse_timestamp


class OTPlotsTestCase(SimpleTestCase):
    test_log = [
        "Tue Feb 28 09:16:33 2017:",
        "Init Kit entered as <SEQ0023>",
        "productDesc: Ion S5 Cleaning Solution",
        "partNumber: 100031096",
        "lotNumber: 013080",
        "expDate: 2017/03/11",
        "remainingUses: 3",
        "productDesc: Ion S5 Wash Solution",
        "partNumber: 100031090",
        "lotNumber: 013080",
        "expDate: 2015/02/14",
        "remainingUses: 1"
    ]

    def test_parse_timestamp(self):
        self.assertEqual(parse_timestamp("Thu Jan  1 03:10:34 1970"), 11434.0)
        self.assertEqual(parse_timestamp("Thu Jan  1 03:11:08 1970"), 11468.0)
        self.assertEqual(parse_timestamp("Thu Apr 26 19:12:50 2018"), 1524769970.0)
