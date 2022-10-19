__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import unittest

from qgis_plugin_manager.utils import parse_version, similar_names


class TestUtils(unittest.TestCase):

    def test_version(self):
        """ Test read versions. """
        self.assertListEqual([3, 10, 0], parse_version("3.10"))
        self.assertListEqual([3, 10, 0], parse_version("3.10.0"))
        self.assertIsNone(parse_version(""))

    def test_similar_names(self):
        """ Test about similar names in the XML file. """
        self.assertListEqual(
            ['Lizmap'],
            similar_names(
                'lizma',  # typo wanted
                ['a', 'Lizmap', 'QuickOSM', ]
            )
        )
