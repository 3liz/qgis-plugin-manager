__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import re
import shutil
import urllib
import urllib.request
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Union

from qgis_plugin_manager.definitions import Level, Plugin
from qgis_plugin_manager.utils import qgis_server_version, DEFAULT_QGIS_VERSION


class Remote:

    def __init__(self, folder: Path):
        """ Constructor. """
        self.folder = folder
        self.list = None
        self.list_plugins = None

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
                            f"Your https://plugins.qgis.org remote is not using dynamic QGIS version."
                            f"{Level.End}"
                        )
                        print(
                            f"Instead of\n{raw_line}"
                            f"\n"
                            f"you should have"
                            f"\n"
                            f"https://plugins.qgis.org/plugins/plugins.xml?qgis=[VERSION]"
                            f"\n"
                            f"If you can remove the file sources.list ? 'qgis-plugin-manager init' will "
                            f"regenerate it using dynamic QGIS version."
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
            shutil.rmtree(cache)
        cache.mkdir()

        for i, server in enumerate(self.list):
            print(f"Downloading {server}...")
            request = urllib.request.Request(server, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                f = urllib.request.urlopen(request)
            except urllib.error.HTTPError as e:
                print(f"\t{e}")
                continue

            filename = ""
            for x in server:
                if x.isalnum():
                    filename += x
                else:
                    filename += '-'

            filename = re.sub(r"\-+", "-", filename)
            # Binary mode does not support encoding parameter
            with open(Path(cache / f"{filename}.xml"), 'wb') as output:
                output.write(f.read())

            print(f"\t{Level.Success}Ok{Level.End}")

    def latest(self, plugin_name: str) -> Union[str, None]:
        """ For a given plugin, it returns the latest version found in all remotes. """
        # plugins is a dict : plugin_name : version
        plugins = {}
        self.list_plugins = {}

        cache = Path(self.folder / ".cache_qgis_plugin_manager")
        if not cache.exists():
            cache.mkdir()
            print("The 'update' has not been done before.")
            print("Running the update to download XML files first.")
            self.update()

        has_xml = False
        for file in cache.iterdir():
            if not file.name.endswith('.xml'):
                continue

            has_xml = True

            tree = ET.parse(file.absolute())
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
                        plugins[xml_plugin_name] = plugin.attrib['version']

                plugin_obj = Plugin()
                data = {}
                for element in plugin:
                    if element.tag in plugin_obj._fields:
                        data[element.tag] = element.text

                # Not present in XML, but property available in metadata.txt
                data['qgis_maximum_version'] = ''

                plugin_obj = Plugin(**data)
                self.list_plugins[xml_plugin_name] = plugin_obj

        if not has_xml:
            print(f"{Level.Warning}No remote repositories found !{Level.End}")
            return None

        return plugins.get(plugin_name)

    def install(self, plugin_name, version="latest") -> bool:
        """ Install the plugin with a specific version.

        Default version is latest.
        """
        xml_version = self.latest(plugin_name)
        if xml_version is None:
            print(f"{Level.Warning}Plugin {plugin_name} {version} not found.{Level.End}")
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

        zip_file = Path(self.folder / file_name)
        # Binary mode does not support encoding parameter
        with open(zip_file, 'wb') as output:
            output.write(f.read())

        existing = Path(self.folder / plugin_name)
        if existing.exists():
            shutil.rmtree(existing)

        import zipfile
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(self.folder)

        zip_file.unlink()

        print(f"\t{Level.Success}Ok {zip_file.name}{Level.End}")

        return True
