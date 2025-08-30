__copyright__ = "Copyright 2021, 3Liz"
__license__ = "GPL version 3"
__email__ = "info@3liz.org"

import unittest

from qgis_plugin_manager.utils import similar_names


class TestUtils(unittest.TestCase):
    def test_similar_names(self):
        """Test about similar names in the XML file."""
        # typo wanted
        self.assertListEqual(
            ["Lizmap"],
            list(similar_names("lizma", ["a", "Lizmap", "QuickOSM"])),
        )

        existing = ["data plotly", "DATA PLOTLY", "Data   PLOTLY"]

        # lower case
        self.assertListEqual(
            existing,
            list(similar_names("dataplotly", existing)),
        )

        # upper case
        self.assertListEqual(
            existing,
            list(similar_names("DATA PLOT LY", existing)),
        )
