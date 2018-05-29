from xml.etree import ElementTree

from django.test import SimpleTestCase

from reports.diagnostics.Chef_Kit_Details.main import get_chip_names_from_element_tree, get_kit_from_element_tree


class ChefChipTestCase(SimpleTestCase):
    def test_get_chip_names_from_element_tree_2_chips(self):
        chip_a, chip_b = get_chip_names_from_element_tree(ElementTree.fromstring("".join([
            "<RunLog> ",
            "	<RunInfo>",
            "		<chip>1</chip>",
            "		<chip2>316</chip2>",
            "		<chipVersion>3</chipVersion>",
            "		<chipVersion2>0</chipVersion2>",
            "	</RunInfo>",
            "</RunLog>"
        ])))
        self.assertEqual(chip_a, "P1v3")
        self.assertEqual(chip_b, "316")

    def test_get_chip_names_from_element_tree_1_chip(self):
        chip_a, chip_b = get_chip_names_from_element_tree(ElementTree.fromstring("".join([
            "<RunLog> ",
            "	<RunInfo>",
            "		<chip>1</chip>",
            "		<chipVersion>3</chipVersion>",
            "	</RunInfo>",
            "</RunLog>"
        ])))
        self.assertEqual(chip_a, "P1v3")
        self.assertEqual(chip_b, None)

    def test_get_chip_names_from_element_tree_no_chip(self):
        chip_a, chip_b = get_chip_names_from_element_tree(ElementTree.fromstring("".join([
            "<RunLog> ",
            "	<RunInfo>",
            "	</RunInfo>",
            "</RunLog>"
        ])))
        self.assertEqual(chip_a, None)
        self.assertEqual(chip_b, None)

    def test_get_chip_names_from_element_tree_500(self):
        chip_a, chip_b = get_chip_names_from_element_tree(ElementTree.fromstring("".join([
            "<RunLog> ",
            "	<RunInfo>",
            "      <chip>530</chip>",
            "      <chip2>500</chip2>",
            "	</RunInfo>",
            "</RunLog>"
        ])))
        self.assertEqual(chip_a, "530")
        self.assertEqual(chip_b, "Balance")

    def test_get_kit_from_element_tree_hiq(self):
        kit = get_kit_from_element_tree(ElementTree.fromstring("".join([
            "<RunLog> ",
            "	<RunInfo>",
            "       <kit>pgm_ic_v2</kit>",
            "	</RunInfo>",
            "</RunLog>"
        ])))
        self.assertEqual(kit, "Ion PGM Hi-Q Chef Kit")

    def test_get_kit_from_element_tree_no_kit(self):
        kit = get_kit_from_element_tree(ElementTree.fromstring("".join([
            "<RunLog> ",
            "	<RunInfo>",
            "	</RunInfo>",
            "</RunLog>"
        ])))
        self.assertEqual(kit, None)
