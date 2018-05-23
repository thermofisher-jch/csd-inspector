from django.test import SimpleTestCase
from datetime import date

from reports.diagnostics.S5_Reagents.main import parse_init_log, parse_start_time, reagents_expired


class S5ReagentsTestCase(SimpleTestCase):
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
        "remainingUses: 1",
        "productDesc: Precision ID Cleaning Solution",
        "partNumber: 100049484",
        "lotNumber: 1943228",
        "expDate: 2018/11/30",
        "remainingUses: 4"
    ]
    test_start_time = "02/28/2017 12:48:49"

    def test_parse_init_log_keys(self):
        results = parse_init_log(self.test_log)
        self.assertItemsEqual(results.keys(), ["Ion S5 Cleaning Solution", "Ion S5 Wash Solution", "Precision ID Cleaning Solution"])

    def test_parse_init_log_strings(self):
        results = parse_init_log(self.test_log)
        self.assertEqual(results["Ion S5 Cleaning Solution"]["lotNumber"], "013080")
        self.assertEqual(results["Ion S5 Cleaning Solution"]["productDesc"], "Ion S5 Cleaning Solution")
        self.assertEqual(results["Ion S5 Cleaning Solution"]["remainingUses"], "3")

    def test_parse_init_log_dates(self):
        results = parse_init_log(self.test_log)
        self.assertEqual(results["Ion S5 Cleaning Solution"]["expDate"], date(2017, 03, 11))
        self.assertEqual(results["Ion S5 Wash Solution"]["expDate"], date(2015, 02, 14))

    def test_parse_start_time(self):
        results = parse_start_time(self.test_start_time)
        self.assertEqual(results, date(2017, 02, 28))

    def test_reagents_expired(self):
        self.assertTrue(reagents_expired(date(2017, 02, 28), [date(2017, 01, 27)]))
        self.assertFalse(reagents_expired(date(2017, 02, 28), [date(2017, 04, 29)]))
        # Reagents that expire before a run but in the same month should not be expired:
        # https://jira.amer.thermo.com/browse/IO-252
        self.assertFalse(reagents_expired(date(2017, 02, 28), [date(2017, 02, 10)]))
