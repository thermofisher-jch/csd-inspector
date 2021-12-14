from django.test import SimpleTestCase
import tarfile
import StringIO
import datetime
from reports.diagnostics.common.inspector_utils import (
    parse_ts_version,
    get_xml_from_run_log,
    get_lines_from_chef_gui_logs,
    get_run_log_data,
)

from reports.diagnostics.common.inspector_utils import TemporaryDirectory


class InspectorUtilsTestCase(SimpleTestCase):
    def test_parse_ts_version(self):
        self.assertEqual(parse_ts_version("5.0"), "5.0.0")
        self.assertEqual(parse_ts_version("5.2"), "5.2.0")
        self.assertEqual(parse_ts_version("5.6.0.RC2"), "5.6.0-rc.2")
        self.assertEqual(parse_ts_version("6.15.3.1"), "6.15.3-1")
        self.assertEqual(parse_ts_version("6.16.4.1.10"), "6.16.4-1.10")

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

    def test_get_lines_from_chef_gui_logs(self):
        files = {
            "/var/log/IonChef/ICS/gui-2018-10-16-15-22.log": """
                   [TSLINK]-[INFO]:2018-11-02 01:19:47,121: In post_chef_status::handle()
                    [TSLINK]-[INFO]:2018-11-02 01:19:47,122: Json Object {"chefLastUpdate":"2018-11-02T01:19:47","chefStatus":"ISP Collection","chefProgress":"49","chefLogPath":"","chefRemainingSeconds":"33154","chefOperationMode":"Customer Mode","chefProtocolDeviationName":"","chefStartTime":"2018-11-01T16:33:46","total_process_time":"65009","chefTimeZone":"US/Eastern","chefKitType":"Ion 550 Kit-Chef","chefSolutionsPart":"A36410C","chefChipExpiration1":"Aug2019","chefChipExpiration2":"None","chefReagentsPart":"A34540C","chefSolutionsExpiration":"190731","chefReagentsLot":"2012013","chefReagentsSerialNum":"12345710","chefSamplePos":"1","chefTipRackBarcode":"47620013A","chefChipType1":"550v1","chefChipType2":"S500","chefReagentsExpiration":"190831","chefSolutionsLot":"1986520","chefSolutionsSerialNum":"12346014","chefPackageVer":"IC.5.10.0","chefScriptVersion":"803","chefInstrumentName":"CHEF01167","chefExtraInfo_1":"","chefExtraInfo_2":"","chefFlexibleWorkflow":"Single-chip run 1"}
                    [TSLINK]-[INFO]:2018-11-02 01:19:47,123: PostChefStatusService: HTTP: http://storm.ite/rundb/api/v1/experiment/2091/
                    """
        }
        with TemporaryDirectory(files) as archive_path:
            # write a tar log for testing
            with tarfile.open(
                archive_path + "/var/log/IonChef/ICS/gui-2018-09-03-12-13.tar", "w"
            ) as tar:
                tar_data = """
                    [TSLINK]-[INFO]:2018-09-03 01:19:47,121: In post_chef_status::handle()
                    [TSLINK]-[INFO]:2018-09-03 01:19:47,122: Json Object {"chefLastUpdate":"2018-11-02T01:19:47","chefStatus":"ISP Collection","chefProgress":"49","chefLogPath":"","chefRemainingSeconds":"33154","chefOperationMode":"Customer Mode","chefProtocolDeviationName":"","chefStartTime":"2018-11-01T16:33:46","total_process_time":"65009","chefTimeZone":"US/Eastern","chefKitType":"Ion 550 Kit-Chef","chefSolutionsPart":"A36410C","chefChipExpiration1":"Aug2019","chefChipExpiration2":"None","chefReagentsPart":"A34540C","chefSolutionsExpiration":"190731","chefReagentsLot":"2012013","chefReagentsSerialNum":"12345710","chefSamplePos":"1","chefTipRackBarcode":"47620013A","chefChipType1":"550v1","chefChipType2":"S500","chefReagentsExpiration":"190831","chefSolutionsLot":"1986520","chefSolutionsSerialNum":"12346014","chefPackageVer":"IC.5.10.0","chefScriptVersion":"803","chefInstrumentName":"CHEF01167","chefExtraInfo_1":"","chefExtraInfo_2":"","chefFlexibleWorkflow":"Single-chip run 1"}
                    [TSLINK]-[INFO]:2018-09-03 01:19:47,123: PostChefStatusService: HTTP: http://storm.ite/rundb/api/v1/experiment/2091/
                    """
                tar_info = tarfile.TarInfo(
                    "/var/log/IonChef/ICS/gui-2018-09-03-12-13.log"
                )
                tar_info.size = len(tar_data)
                tar.addfile(tar_info, StringIO.StringIO(tar_data))

            lines = get_lines_from_chef_gui_logs(archive_path)
            self.assertEquals(len(lines), 6)
            self.assertListEqual(
                lines[0],
                [
                    "[TSLINK]-[INFO]",
                    datetime.datetime(2018, 9, 3, 1, 19, 47),
                    "In post_chef_status::handle()",
                ],
            )
            self.assertListEqual(
                lines[5],
                [
                    "[TSLINK]-[INFO]",
                    datetime.datetime(2018, 11, 2, 1, 19, 47),
                    "PostChefStatusService: HTTP: http://storm.ite/rundb/api/v1/experiment/2091/",
                ],
            )


class GetRunLogDataTestCase(SimpleTestCase):
    run_log_lines = [
        "timestamp,n_stage,stage0,stage1,stage2,last_code,tach_chassis",
        "2.783859968,10553,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,89",
        "20.67976213,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
        "23.25025606,10555,load,NOT_SPECIFIED,NOT_SPECIFIED,NONE,100",
        "28.7172451,10557,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,80",
        "34.27806306,10558,prep,NOT_SPECIFIED,NOT_SPECIFIED,NONE,128",
    ]
    run_log_fields = [["tach_chassis", "Speed", int]]

    def test_get_run_log_data_valid(self):
        data = get_run_log_data(self.run_log_lines, self.run_log_fields)
        self.assertDictEqual(
            data["stages"][0], {"name": "START", "start": 0, "end": 2.783859968}
        )
        self.assertDictEqual(
            data["stages"][1], {"name": "LOAD", "start": 2.783859968, "end": 28.7172451}
        )
        self.assertDictEqual(
            data["stages"][2], {"name": "PREP", "start": 28.7172451, "end": 34.27806306}
        )

    def test_get_run_log_data_missing(self):
        data = get_run_log_data(self.run_log_lines[0:1], self.run_log_fields)
        self.assertEquals(len(data["stages"]), 0)
