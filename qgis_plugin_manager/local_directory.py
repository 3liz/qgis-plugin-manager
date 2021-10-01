__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import configparser

from pathlib import Path
from typing import List, Union

from .remote import Remote
from .utils import parse_version, pretty_table

DEFAULT_QGIS_VERSION = "3.16"


class LocalDirectory:

    def __init__(self, folder: Path, qgis_version: str = None):
        """ Constructor"""
        self.folder = folder
        self._plugins = None
        self._invalid = []

        self.qgis_version = None
        if qgis_version:
            self.qgis_version = qgis_version.split('.')
            if len(self.qgis_version) != 3:
                self.qgis_version = None
            else:
                self.qgis_version = [int(i) for i in self.qgis_version]

    def init(self) -> bool:
        """ Init this qgis-plugin-manager by creating the default sources.list."""
        source_file = self.folder.joinpath('sources.list')
        if source_file.exists():
            print("sources.list already existing. Quit")
            return False

        if self.qgis_version:
            version = f"{self.qgis_version[0]}.{self.qgis_version[1]}"
            print(f"Init https://plugins.qgis.org with {version}")
        else:
            print(f"QGIS version is unknown, creating with a default {DEFAULT_QGIS_VERSION}")
            version = DEFAULT_QGIS_VERSION

        server = f"https://plugins.qgis.org/plugins/plugins.xml?qgis={version}\n"

        with open(source_file, 'w', encoding='utf8') as f:
            f.write(server)

        return True

    def plugins(self) -> List[str]:
        """ Get the list of plugins installed in the current directory. """
        self._plugins = []
        for folder in self.folder.iterdir():

            if not folder.is_dir():
                continue

            if folder.name.startswith('.'):
                continue

            have_python = list(folder.glob('*.py'))
            have_metadata = list(folder.glob('metadata.txt'))
            if have_python and have_metadata:
                self._plugins.append(folder.name)
            else:
                self._invalid.append(folder.name)

        # Weird issue, there are duplicates
        self._invalid = list(dict.fromkeys(self._invalid))

        return self._plugins

    def plugin_metadata(self, plugin: str, key: str) -> Union[str, None]:
        """ For a given plugin installed, get a metadata item. """
        if self._plugins is None:
            self.plugins()

        if plugin not in self._plugins:
            return None

        config_parser = configparser.ConfigParser()

        with Path(self.folder / Path(f"{plugin}/metadata.txt")).open() as f:
            config_parser.read_file(f)

        try:
            return config_parser.get('general', key)
        except configparser.NoOptionError:
            return ''

    @property
    def invalid(self) -> list:
        """ List of invalid plugins.

        Maybe not a valid folder ? No metadata.txt ?
        """
        return self._invalid

    def plugin_all_info(self, plugin: str) -> Union[List[str], None]:
        """ For a given plugin, retrieve all metadata."""
        if self._plugins is None:
            self.plugins()

        if plugin not in self._plugins:
            return None

        data = []
        for item in ("name", "version", "experimental", "qgisMinimumVersion", "qgisMaximumVersion", "author"):
            value = self.plugin_metadata(plugin, item)
            if item == "experimental":
                value = 'x' if value in ['True', 'true'] else ''
            data.append(value)
        return data

    def print_table(self):
        """ Print all plugins installed as a table. """
        if self._plugins is None:
            self.plugins()

        remote = Remote(self.folder)

        print(f"List all plugins in {self.folder.absolute()}\n")
        headers = ['Name', 'Version', 'Experimental', 'QGIS min', 'QGIS max', 'Author', 'Action ⚠']
        headers = [f"  {i}  " for i in headers]
        data = []
        for plugin in self.plugins():
            plugin_data = self.plugin_all_info(plugin)

            latest = remote.latest(plugin)
            current = plugin_data[1]

            qgis_min = parse_version(plugin_data[3])
            qgis_max = parse_version(plugin_data[4])
            extra_info = []

            if latest:
                if latest.startswith('v'):
                    latest = latest[1:]

                if latest > current:
                    extra_info.append(f"Upgrade to {latest}")

                if self.qgis_version and qgis_min:
                    if qgis_min > self.qgis_version:
                        extra_info.append(f"QGIS Minimum {plugin_data[3]}")

                if self.qgis_version and qgis_max:
                    if qgis_max < self.qgis_version:
                        extra_info.append(f"QGIS Maximum {plugin_data[4]}")

            else:
                extra_info.append('Unknown version')

            plugin_data.append(';'.join(extra_info))
            data.append(plugin_data)
        print(pretty_table(data, headers))

        if len(self._invalid) >= 1:
            print(pretty_table(self._invalid, ['Invalid']))
