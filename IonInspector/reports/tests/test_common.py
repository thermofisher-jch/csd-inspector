from django.test import SimpleTestCase
from IonInspector.reports.diagnostics.common.inspector_utils import parse_ts_version, get_xml_from_run_log

from reports.diagnostics.common.inspector_utils import TemporaryDirectory


class InspectorUtilsTestCase(SimpleTestCase):
    def test_parse_ts_version(self):
        self.assertEqual(parse_ts_version("5.0"), "5.0.0")
        self.assertEqual(parse_ts_version("5.2"), "5.2.0")
        self.assertEqual(parse_ts_version("5.6.0.RC2"), "5.6.0-rc.2")

    def test_get_xml_from_run_log(self):
        files = {
            "/var/log/IonChef/RunLog/242471001-000040_rl_2018-4-6_1504.xml": """
            <root>
                <Warnings_All>
                    <warning>
                    <time>20180405_111932</time><usr>37</usr><sys>1500</sys><sys_name>VISION</sys_name><usr_msg>Vision System Fault.</usr_msg><resolution>Obsolete field.</resolution><msg> microscan. Failed barcode scanning of lc_pcr_plate_bc.</msg>
                    </warning>
                </Warnings_All>
            </root>
            """
        }
        with TemporaryDirectory(files) as archive_path:
            root = get_xml_from_run_log(archive_path)
            notification_elements = root.findall("Warnings_All/warning")
            self.assertEquals(len(notification_elements), 1)
