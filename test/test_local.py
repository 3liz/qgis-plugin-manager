__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import unittest

from pathlib import Path

from qgis_plugin_manager.local_directory import LocalDirectory


class PluginManager(unittest.TestCase):

    def setUp(self) -> None:
        self.local = LocalDirectory(Path('fixtures/plugins'))

    def test_list_existing_plugins(self):
        """ Test to find existing plugins. """
        self.assertCountEqual(['plugin_a', 'plugin_b'], self.local.plugins())
        self.assertCountEqual(['missing_init', 'missing_metadata'], self.local.invalid)

    def test_read_metadata(self):
        self.assertIsNone(self.local.plugin_metadata('do_not_exist', 'author'))
        self.assertIsNone(self.local.plugin_metadata('missing_init', 'author'))
        self.assertIsNone(self.local.plugin_metadata('missing_metadata', 'author'))

        self.assertEqual('Hazel Nutt', self.local.plugin_metadata('plugin_a', 'author'))
        self.assertEqual('', self.local.plugin_metadata('plugin_a', 'do_not_exist'))

        self.assertCountEqual(
            ['Plugin A', '1.0.0', '', '3.0', '', 'Hazel Nutt'],
            self.local.plugin_all_info('plugin_a'))


if __name__ == '__main__':
    unittest.main()
