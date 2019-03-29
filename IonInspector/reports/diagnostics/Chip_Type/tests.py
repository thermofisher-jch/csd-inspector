from django.test import SimpleTestCase
from .main import parse_efuse


class ParseEfuseTestCase(SimpleTestCase):
    def test_parse(self):
        results = parse_efuse(
            "L:Q6P682,W:16,X:5,Y:7,P:20,FC:V,B:1,CT:GX5v2,BC:21DAFA00083*241GX5,,US:6"
        )
        self.assertDictEqual(
            results,
            {
                # raw values
                "L": "Q6P682",
                "W": "16",
                "X": "5",
                "Y": "7",
                "P": "20",
                "FC": "V",
                "B": "1",
                "CT": "GX5v2",
                "BC": "21DAFA00083*241GX5",
                "US": "6",
                # extra values
                "Assembly": "Tong Hsing",
                "Product": "RUO",
                "ExpirationYear": 2020,
                "ExpirationMonth": 1,
            },
        )

