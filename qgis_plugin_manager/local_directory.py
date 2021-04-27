import configparser

from pathlib import Path
from typing import List, Union

from .remote import Remote
from .utils import pretty_table


class LocalDirectory:

    def __init__(self, folder: Path):
        self.folder = folder
        self._plugins = None
        self._invalid = []

    def plugins(self) -> List[str]:
        self._plugins = []
        for folder in self.folder.iterdir():

            if not folder.is_dir():
                continue

            if folder.name.startswith('.'):
                continue

            have_python = list(folder.glob('**/*.py'))
            have_metadata = list(folder.glob('**/metadata.txt'))
            if have_python and have_metadata:
                self._plugins.append(folder.name)
            else:
                self._invalid.append(folder.name)

        return self._plugins

    def plugin_metadata(self, plugin: str, key: str) -> Union[str, None]:
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
        return self._invalid

    def plugin_all_info(self, plugin: str) -> Union[List[str], None]:
        if self._plugins is None:
            self.plugins()

        if plugin not in self._plugins:
            return None

        data = []
        for item in ("name", "version", "qgisMinimumVersion", "qgisMaximumVersion", "author"):
            data.append(self.plugin_metadata(plugin, item))
        return data

    def print_table(self):
        if self._plugins is None:
            self.plugins()

        remote = Remote(self.folder)

        print(f"List all plugins in {self.folder.absolute()}\n")
        headers = ['Name', 'Version', 'QGIS min', 'QGIS max', 'Author', 'Action']
        headers = [f"  {i}  " for i in headers]
        data = []
        for plugin in self.plugins():
            plugin_data = self.plugin_all_info(plugin)

            latest = remote.latest(plugin)
            current = plugin_data[1]

            if latest:
                if latest.startswith('v'):
                    latest = latest[1:]

                if latest > current:
                    plugin_data.append(f"Upgrade to {latest}")
                else:
                    plugin_data.append('')
            else:
                plugin_data.append('Unkowwn')
            data.append(plugin_data)
        print(pretty_table(data, headers))

        if len(self._invalid) >= 1:
            print(pretty_table(self._invalid, ['Invalid']))
