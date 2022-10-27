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

    def test_plugin_name_with_space_and_tags(self):
        """ Test plugin with different name, using tags. """
        self.remote = Remote(Path('fixtures/xml_files/dataplotly'))
        plugins = self.remote._parse_xml(Path('fixtures/xml_files/dataplotly/dataplotly.xml'), {})
        self.assertDictEqual({'Data Plotly': '0.4'}, plugins)

        self.assertEqual(1, len(self.remote.list_plugins))

        plugin = self.remote.list_plugins.get('Data Plotly')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, 'Data Plotly')
        self.assertEqual(plugin.tags, 'vector,python,d3,plots,graphs,datavis,dataplotly,dataviz')
        self.assertListEqual(
            plugin.search,
            [
                'data plotly', 'dataplotly', 'vector', 'python', 'd3', 'plots', 'graphs', 'datavis',
                'dataviz', 'data', 'plotly'
            ]
        )

        # Test the search
        self.assertListEqual([], self.remote.search("foo"))
        self.assertListEqual(['Data Plotly'], self.remote.search("dataviz", strict=False))
        self.assertListEqual(['Data Plotly'], self.remote.search("dataplotly", strict=False))

    def test_search_with_space_in_name(self):
        """ Test Lizmap should give 2 values : Lizmap and 'Lizmap server'. """
        self.remote = Remote(Path('fixtures/xml_files/lizmap'))
        plugins = self.remote._parse_xml(Path('fixtures/xml_files/lizmap/lizmap.xml'), {})
        self.assertEqual(2, len(self.remote.list_plugins))
        self.assertDictEqual(
            {
                'Lizmap': '3.7.4',
                'Lizmap server': '1.0.0',
            },
            plugins
        )

        plugin = self.remote.list_plugins.get('Lizmap server')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, 'Lizmap server')

        self.assertListEqual(
            plugin.search,
            ['lizmap server', 'lizmapserver', 'web', 'cloud', 'lizmap', 'server']
        )

        # Test the search
        self.assertListEqual(['Lizmap', 'Lizmap server'], self.remote.search("lizmap", strict=False))

    def test_qgis_dev_version(self):
        """ Test check QGIS dev version number. """
        self.assertListEqual(["3", "22", "11"], Remote.check_qgis_dev_version('3.22.11'))
        self.assertListEqual(["3", "24", "0"], Remote.check_qgis_dev_version('3.23.0'))

    @unittest.expectedFailure
    def test_latest_pgmetadata(self):
        """ Test read multiple remotes. """
        # There is 0.1.0 and 0.2.0 in these XML files
        self.assertEqual('0.2.0', self.remote.latest("PgMetadata"))
