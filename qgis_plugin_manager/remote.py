import base64
import os
import platform
import re
import shutil
import urllib
import urllib.request
import zipfile

from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlencode, urlparse, urlunparse
from xml.etree.ElementTree import parse

from semver import Version

from qgis_plugin_manager import echo
from qgis_plugin_manager.definitions import Plugin
from qgis_plugin_manager.utils import (
    PluginManagerError,
    similar_names,
    sources_file,
    to_bool,
)

PluginDict = Dict[str, Tuple[Plugin, ...]]


class PluginNotFoundError(PluginManagerError):
    pass


class Remote:
    def __init__(self, folder: Path, qgis_version: Optional[str] = None):
        """Constructor."""
        self.folder = folder
        self.list: List[str] = []
        self.setting_error = False
        self.qgis_version = qgis_version

        self._list_plugins: PluginDict = {}

        self.list_remote()

    def user_agent(self) -> str:
        """User agent."""
        # https://github.com/3liz/qgis-plugin-manager/issues/66
        # https://lists.osgeo.org/pipermail/qgis-user/2024-May/054439.html
        if not self.qgis_version:
            raise PluginManagerError("QGIS version required")
        else:
            qgis_version = self.qgis_version

        qgis_version = qgis_version.replace(".", "")
        return f"Mozilla/5.0 QGIS/{self.qgis_version}/{platform.system()}"

    def check_remote_cache(self) -> bool:
        """Return if the remote is ready to be parsed."""
        if to_bool(os.getenv("QGIS_PLUGIN_MANAGER_SKIP_SOURCES_FILE")):
            return True

        source_list = sources_file(self.folder)
        if not source_list.exists():
            if not self.setting_error:
                echo.critical(f"The {source_list.absolute()} file does not exist")
                echo.info("Use the 'init' command to create the file")
                self.setting_error = True
                return False

        cache = self.cache_directory()
        for server in self.list:
            filename = self.server_cache_filename(cache, server)

            if not filename.exists():
                if not self.setting_error:
                    echo.critical(
                        "The 'update' command has not been done before. "
                        f"The repository {server} has not been fetched before."
                    )
                    self.setting_error = True
                    return False

        return True

    def remote_list(self) -> list:
        return self.list

    def list_remote(self) -> list:
        """Return the list of remotes configured.

        The token [VERSION] is replaced by the current version X.YY
        """
        source_list = sources_file(self.folder)
        if not source_list.exists():
            return []

        qgis_version = self.check_qgis_dev_version(self.qgis_version)

        with source_list.open(encoding="utf8") as f:
            for line in f.readlines():
                raw_line = line.strip()
                if not raw_line:
                    # Empty line
                    continue

                if line.startswith("#"):
                    # Commented line
                    continue

                if "[VERSION]" in raw_line:
                    if not qgis_version:
                        echo.alert(
                            f"Skipping line '{raw_line}' because it has a "
                            "token [VERSION] but "
                            "no QGIS version could be detected."
                        )
                        continue

                    raw_line = raw_line.replace("[VERSION]", f"{qgis_version[0]}.{qgis_version[1]}")

                self.list.append(raw_line)

        return self.list

    def cache_directory(self) -> Path:
        """Return the cache directory.

        The default one, or the one defined by environment variable.
        """
        env_path = os.getenv("QGIS_PLUGIN_MANAGER_CACHE_DIR")
        if env_path:
            return Path(env_path)

        return Path(self.folder / ".cache_qgis_plugin_manager")

    def print_list(self):
        """Print in the console the list of remotes."""

        echo.echo("List of remotes :\n")
        if len(self.list):
            echo.echo("\n".join([self.public_remote_name(s) for s in self.list]))
        else:
            echo.alert("No remote configured")

    def latest(
        self,
        name: str,
        include_prerelease: bool = False,
        include_deprecated: bool = False,
    ) -> Optional[Plugin]:
        plugin = None
        for plugin in self.available_plugins().get(name, ()):
            if (plugin.version.prerelease or plugin.experimental) and not include_prerelease:
                continue
            elif plugin.deprecated and not include_deprecated:
                continue
            else:
                break
        return plugin

    def update(self) -> bool:
        """For each remote, it updates the XML file."""

        # Clear plugin list
        self._list_plugins = {}

        if not self.list:
            echo.critical("\tNo remote found.")
            return False

        cache = self.cache_directory()
        if cache.exists():
            try:
                shutil.rmtree(cache)
            except OSError as e:
                # https://github.com/3liz/qgis-plugin-manager/issues/53
                echo.critical(f"{e}")
                return False

        cache.mkdir()

        flag = False
        for server in self.list:
            echo.info(f"Downloading {self.public_remote_name(server)}…")
            url, login, password = self.credentials(server)
            headers = {
                "User-Agent": self.user_agent(),
            }
            if login:
                token = base64.b64encode(f"{login}:{password}".encode())
                headers["Authorization"] = f"Basic {token.decode()}"
            request = urllib.request.Request(url, headers=headers)
            try:
                f = urllib.request.urlopen(request)
            except urllib.error.HTTPError as e:
                echo.critical(f"ERROR: {e}")
                continue
            except urllib.error.URLError as e:
                echo.critical(f"ERROR: {e}")
                continue

            filename = self.server_cache_filename(cache, server)

            # Binary mode does not support encoding parameter
            try:
                with open(filename, "wb") as output:
                    output.write(f.read())
            except PermissionError:
                # https://github.com/3liz/qgis-plugin-manager/issues/53
                echo.critical("The directory is not writable.")
                return False

            echo.success("\tOk")
            flag = True

        return flag

    def xml_in_folder(self) -> List[Path]:
        """Returns the list of XML files in the folder."""
        cache = self.cache_directory()
        if not cache.exists():
            cache.mkdir()
            echo.info("No cache directory: please run the 'update' command")
            return []

        xml = []
        for xml_file in cache.iterdir():
            if not xml_file.name.endswith(".xml"):
                continue

            xml.append(xml_file)

        return xml

    def available_plugins(self) -> PluginDict:
        """Populates the list of available plugins, in all XML files."""
        if not self._list_plugins:
            for xml_file in self.xml_in_folder():
                self._parse_xml(xml_file, self._list_plugins)
        return self._list_plugins

    def _parse_xml(self, xml_file: Path, plugins: PluginDict):
        """Parse the given XML file."""

        tree = parse(xml_file.absolute())
        root = tree.getroot()
        for elem in root:
            plugin = Plugin.from_xml_element(elem)

            name = plugin.name
            versions = plugins.get(name)
            if versions:
                if plugin.version > versions[0].version:
                    plugins[name] = (plugin, *versions)
                elif plugin.version < versions[-1].version:
                    plugins[name] = (*versions, plugin)
                else:  # Need to sort
                    plugins[name] = tuple(
                        sorted(
                            (*versions, plugin),
                            key=lambda p: p.version,
                            reverse=True,
                        ),
                    )
            else:
                plugins[name] = (plugin,)

    def search(self, search_string: str, strict: bool = True) -> Iterator[str]:
        """Search in plugin names and tags."""
        # strict is used in tests to not check if the remote is ready
        if strict and not self.check_remote_cache():
            return

        self.available_plugins()

        results = set()
        for plugin_name, versions in self._list_plugins.items():
            found = plugin_name in results
            if not found:
                for plugin in versions:
                    if next(similar_names(search_string, plugin.search), None):
                        found = True
                        results.add(plugin_name)
                        break
                if found:
                    yield plugin_name

    def check_similar_names(self, name: str) -> Iterator[str]:
        yield from similar_names(name, self._list_plugins.keys())

    def install(
        self,
        plugin_name: str,
        version: Optional[str] = None,
        include_prerelease: bool = False,
        include_deprecated: bool = False,
        remove_zip: bool = True,
        fix_permissions: bool = False,
        plugin_folder: Optional[str] = None,
    ) -> str:
        """Install the plugin with a specific version.

        Default version is latest.
        """
        self.available_plugins()

        if not self.check_remote_cache():
            raise PluginManagerError("No remote data")

        if not self._list_plugins:
            raise PluginManagerError("No available plugins")

        plugin = None

        # Check for requested version otherwise get the latest
        if version:
            # Find version
            versions = self._list_plugins.get(plugin_name)
            if versions:
                requested_ver = Version.parse(version)
                plugin = next((p for p in versions if p.version == requested_ver), None)
        else:
            plugin = self.latest(
                plugin_name,
                include_prerelease,
                include_deprecated,
            )

        if not plugin:
            echo.alert(f"No matching plugin found for {plugin_name}.")
            raise PluginNotFoundError()

        url = plugin.download_url
        file_name = plugin.file_name

        # Check consistency
        if not file_name:
            raise PluginManagerError(f"Incomplete plugin data: file_name: {plugin})")

        if not url:
            raise PluginManagerError(f"Incomplete plugin data: url: {plugin})")

        echo.debug("Downloading {} from {}", file_name, url)
        zip_file = self._download_zip(url, plugin_name, file_name)

        # Removing existing plugin folder if needed
        if plugin_folder:
            existing = self.folder.joinpath(plugin_folder)
            if existing.exists():
                echo.debug(f"{plugin_name}: Removing existing installation: {existing}")
                try:
                    shutil.rmtree(existing)
                except OSError as e:
                    # https://github.com/3liz/qgis-plugin-manager/issues/53
                    zip_file.unlink()
                    raise PluginManagerError(f"{e}")

        if not zip_file.exists():
            raise PluginManagerError(
                f"The zip file does not exist : {zip_file.absolute()}",
            )
        # Extracting the zip in the folder
        echo.debug(f"Extracting {zip_file.name}")
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            zip_ref.extractall(self.folder)

        if remove_zip:
            # Removing the zip file
            zip_file.unlink()

        # Set permissions to 0644 for files, 0755 for directories
        if fix_permissions:
            echo.debug("Fixing files permissions to 0644")
            for p in self.folder.glob("**"):
                if p.is_dir():
                    p.chmod(0o755)
                else:
                    p.chmod(0o644)

        return str(plugin.version)

    def _download_zip(
        self,
        url: str,
        plugin_name: str,
        file_name: str,
    ) -> Path:
        """Download the ZIP"""
        if url.startswith("file:"):
            zip_file = Path(unquote(urlparse(url).path))
        else:
            headers = {
                "User-Agent": self.user_agent(),
            }
            request = urllib.request.Request(url, headers=headers)
            try:
                f = urllib.request.urlopen(request)
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    echo.debug("Authentication required")
                    for _, login, password in self.all_credentials():
                        # Hack to try all logins until we find the one working…
                        token = base64.b64encode(f"{login}:{password}".encode())
                        headers["Authorization"] = f"Basic {token.decode()}"

                        request = urllib.request.Request(url, headers=headers)
                        try:
                            f = urllib.request.urlopen(request)
                            break
                        except urllib.error.HTTPError:
                            continue
                    else:
                        raise PluginManagerError("Failed to download plugin")
                elif e.code == "404":
                    raise PluginManagerError("Plugin not found.")
                else:
                    raise PluginManagerError(f"Error downloading plugin: {e}")

            # Saving the zip from the URL
            zip_file = self.folder.joinpath(file_name)

            try:
                with open(zip_file, "wb") as output:
                    output.write(f.read())
            except PermissionError:
                file_path = self.folder.absolute()
                echo.critical(f"Cannot write to \t{file_path}")
                raise

        return zip_file

    @staticmethod
    def check_qgis_dev_version(qgis_version: Optional[str]) -> Optional[List[str]]:
        """Check if the QGIS current version is odd number."""
        if not qgis_version:
            return None

        qgis_version_info = qgis_version.split(".")
        if int(qgis_version_info[1]) % 2 != 0:
            echo.alert(
                f"A QGIS development version is detected : {qgis_version_info[0]}.{qgis_version_info[1]}."
            )
            qgis_version_info[1] = str(int(qgis_version_info[1]) + 1)
            echo.alert(f"If needed, it will use {qgis_version_info[0]}.{qgis_version_info[1]} instead.")
        return qgis_version_info

    @staticmethod
    def server_cache_filename(cache_folder: Path, server: str) -> Path:
        """Return the path for XML file."""
        server, login, _ = Remote.credentials(server)
        filename = ""
        for x in server:
            if x.isalnum():
                filename += x
            else:
                filename += "-"

        filename = re.sub(r"\-+", "-", filename)
        if login:
            filename += "-protected"
        return cache_folder.joinpath(f"{filename}.xml")

    @classmethod
    def credentials(cls, server: str) -> Tuple[str, str, str]:
        """Parse for login and password if needed."""
        u = urlparse(server)
        query = parse_qs(u.query, keep_blank_values=True)
        login = query.get("username", "")
        password = query.get("password", "")

        query.pop("username", None)
        query.pop("password", None)

        u = u._replace(query=urlencode(query, True))
        if login and password:
            return urlunparse(u), login[0], password[0]

        return urlunparse(u), "", ""

    def all_credentials(self) -> Iterator[Tuple[str, str, str]]:
        """Dirty hack to get all credentials for now…"""

        for server in self.list:
            url, login, password = self.credentials(server)
            yield url, login, password

    @classmethod
    def public_remote_name(cls, server: str) -> str:
        """Clean a URL from a password if needed."""
        u = urlparse(server)
        query = parse_qs(u.query, keep_blank_values=True)
        if "password" in query.keys():
            query["password"] = ["******"]
        u = u._replace(query=urlencode(query, True))
        return urlunparse(u)
