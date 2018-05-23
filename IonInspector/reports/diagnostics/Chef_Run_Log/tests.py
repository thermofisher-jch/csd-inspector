from django.test import SimpleTestCase
from main import get_run_log_data


class GetRunLogDataTestCase(SimpleTestCase):
    run_log_lines = [
        "timestamp,n_stage,stage0,stage1,stage2,last_code,tach_chassis",
        "2.783859968,10553,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,89",
        "20.67976213,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
        "23.25025606,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
        "28.7172451,10557,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,80",
        "34.27806306,10558,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128"
    ]
    run_log_fields = [
        ["tach_chassis", "Speed", int]
    ]

    def test_get_run_log_data_valid(self):
        data = get_run_log_data(self.run_log_lines, self.run_log_fields)
        self.assertDictEqual(data["stages"][0], {"name": "START", "start": 0, "end": 2.783859968})
        self.assertDictEqual(data["stages"][1], {"name": "LOAD", "start": 2.783859968, "end": 28.7172451})
        self.assertDictEqual(data["stages"][2], {"name": "PREP", "start": 28.7172451, "end": 34.27806306})

    def test_get_run_log_data_missing(self):
        data = get_run_log_data(self.run_log_lines[0:1], self.run_log_fields)
        self.assertEquals(len(data["stages"]), 0)
