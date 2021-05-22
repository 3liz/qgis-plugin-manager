import re
import shutil
import urllib
import urllib.request
import xml.etree.ElementTree as ET

from pathlib import Path

from qgis_plugin_manager.definitions import Plugin


class Remote:

    def __init__(self, folder: Path):
        self.folder = folder
        self.list = None
        self.list_plugins = None

    def remote_list(self) -> list:
        self.list = []
        source_list = Path(self.folder / 'sources.list')
        if not source_list.exists():
            return []

        with source_list.open() as f:
            for line in f.readlines():
                if not line.startswith('#'):
                    self.list.append(line.strip())
        return self.list

    def print_list(self):
        if self.list is None:
            self.remote_list()

        print("List of remotes :\n")
        print('\n'.join(self.list))

    def update(self):
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
            with open(Path(cache / f"{filename}.xml"), 'wb') as output:
                output.write(f.read())

            print("\tOk")

    def latest(self, plugin_name):
        plugins = {}
        self.list_plugins = {}

        cache = Path(self.folder / ".cache_qgis_plugin_manager")
        for file in cache.iterdir():
            if not file.name.endswith('.xml'):
                continue

            tree = ET.parse(file.absolute())
            root = tree.getroot()
            for plugin in root:

                xml_plugin_name = plugin.attrib['name']
                if xml_plugin_name in plugins.keys():
                    previous_parsed_version = plugins[xml_plugin_name].split('.')
                    new_parsed_version = plugin.attrib['version'].split('.')
                    if previous_parsed_version < new_parsed_version:
                        plugins[xml_plugin_name] = plugin.attrib['version']
                    else:
                        continue
                else:
                    plugins[xml_plugin_name] = plugin.attrib['version']

                plugin_obj = Plugin()
                data = {}
                for element in plugin:
                    if element.tag in plugin_obj._fields:
                        data[element.tag] = element.text

                plugin_obj = Plugin(**data)
                self.list_plugins[xml_plugin_name] = plugin_obj

        return plugins.get(plugin_name)

    def install(self, plugin_name, version="latest"):
        print(f"Installation {plugin_name} {version}")

        xml_version = self.latest(plugin_name)
        if xml_version is None:
            return

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
            print(f"Plugin {plugin_name} {version} not found.")
            return

        zip_file = Path(self.folder / file_name)
        with open(zip_file, 'wb') as output:
            output.write(f.read())

        existing = Path(self.folder / plugin_name)
        if existing.exists():
            shutil.rmtree(existing)

        import zipfile
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(self.folder)

        zip_file.unlink()

        print(f"\tOk {zip_file.name}")
