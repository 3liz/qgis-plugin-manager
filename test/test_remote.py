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
        self.remote._parse_xml(Path('fixtures/xml_files/lizmap/lizmap.xml'), {})
        self.assertListEqual(['Lizmap'], self.remote.similar_names('lizmap'))

    def test_plugin_name_with_space_and_tags(self):
        """ Test plugin with different name, using tags. """
        self.remote = Remote(Path('fixtures/xml_files/dataplotly'))
        plugins = self.remote._parse_xml(Path('fixtures/xml_files/dataplotly/dataplotly.xml'), {})
        self.assertEqual(1, len(self.remote.list_plugins))
        plugin = self.remote.list_plugins.get('Data Plotly')
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, 'Data Plotly')
        self.assertDictEqual({'Data Plotly': '0.4'}, plugins)
        self.assertEqual(plugin.tags, 'vector,python,d3,plots,graphs,datavis,dataplotly,dataviz')
        self.assertListEqual(
            plugin.search,
            ['data plotly', 'dataplotly', 'vector', 'python', 'd3', 'plots', 'graphs', 'datavis', 'dataviz']
        )

        # Test the search
        self.assertListEqual([], self.remote.search("foo"))
        self.assertListEqual(['Data Plotly'], self.remote.search("dataviz"))
        self.assertListEqual(['Data Plotly'], self.remote.search("dataplotly"))

    @unittest.expectedFailure
    def test_latest_pgmetadata(self):
        """ Test read multiple remotes. """
        # There is 0.1.0 and 0.2.0 in these XML files
        self.assertEqual('0.2.0', self.remote.latest("PgMetadata"))
