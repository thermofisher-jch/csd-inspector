from django.test import SimpleTestCase

from lemontest.diagnostics.common.inspector_utils import parse_ts_version


class InspectorUtilsTestCase(SimpleTestCase):
    def test_parse_ts_version(self):
        self.assertEqual(parse_ts_version("5.0"), "5.0.0")
        self.assertEqual(parse_ts_version("5.2"), "5.2.0")
        self.assertEqual(parse_ts_version("5.6.0.RC2"), "5.6.0-rc.2")
