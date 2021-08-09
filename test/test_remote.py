__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import unittest

from pathlib import Path

from qgis_plugin_manager.remote import Remote


class PluginManager(unittest.TestCase):

    def setUp(self) -> None:
        self.remote = Remote(Path('fixtures/plugins'))

    def test_list_remote(self):
        self.assertCountEqual(
            ["https://my.url/plugins.xml", "https://my.repo/plugins.xml"],
            self.remote.remote_list())

    @unittest.expectedFailure
    def test_latest_pgmetadata(self):
        # There is 0.1.0 and 0.2.0 in these XML files
        self.assertEqual('0.2.0', self.remote.latest("PgMetadata"))
