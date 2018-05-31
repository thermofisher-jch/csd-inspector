from django.test import SimpleTestCase
from xml.etree import ElementTree
from main import get_chef_notifications
from datetime import datetime


class ChefNotificationsTestCase(SimpleTestCase):
    def test_warnings_70_min_before_run_start(self):
        # see IO-317
        notifications = get_chef_notifications(ElementTree.fromstring("".join([
            "<RunLog> ",
            "	<Warnings_Run>",
            "       <warning>",
            "           <time>20180406_150236</time>",
            "           <usr>60</usr>",
            "           <sys>9580</sys>",
            "           <sys_name>LC_OPTIONAL</sys_name>",
            "           <usr_msg>Load Check Warning. </usr_msg>",
            "           <resolution>Obsolete field.</resolution>",
            "           <msg> Optional round of load check inspections found a fault.</msg>",
            "       </warning>",
            "	</Warnings_Run>",
            "</RunLog>"
        ])), datetime(2018, 4, 6, 16, 12))

        self.assertEquals(len(notifications), 0)

    def test_warnings_2_min_before_run_start(self):
        # see IO-317
        notifications = get_chef_notifications(ElementTree.fromstring("".join([
            "<RunLog> ",
            "	<Warnings_Run>",
            "       <warning>",
            "           <time>20180406_150236</time>",
            "           <usr>60</usr>",
            "           <sys>9580</sys>",
            "           <sys_name>LC_OPTIONAL</sys_name>",
            "           <usr_msg>Load Check Warning. </usr_msg>",
            "           <resolution>Obsolete field.</resolution>",
            "           <msg> Optional round of load check inspections found a fault.</msg>",
            "       </warning>",
            "	</Warnings_Run>",
            "</RunLog>"
        ])), datetime(2018, 4, 6, 15, 4))

        self.assertEquals(len(notifications), 1)

    def test_warnings_after_run_start(self):
        notifications = get_chef_notifications(ElementTree.fromstring("".join([
            "<RunLog> ",
            "	<Warnings_Run>",
            "       <warning>",
            "           <time>20180406_150236</time>",
            "           <usr>60</usr>",
            "           <sys>9580</sys>",
            "           <sys_name>LC_OPTIONAL</sys_name>",
            "           <usr_msg>Load Check Warning. </usr_msg>",
            "           <resolution>Obsolete field.</resolution>",
            "           <msg> Optional round of load check inspections found a fault.</msg>",
            "       </warning>",
            "	</Warnings_Run>",
            "</RunLog>"
        ])), datetime(2018, 4, 6, 15, 0))

        self.assertEquals(len(notifications), 1)
