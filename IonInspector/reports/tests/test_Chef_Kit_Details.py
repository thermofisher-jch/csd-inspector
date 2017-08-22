from xml.etree import ElementTree

from django.test import SimpleTestCase

from lemontest.diagnostics.Chef_Kit_Details.main import get_chip_names_from_element_tree, get_kit_from_element_tree


class ChefChipTestCase(SimpleTestCase):
    test_element_tree_2_chips = ElementTree.fromstring("".join([
        "<RunLog> ",
        "	<RunInfo>",
        "		<chip>1</chip>",
        "		<chip2>316</chip2>",
        "		<chipVersion>3</chipVersion>",
        "		<chipVersion2>0</chipVersion2>",
        "	</RunInfo>",
        "</RunLog>"
    ]))

    test_element_tree_1_chip = ElementTree.fromstring("".join([
        "<RunLog> ",
        "	<RunInfo>",
        "		<chip>1</chip>",
        "		<chipVersion>3</chipVersion>",
        "	</RunInfo>",
        "</RunLog>"
    ]))

    test_element_tree_no_chips = ElementTree.fromstring("".join([
        "<RunLog> ",
        "	<RunInfo>",
        "	</RunInfo>",
        "</RunLog>"
    ]))

    test_element_tree_kit_hiq = ElementTree.fromstring("".join([
        "<RunLog> ",
        "	<RunInfo>",
        "       <kit>pgm_ic_v2</kit>",
        "	</RunInfo>",
        "</RunLog>"
    ]))

    test_element_tree_kit_none = ElementTree.fromstring("".join([
        "<RunLog> ",
        "	<RunInfo>",
        "	</RunInfo>",
        "</RunLog>"
    ]))

    def test_get_chip_names_from_element_tree_2_chips(self):
        chip_a, chip_b = get_chip_names_from_element_tree(self.test_element_tree_2_chips)
        self.assertEqual(chip_a, "P1v3")
        self.assertEqual(chip_b, "316")

    def test_get_chip_names_from_element_tree_1_chip(self):
        chip_a, chip_b = get_chip_names_from_element_tree(self.test_element_tree_1_chip)
        self.assertEqual(chip_a, "P1v3")
        self.assertEqual(chip_b, None)

    def test_get_chip_names_from_element_tree_no_chip(self):
        chip_a, chip_b = get_chip_names_from_element_tree(self.test_element_tree_no_chips)
        self.assertEqual(chip_a, None)
        self.assertEqual(chip_b, None)

    def test_get_kit_from_element_tree_hiq(self):
        kit = get_kit_from_element_tree(self.test_element_tree_kit_hiq)
        self.assertEqual(kit, "Ion PGM Hi-Q Chef Kit")

    def test_get_kit_from_element_tree_no_kit(self):
        kit = get_kit_from_element_tree(self.test_element_tree_kit_none)
        self.assertEqual(kit, None)
