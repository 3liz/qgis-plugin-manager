__copyright__ = 'Copyright 2022, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import configparser
import os
import pwd
import stat

from pathlib import Path
from typing import Union, Dict

from qgis_plugin_manager.definitions import Level, Plugin

from .remote import Remote
from .utils import DEFAULT_QGIS_VERSION, parse_version, pretty_table


class LocalDirectory:

    def __init__(self, folder: Path, qgis_version: str = None):
        """ Constructor"""
        self.folder = folder
        # Dictionary : folder : plugin name
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
            print(f"{Level.Warning}sources.list already existing. Quit{Level.End}")
            return False

        if self.qgis_version:
            version = "[VERSION]"
            print("Init https://plugins.qgis.org")
        else:
            print(
                f"{Level.Warning}"
                f"QGIS version is unknown, creating with a default {DEFAULT_QGIS_VERSION}"
                f"{Level.End}"
            )
            version = DEFAULT_QGIS_VERSION

        server = f"https://plugins.qgis.org/plugins/plugins.xml?qgis={version}\n"

        with open(source_file, 'w', encoding='utf8') as f:
            f.write(server)

        return True

    def plugin_list(self) -> Dict[str, str]:
        """ Get the list of plugins installed in the current directory. """
        self._plugins = {}
        for folder in self.folder.iterdir():

            if not folder.is_dir():
                continue

            if folder.name.startswith('.'):
                continue

            have_python = list(folder.glob('*.py'))
            have_metadata = list(folder.glob('metadata.txt'))
            if have_python and have_metadata:
                name = self.plugin_metadata(folder.name, 'name')
                self._plugins[folder.name] = name
            else:
                self._invalid.append(folder.name)

        # Weird issue, there are duplicates
        self._invalid = list(dict.fromkeys(self._invalid))

        return self._plugins

    def plugin_metadata(self, plugin_folder: str, key: str) -> Union[str, None]:
        """ For a given plugin installed, get a metadata item. """
        if self._plugins is None:
            self.plugin_list()

        if plugin_folder not in self._plugins.keys():
            return None

        config_parser = configparser.ConfigParser()

        with Path(self.folder / Path(f"{plugin_folder}/metadata.txt")).open(encoding='utf8') as f:
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

    def plugin_info(self, plugin: str) -> Union[None, Plugin]:
        """ For a given plugin, retrieve all metadata."""
        if self._plugins is None:
            self.plugin_list()

        if plugin in self._plugins.keys():
            # It's plugin folder
            plugin_folder = plugin
        elif plugin not in self._plugins.values():
            # Not found, either as a plugin folder or plugin name
            return None
        else:
            # It's a plugin name
            plugin_folder = list(self._plugins.keys())[list(self._plugins.values()).index(plugin)][0]

        data = Plugin(
            name=self.plugin_metadata(plugin_folder, "name"),
            version=self.plugin_metadata(plugin_folder, "version"),
            experimental=self.plugin_metadata(plugin_folder, "experimental"),
            qgis_minimum_version=self.plugin_metadata(plugin_folder, "qgisMinimumVersion"),
            qgis_maximum_version=self.plugin_metadata(plugin_folder, "qgisMaximumVersion"),
            author_name=self.plugin_metadata(plugin_folder, "author"),
        )
        return data

    def print_table(self):
        """ Print all plugins installed as a table. """
        if self._plugins is None:
            self.plugin_list()

        remote = Remote(self.folder)

        print(f"List all plugins in {self.folder.absolute()}\n")
        headers = [
            'Folder', 'Name', 'Version', 'Experimental', 'QGIS min', 'QGIS max', 'Author',
            'Folder rights', 'Action ⚠', ]
        headers = [f"  {i}  " for i in headers]
        data = []
        for folder in self.plugin_list():
            # Folder
            plugin_data = [str(folder)]

            info = self.plugin_info(folder)

            # Name
            plugin_data.append(info.name)

            # Version
            plugin_data.append(info.version)

            # Experimental
            plugin_data.append('x' if info.experimental in ('True', 'true', '1') else '')

            # QGIS Min
            plugin_data.append(info.qgis_minimum_version)
            qgis_min = parse_version(info.qgis_minimum_version)

            # QGIS Max
            plugin_data.append(info.qgis_maximum_version)
            qgis_max = parse_version(info.qgis_maximum_version)

            # Author
            plugin_data.append(info.author_name)

            # Folder rights
            folder = self.folder.joinpath(folder)
            stat_info = os.stat(folder)
            perms = stat.S_IMODE(os.stat(folder).st_mode)
            plugin_data.append(f"{pwd.getpwuid(stat_info.st_uid)[0]} : {oct(perms)}")

            # Action
            latest = remote.latest(info.name)
            current = info.version

            extra_info = []

            if len(current.split('.')) == 1:
                extra_info.append("Not a semantic version")

            elif latest:
                if latest.startswith('v'):
                    latest = latest[1:]

                if latest > current:
                    extra_info.append(f"Upgrade to {latest}")

                if self.qgis_version and qgis_min:
                    if qgis_min > self.qgis_version:
                        extra_info.append(f"QGIS Minimum {info.qgis_minimum_version}")

                if self.qgis_version and qgis_max:
                    if qgis_max < self.qgis_version:
                        extra_info.append(f"QGIS Maximum {info.qgis_maximum_version}")

            else:
                extra_info.append('Unknown version')

            plugin_data.append(Level.Warning + ';'.join(extra_info) + Level.End)
            data.append(plugin_data)
        print(pretty_table(data, headers))

        if len(self._invalid) >= 1:
            print(pretty_table(self._invalid, ['Invalid']))
