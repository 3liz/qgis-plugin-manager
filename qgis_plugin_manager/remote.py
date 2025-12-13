import base64
import os
import platform
import re
import shutil
import urllib
import urllib.request
import zipfile

from pathlib import Path
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)
from urllib.parse import parse_qs, unquote, urlencode, urlparse, urlunparse
from xml.etree.ElementTree import parse

from semver import Version

from qgis_plugin_manager import echo
from qgis_plugin_manager.definitions import Plugin
from qgis_plugin_manager.utils import (
    PluginManagerError,
    get_semver_version,
    similar_names,
    sources_file,
)

PluginDict = Dict[str, Tuple[Plugin, ...]]


class PluginNotFoundError(PluginManagerError):
    pass


class PluginVersionNotFoundError(PluginManagerError):
    pass


class SourcesNotFoundError(PluginManagerError):
    pass


DEFAULT_SOURCE_URL = "https://plugins.qgis.org/plugins/plugins.xml?qgis={version}"


class Remote:
    def __init__(self, folder: Path, qgis_version: Optional[str] = None):
        """Constructor."""
        self.folder = folder
        self.list: List[str] = []
        self.qgis_version = qgis_version

        self._list_plugins: PluginDict = {}

        self.list_remote()

    @staticmethod
    def create_sources_file(folder: Path, qgis_version: Optional[str]) -> bool:
        """Init this qgis-plugin-manager by creating the default sources.list."""
        source_file = sources_file(folder)
        if source_file.exists():
            echo.alert(f"{source_file.absolute()} is already existing. Quit")
            return False

        if qgis_version:
            try:
                ver = get_semver_version(qgis_version)
                version = f"{ver.major}.{ver.minor}"
            except ValueError:
                raise PluginManagerError(f"{qgis_version} is not a valid QGIS version") from None
        else:
            version = "[VERSION]"

        server = os.getenv(
            "QGIS_PLUGIN_MANAGER_DEFAULT_SOURCE_URL",
            DEFAULT_SOURCE_URL,
        ).format(version=version)

        try:
            with open(source_file, "w", encoding="utf8") as f:
                print(server, file=f)
        except PermissionError:
            # https://github.com/3liz/qgis-plugin-manager/issues/53
            echo.critical("The directory is not writable.")
            return False

        echo.info(f"{source_file.absolute()} has been written.")
        return True

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
                            f"Skipping source '{raw_line}' because it has a "
                            "token [VERSION] but "
                            "no QGIS version could be detected.\n"
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

        return self.folder.joinpath(".cache_qgis_plugin_manager")

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
        *,
        qgis_version: Optional[Union[str, Version]] = None,
    ) -> Optional[Plugin]:
        if qgis_version and isinstance(qgis_version, str):
            qgis_version = get_semver_version(qgis_version)

        plugin = None
        for plugin in self.available_plugins().get(name, ()):
            if plugin.is_pre() and not include_prerelease:
                continue
            elif plugin.deprecated and not include_deprecated:
                continue
            elif qgis_version is not None and not plugin.check_qgis_version(qgis_version):
                continue
            else:
                break
        else:
            plugin = None
        return plugin

    def update(self):
        """For each remote, it updates the XML file."""

        # Clear plugin list
        self._list_plugins = {}

        if not self.list:
            raise SourcesNotFoundError()

        cache = self.cache_directory()
        if cache.exists():
            shutil.rmtree(cache)

        cache.mkdir()

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

            with open(filename, "wb") as output:
                output.write(f.read())

            echo.success("\tOk")

    def plugin_collection_files(self) -> Iterator[Tuple[str, Path]]:
        """Returns the list of plugins XML file in the cache folder."""
        cache = self.cache_directory()
        for source in self.list:
            coll = self.server_cache_filename(cache, source)
            if not coll.exists():
                raise PluginManagerError(
                    f"File cache missing for source: {source}\nPlease run the 'update' command"
                )
            yield source, coll

    def available_plugins(self) -> PluginDict:
        """Populates the list of available plugins, in all XML files."""
        if not self._list_plugins:
            if not self.list:
                raise SourcesNotFoundError()
            for source, xml_file in self.plugin_collection_files():
                self._parse_xml(xml_file, self._list_plugins, source)
        return self._list_plugins

    def _parse_xml(self, xml_file: Path, plugins: PluginDict, source: Optional[str] = None):
        """Parse the given XML file."""

        # IMPORTANT
        # The qgis index usually only show the latest experimental
        # and stable versions of the a plugin
        # Then you cannot rely on it for checking intermediate versions

        tree = parse(xml_file.absolute())
        root = tree.getroot()
        for elem in root:
            plugin = Plugin.from_xml_element(elem, source)

            name = plugin.name

            # Check consistency
            if not plugin.file_name:
                echo.critical(f"Incomplete plugin data for'{name}': file_name")
                continue

            if not plugin.download_url:
                echo.critical(f"Incomplete plugin data for '{name}': url")
                continue

            versions = plugins.get(name)
            if versions:
                # Store as decreasing version order (latest first)
                if plugin.version < versions[-1].version:
                    plugins[name] = (*versions, plugin)
                elif plugin.version > versions[0].version:
                    plugins[name] = (plugin, *versions)
                else:  # Need to sort
                    for i, p in enumerate(versions):
                        if plugin.version > p.version:
                            plugins[name] = (*versions[:i], plugin, *versions[i:])
                            break
                        elif plugin.version == p.version:
                            # SEMVER does not take build into account
                            # but here build are meaningfull because QGIS
                            # plugin version does not stick to SEMVER scheme
                            #
                            # Use lexicographic comparison
                            if (plugin.version.build or "") > (p.version.build or ""):
                                plugins[name] = (*versions[:i], plugin, *versions[i:])
                                break
                    else:
                        plugins[name] = (*versions, plugin)
            else:
                plugins[name] = (plugin,)

    def search(
        self,
        search_string: str,
        predicat: Optional[Callable[[Plugin], bool]] = None,
        latest: bool = False,
    ) -> Iterator[Plugin]:
        """Search in plugin names and tags."""
        self.available_plugins()

        for plugin_name, versions in self._list_plugins.items():
            for plugin in versions:
                if predicat is not None and not predicat(plugin):
                    continue
                if next(similar_names(search_string, plugin.search), None):
                    yield plugin
                    break
                if latest:  # Don't look at previous versions
                    break

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

        plugin = None
        # Check for requested version otherwise get the latest
        if version:
            # Find version
            # NOTE that the index file may not contains all versions
            # available !!!!!
            versions = self._list_plugins.get(plugin_name)
            if versions:
                try:
                    requested_ver = get_semver_version(version)
                    plugin = next((p for p in versions if p.version == requested_ver), None)
                except ValueError:
                    # Not a semver version
                    echo.debug(
                        f"{version} cannot be turned into SemVer compatible version"
                        f"Using the the literal requested version for download"
                    )
                    pass

                # Build a download URL from the latest version
                # XXX This is a best effort for getting a specific version
                # This may no works when using versions splitted accross
                # several repositories
                latest = versions[0]
                url = latest.download_url.replace(  # type: ignore [union-attr]
                    latest.version_str, version
                )
                file_name = latest.file_name.replace(  # type: ignore [union-attr]
                    latest.version_str, version
                )
                version_str = version
            else:
                raise PluginNotFoundError()
        else:
            plugin = self.latest(
                plugin_name,
                include_prerelease,
                include_deprecated,
            )

            if not plugin:
                raise PluginNotFoundError()

            version_str = plugin.version_str

            url = plugin.download_url
            file_name = plugin.file_name

        echo.debug("Downloading {} from {}", file_name, url)
        zip_file = self._download_zip(url, plugin_name, file_name, version_str)

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

        return version_str

    def _download_zip(
        self,
        url: str,
        plugin_name: str,
        file_name: str,
        version_str: str,
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
                elif e.code == 404:
                    raise PluginVersionNotFoundError(version_str)
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
        filename = "".join(x if x.isalnum() else "-" for x in server)
        filename = re.sub(r"\-+", "-", filename)
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
