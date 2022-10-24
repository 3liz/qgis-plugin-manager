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
        """ Test install QuickOSM with a specific version, remove and try the latest. """
        self.assertFalse(Path(self.directory / 'QuickOSM').exists())
        self.assertNotIn(self.plugin_name, self.local.plugin_list())

        with open(Path(self.directory / 'sources.list'), 'w', encoding='utf8') as file:
            file.write(self.repository)

        self.remote.update()

        version = '1.1.1'
        self.remote.install(self.plugin_name, version)
        self.assertTrue(Path(self.directory / 'QuickOSM').exists())
        self.local.plugin_list()
        self.assertEqual(version, self.local.plugin_metadata(self.plugin_name, 'version'))

        self.remote.install(self.plugin_name)
        self.assertTrue(Path(self.directory / 'QuickOSM').exists())
        self.assertNotEqual(version, self.local.plugin_metadata(self.plugin_name, 'version'))


class FullInstallLocal(unittest.TestCase):

    def tearDown(self) -> None:
        destination = Path('fixtures/xml_files/file_protocol/minimal_plugin')
        if destination.exists():
            shutil.rmtree(destination)

        cache_folder = Path('fixtures/xml_files/file_protocol/.cache_qgis_plugin_manager')
        if cache_folder.exists():
            shutil.rmtree(cache_folder)

        sources_list = Path('fixtures/xml_files/file_protocol/sources.list')
        if sources_list.exists():
            sources_list.unlink()

    def test_install_local(self):
        """ Test install local file. """
        folder = Path('fixtures/xml_files/file_protocol/')
        folder.joinpath('sources.list').touch()
        folder.joinpath('.cache_qgis_plugin_manager').mkdir(parents=True, exist_ok=True)
        shutil.copy(
            folder.joinpath('plugin.xml'),
            folder.joinpath('.cache_qgis_plugin_manager/plugins.xml')
        )

        remote = Remote(folder)
        plugins = remote._parse_xml(folder.joinpath('plugin.xml'), {})
        self.assertDictEqual({'Minimal': '1.0.0'}, plugins)
        remote.list_plugins = plugins
        local = LocalDirectory(folder)
        self.assertIsNone(local.plugin_installed_version('Minimal'))
        remote.install("Minimal", remove_zip=False)
        self.assertEqual(local.plugin_installed_version('Minimal'), "1.0")
        self.assertTrue('minimal_plugin' in list(local.plugin_list().keys()))

        # Test to remove the plugin
        self.assertFalse(local.remove("minimal"))
        self.assertTrue(local.remove("Minimal"))
        self.assertIsNone(local.plugin_installed_version('Minimal'))
