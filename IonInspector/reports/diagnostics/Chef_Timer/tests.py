from django.test import SimpleTestCase
from main import get_chef_pause_info


class ChefTimerTestCase(SimpleTestCase):
    def test_no_pause(self):
        run_log_lines = [
            "timestamp,n_stage,stage0,stage1,stage2,last_code,tach_chassis",
            "2.783859968,10553,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,89",
            "20.67976213,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
            "23.25025606,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
            "28.7172451,10557,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,80",
            "34.27806306,10558,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
            "10939.27806306,10558,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
        ]
        message = get_chef_pause_info(run_log_lines)
        self.assertEquals(message, "Total Time: 3h 2m")

    def test_mr_coffee(self):
        run_log_lines = [
            "timestamp,n_stage,stage0,stage1,stage2,last_code,tach_chassis",
            "2.783859968,10553,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,89",
            "20.67976213,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
            "23.25025606,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
            "28.7172451,10557,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,80",
            "34.27806306,10558,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
            "6899.27806306,10558,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
            "9839.27806306,10558,mrcoffee,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
            "10939.27806306,10558,mrcoffee,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
        ]
        message = get_chef_pause_info(run_log_lines)
        self.assertEquals(message, "Total Time: 3h 2m | Mr Coffee: 0h 18m")

    def test_user_pause(self):
        run_log_lines = [
            "timestamp,n_stage,stage0,stage1,stage2,last_code,tach_chassis",
            "2.783859968,10553,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,89",
            "20.67976213,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
            "23.25025606,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
            "28.7172451,10557,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,80",
            "34.27806306,10558,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
            "6899.27806306,10558,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
            "9839.27806306,10558,enr,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
            "10939.27806306,10558,enr,PAUSE,NOT_SPECIFIED,NONE,128",
            "11639.27806306,10558,enr,PAUSE,NOT_SPECIFIED,NONE,128",
            "12339.27806306,10558,enr,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
        ]
        message = get_chef_pause_info(run_log_lines)
        self.assertEquals(message, "Total Time: 3h 25m | User Pause: 0h 23m")
