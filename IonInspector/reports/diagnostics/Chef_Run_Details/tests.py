from datetime import datetime
from xml.etree import ElementTree

from django.test import SimpleTestCase

from reports.diagnostics.Chef_Run_Details.main import parse_run_date_from_xml_path, get_deviation_from_element_tree, \
    get_cycles_and_extend


class ChefRunDetailsTestCase(SimpleTestCase):
    def test_get_cycles_and_extend(self):
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
                <RunType>rl</RunType>
                <cycles>18</cycles>
                <extend>4</extend>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_cycles_and_extend(element_tree), ("18", "4"))

    def test_get_cycles_and_extend_rc(self):
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
                <RunType>rc</RunType>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_cycles_and_extend(element_tree), (None, None))

    test_xml_path_1 = "example/242470601-000033_rc_2017-5-3_1547.xml"
    test_xml_path_2 = "/opt/example/242470284-000327_rl_2017-4-18_1759.xml"

    def test_parse_run_date_from_xml_path(self):
        run_date = parse_run_date_from_xml_path(self.test_xml_path_1)
        self.assertEqual(run_date, datetime(2017, 5, 3, hour=15, minute=47))

        run_date = parse_run_date_from_xml_path(self.test_xml_path_2)
        self.assertEqual(run_date, datetime(2017, 4, 18, hour=17, minute=59))

    def test_get_deviation_from_element_tree(self):
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
                <deviation>denature30_cycles45_20</deviation>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_deviation_from_element_tree(element_tree), "Myeloid")

    def test_get_deviation_with_lib_from_element_tree(self):
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
                <lib>200</lib>
                <deviation>denature30_cycles45_20</deviation>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_deviation_from_element_tree(element_tree), "Myeloid (200bp)")

    def test_get_deviation_with_lib_not_int_from_element_tree(self):
        """ Not a case I have seen but just covering my bases """
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
                <lib>ERROR</lib>
                <deviation>denature30_cycles45_20</deviation>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_deviation_from_element_tree(element_tree), "Myeloid (ERROR)")

    def test_get_unknown_deviation_from_element_tree(self):
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
                <deviation>some_new_thing</deviation>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_deviation_from_element_tree(element_tree), "Unknown(some_new_thing)")

    def test_get_no_deviation_from_element_tree(self):
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_deviation_from_element_tree(element_tree), None)

    def test_get_default_deviation_from_element_tree(self):
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
                <deviation>default</deviation>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_deviation_from_element_tree(element_tree), None)

    def test_get_default_deviation_with_lib_from_element_tree(self):
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
                <lib>400</lib>
                <deviation>default</deviation>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_deviation_from_element_tree(element_tree), "400bp")

    def test_get_pcr200bp_deviation_from_element_tree(self):
        element_tree = ElementTree.fromstring("""
        <RunLog>
            <RunInfo>
                <deviation>pcr200bp</deviation>
            </RunInfo>
        </RunLog>
        """)
        self.assertEquals(get_deviation_from_element_tree(element_tree), "200bp")
