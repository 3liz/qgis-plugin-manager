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

    def test_similar_names(self):
        """ Test about similar names in the XML file. """
        self.remote = Remote(Path('fixtures/xml_files/lizmap'))
        self.remote.parse_xml(Path('fixtures/xml_files/lizmap/lizmap.xml'), {})
        self.assertListEqual(['Lizmap'], self.remote.similar_names('lizmap'))

    @unittest.expectedFailure
    def test_latest_pgmetadata(self):
        """ Test read multiple remotes. """
        # There is 0.1.0 and 0.2.0 in these XML files
        self.assertEqual('0.2.0', self.remote.latest("PgMetadata"))
