import unittest

from qgis_plugin_manager.utils import parse_version


class TestUtils(unittest.TestCase):

    def test_version(self):
        self.assertListEqual([3, 10, 0], parse_version("3.10"))
        self.assertListEqual([3, 10, 0], parse_version("3.10.0"))
        self.assertIsNone(parse_version(""))
