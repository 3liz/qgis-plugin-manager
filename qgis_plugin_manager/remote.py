__copyright__ = 'Copyright 2022, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import os
import re
import shutil
import urllib
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Union

from qgis_plugin_manager.definitions import Level, Plugin
from qgis_plugin_manager.utils import (
    DEFAULT_QGIS_VERSION,
    current_user,
    qgis_server_version,
)


class Remote:

    def __init__(self, folder: Path):
        """ Constructor. """
        self.folder = folder
        self.list = None
        self.list_plugins = None
        self.setting_error = False

    def remote_is_ready(self) -> bool:
        """ Return if the remote is ready to be parsed. """
        source_list = Path(self.folder / 'sources.list')
        if not source_list.exists():
            if not self.setting_error:
                print(f"{Level.Critical}The sources.list file does not exist{Level.End}")
                print("Use the 'init' command to create the file")
                self.setting_error = True
                return False

        if self.list is None:
            self.remote_list()

        cache = Path(self.folder / ".cache_qgis_plugin_manager")
        for server in self.list:
            filename = self.server_cache_filename(cache, server)

            if not filename.exists():
                if not self.setting_error:
                    print(
                        f"{Level.Critical}"
                        f"The 'update' command has not been done before. "
                        f"The repository {server} has not been fetched before."
                        f"{Level.End}"
                    )
                    self.setting_error = True
                    return False

        return True

    def remote_list(self) -> list:
        """Return the list of remotes configured.

        The token [VERSION] is replaced by the current version X.YY
        """
        self.list = []
        source_list = Path(self.folder / 'sources.list')
        if not source_list.exists():
            return []

        qgis_version = qgis_server_version()
        if not qgis_version:
            qgis_version = DEFAULT_QGIS_VERSION

        qgis_version = qgis_version.split('.')

        with source_list.open(encoding='utf8') as f:
            for line in f.readlines():
                if not line.startswith('#'):
                    raw_line = line.strip()
                    if raw_line.startswith("https://plugins.qgis.org") and "[VERSION]" not in raw_line:
                        print(
                            f"{Level.Warning}"
                            f"Your https://plugins.qgis.org remote is not using a dynamic QGIS version."
                            f"{Level.End}"
                        )
                        print(
                            f"Instead of\n'{raw_line}'"
                            f"\nin your 'sources.list' file, you should have"
                            f"\n"
                            f"'https://plugins.qgis.org/plugins/plugins.xml?qgis=[VERSION]'"
                            f"\n\n"
                            f"Can you remove the file sources.list ? 'qgis-plugin-manager init' will "
                            f"regenerate it using dynamic QGIS version if QGIS is well configured.\n"
                            f"This just warning, the process will continue with the hardcoded QGIS version."
                            f"\n\n"
                        )

                    raw_line = raw_line.replace("[VERSION]", f"{qgis_version[0]}.{qgis_version[1]}")
                    self.list.append(raw_line)

        return self.list

    def print_list(self):
        """ Print in the console the list of remotes. """
        if self.list is None:
            self.remote_list()

        print("List of remotes :\n")
        if len(self.list):
            print('\n'.join(self.list))
        else:
            print(f"{Level.Warning}No remote configured{Level.End}")

    def update(self):
        """ For each remote, it updates the XML file. """
        if self.list is None:
            self.remote_list()

        cache = Path(self.folder / ".cache_qgis_plugin_manager")
        if cache.exists():
            try:
                shutil.rmtree(cache)
            except OSError as e:
                print(f"\t{Level.Critical}{e}{Level.End}")
                return

        cache.mkdir()

        for i, server in enumerate(self.list):
            print(f"Downloading {server}...")
            request = urllib.request.Request(server, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                f = urllib.request.urlopen(request)
            except urllib.error.HTTPError as e:
                print(f"\t{e}")
                continue

            filename = self.server_cache_filename(cache, server)

            # Binary mode does not support encoding parameter
            with open(filename, 'wb') as output:
                output.write(f.read())

            print(f"\t{Level.Success}Ok{Level.End}")

    def xml_in_folder(self) -> List[Path]:
        """ Returns the list of XML files in the folder. """
        if not self.remote_is_ready():
            return []

        cache = Path(self.folder / ".cache_qgis_plugin_manager")
        if not cache.exists():
            cache.mkdir()
            print("The 'update' has not been done before.")
            print("Running the update to download XML files first.")
            self.update()

        xml = []
        for xml_file in cache.iterdir():
            if not xml_file.name.endswith('.xml'):
                continue

            xml.append(xml_file)

        return xml

    def available_plugins(self) -> Dict:
        """ Populates the list of available plugins, in all XML files. """
        plugins = {}
        for xml_file in self.xml_in_folder():
            plugins = self._parse_xml(xml_file, plugins)
        return plugins

    def latest(self, plugin_name: str) -> Union[str, None]:
        """ For a given plugin, it returns the latest version found in all remotes. """
        return self.available_plugins().get(plugin_name)

    def _parse_xml(self, xml_file: Path, plugins: Dict) -> Dict:
        """ Parse the given XML file. """
        if self.list_plugins is None:
            # Maybe only in tests
            self.list_plugins = {}

        tree = ET.parse(xml_file.absolute())
        root = tree.getroot()
        for plugin in root:

            experimental = False
            for element in plugin:
                if element.tag == 'experimental':
                    experimental = element.text == "True"

            xml_plugin_name = plugin.attrib['name']
            if xml_plugin_name in plugins.keys():
                previous_parsed_version = plugins[xml_plugin_name].split('.')
                new_parsed_version = plugin.attrib['version'].split('.')
                if previous_parsed_version < new_parsed_version and not experimental:
                    plugins[xml_plugin_name] = plugin.attrib['version']
                else:
                    continue
            else:
                if not experimental:
                    # Not sure about this one, fixme
                    plugins[xml_plugin_name] = plugin.attrib['version']
                else:
                    plugins[xml_plugin_name] = plugin.attrib['version']

            plugin_obj = Plugin()
            data = {}
            for element in plugin:
                if element.tag in plugin_obj._fields:
                    data[element.tag] = element.text

            # Add the real name of the plugin
            data['name'] = plugin.attrib['name']

            # Not present in XML, but property available in metadata.txt
            data['qgis_maximum_version'] = ''

            # Add more search fields
            if data.get('tags'):
                tags = data['tags'].split(',')
            else:
                tags = []

            search_text = [
                xml_plugin_name.lower(),
                xml_plugin_name.lower().replace(" ", ""),
            ]
            search_text.extend(tags)
            search_text.extend(plugin.attrib['name'].lower().split(" "))

            # Remove duplicates
            data['search'] = list(dict.fromkeys(search_text))

            plugin_obj = Plugin(**data)
            self.list_plugins[xml_plugin_name] = plugin_obj
        return plugins

    def similar_names(self, plugin_name_wanted: str) -> List[str]:
        """ Return a list of similar plugin name found in the XML file. """
        similar = []
        plugin_name_wanted = plugin_name_wanted.lower()
        for plugin_name in self.list_plugins.keys():
            ratio = SequenceMatcher(None, plugin_name_wanted, plugin_name.lower()).ratio()
            if ratio > 0.8:
                similar.append(plugin_name)

        return similar

    def search(self, search_string: str, strict=True) -> List:
        """ Search in plugin names and tags."""
        # strict is used in tests to not check if the remote is ready
        if strict and not self.remote_is_ready():
            return []

        if self.list is None:
            self.remote_list()

        results = []

        if self.list_plugins is None:
            self.available_plugins()

        for plugin_name, plugin in self.list_plugins.items():
            for item in plugin.search:
                ratio = SequenceMatcher(None, search_string.lower(), item.lower()).ratio()
                if ratio > 0.8 and plugin_name not in results:
                    results.append(plugin_name)

        return results

    def install(self, plugin_name, version="latest") -> bool:
        """ Install the plugin with a specific version.

        Default version is latest.
        """
        if not self.remote_is_ready():
            return False

        xml_version = self.latest(plugin_name)
        if xml_version is None:
            print(f"{Level.Warning}Plugin {plugin_name} {version} not found.{Level.End}")
            similarity = self.similar_names(plugin_name)
            if similarity:
                for plugin in similarity:
                    print(f"Do you mean maybe '{plugin}' ?")
            return False

        print(f"Installation {plugin_name} {version}")

        url = self.list_plugins[plugin_name].download_url
        file_name = self.list_plugins[plugin_name].file_name

        if version != 'latest':
            actual = self.list_plugins[plugin_name].version
            url = url.replace(actual, version)
            file_name = file_name.replace(actual, version)

        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            f = urllib.request.urlopen(request)
        except urllib.error.HTTPError:
            print(f"{Level.Warning}Plugin {plugin_name} {version} not found.{Level.End}")
            return False

        # Get current users
        sudo_user = os.environ.get('SUDO_USER')
        user = current_user()

        # Saving the zip from the URL
        zip_file = Path(self.folder / file_name)
        try:
            # Binary mode does not support encoding parameter
            with open(zip_file, 'wb') as output:
                output.write(f.read())
        except PermissionError:
            file_path = self.folder.absolute()
            print(f"\t{Level.Critical}Current user {user} can not write in {file_path}{Level.End}")
            print("Check file permissions for the folder.")
            return False

        # Removing existing plugin folder if needed
        existing = Path(self.folder / plugin_name)
        if existing.exists():
            try:
                shutil.rmtree(existing)
            except OSError as e:
                print(f"\t{Level.Critical}{e}{Level.End}")
                zip_file.unlink()
                return False

        # Extracting the zip in the folder
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(self.folder)

        # Removing the zip file
        zip_file.unlink()

        print(f"\t{Level.Success}Ok {zip_file.name}{Level.End}")

        # Installation done !
        if sudo_user:
            print(f"Installed with super user '{user}' instead of '{sudo_user}'")
        else:
            print(f"Installed with user '{user}'")
        print("Please check file permissions and owner according to the user running QGIS Server.")
        return True

    @staticmethod
    def server_cache_filename(cache_folder, server) -> Path:
        """ Return the path for XML file. """
        filename = ""
        for x in server:
            if x.isalnum():
                filename += x
            else:
                filename += '-'

        filename = re.sub(r"\-+", "-", filename)
        return Path(cache_folder / f"{filename}.xml")
