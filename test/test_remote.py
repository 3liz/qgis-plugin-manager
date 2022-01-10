__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import unittest

from pathlib import Path

from qgis_plugin_manager.remote import Remote


class TestRemote(unittest.TestCase):

    def test_list_remote(self):
        """ Test read the sources.list file. """
        self.remote = Remote(Path('fixtures/plugins'))
        self.assertCountEqual(
            ["https://my.url/plugins.xml", "https://my.repo/plugins.xml"],
            self.remote.remote_list())

    @unittest.expectedFailure
    def test_latest_pgmetadata(self):
        """ Test read multiple remotes. """
        # There is 0.1.0 and 0.2.0 in these XML files
        self.assertEqual('0.2.0', self.remote.latest("PgMetadata"))

    def test_plugin_name_with_space(self):
        """ Test plugin with different name. """
        self.remote = Remote(Path('fixtures/plugins'))
        self.remote.list_plugins = {}
        plugins = self.remote._parse_xml(Path('fixtures/plugins_xml/dataplotly.xml'), {})
        print(self.remote.list_plugins)
        self.assertDictEqual({'Data Plotly': '0.4'}, plugins)

        search = "foo"
