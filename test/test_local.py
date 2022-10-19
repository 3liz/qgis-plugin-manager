__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import unittest

from pathlib import Path

from qgis_plugin_manager.local_directory import LocalDirectory


class TestLocal(unittest.TestCase):

    def setUp(self) -> None:
        self.local = LocalDirectory(Path('fixtures/plugins'))

    def test_list_existing_plugins(self):
        """ Test to find existing plugins. """
        self.assertCountEqual(['plugin_a', 'plugin_b'], self.local.plugin_list())
        self.assertCountEqual(['missing_init', 'missing_metadata'], self.local.invalid)
        self.assertEqual(self.local.plugin_installed_version('Plugin A'), "1.0.0")
        self.assertIsNone(self.local.plugin_installed_version('Plugin Z'))

    def test_read_metadata(self):
        """ Test read metadata. """
        self.assertIsNone(self.local.plugin_metadata('do_not_exist', 'author'))
        self.assertIsNone(self.local.plugin_metadata('missing_init', 'author'))
        self.assertIsNone(self.local.plugin_metadata('missing_metadata', 'author'))

        self.assertEqual('Hazel Nutt', self.local.plugin_metadata('plugin_a', 'author'))
        self.assertEqual('', self.local.plugin_metadata('plugin_a', 'do_not_exist'))

        # Plugin A
        plugin = self.local.plugin_info('plugin_a')
        self.assertEqual('Plugin A', plugin.name)
        self.assertEqual('1.0.0', plugin.version)
        self.assertEqual('', plugin.experimental)
        self.assertEqual('3.0', plugin.qgis_minimum_version)
        self.assertEqual('', plugin.qgis_maximum_version)
        self.assertEqual('Hazel Nutt', plugin.author_name)
        self.assertTrue(plugin.server)
        self.assertTrue(plugin.has_processing)
        self.assertFalse(plugin.deprecated)

        # Plugin B
        plugin = self.local.plugin_info('plugin_b')
        self.assertFalse(plugin.server)
        self.assertFalse(plugin.has_processing)
        self.assertFalse(plugin.deprecated)


if __name__ == '__main__':
    unittest.main()
