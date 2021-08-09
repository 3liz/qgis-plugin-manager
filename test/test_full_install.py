__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import os
import shutil
import unittest

from pathlib import Path

from qgis_plugin_manager.local_directory import LocalDirectory
from qgis_plugin_manager.remote import Remote


@unittest.skipIf(os.getenv('CI') != 'true', "Only run on CI")
class FullInstallNetwork(unittest.TestCase):

    def setUp(self) -> None:
        self.plugin_name = 'QuickOSM'
        self.repository = "https://plugins.qgis.org/plugins/plugins.xml?qgis=3.10"
        self.directory = Path('fixtures/plugins')
        self.remote = Remote(self.directory)
        self.local = LocalDirectory(self.directory)

        self.plugin_path = Path(self.directory / self.plugin_name)
        if self.plugin_path.exists():
            shutil.rmtree(self.plugin_path)

        shutil.copy(Path(self.directory / 'sources.list'), Path(self.directory / 'sources.list.back'))

    def tearDown(self) -> None:
        if self.plugin_path.exists():
            shutil.rmtree(self.plugin_path)

        shutil.copy(Path(self.directory / 'sources.list.back'), Path(self.directory / 'sources.list'))

    def test_install_network(self):

        self.assertFalse(Path(self.directory / 'QuickOSM').exists())
        self.assertNotIn(self.plugin_name, self.local.plugins())

        with open(Path(self.directory / 'sources.list'), 'w') as file:
            file.write(self.repository)

        self.remote.update()

        version = '1.1.1'
        self.remote.install(self.plugin_name, version)
        self.assertTrue(Path(self.directory / 'QuickOSM').exists())
        self.local.plugins()
        self.assertEqual(version, self.local.plugin_metadata(self.plugin_name, 'version'))

        self.remote.install(self.plugin_name)
        self.assertTrue(Path(self.directory / 'QuickOSM').exists())
        self.assertNotEqual(version, self.local.plugin_metadata(self.plugin_name, 'version'))
