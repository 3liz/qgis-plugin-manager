import configparser
import os
import shutil
import stat
import sys

from pathlib import Path
from typing import Dict, List, Optional

from qgis_plugin_manager import echo
from qgis_plugin_manager.definitions import Plugin
from qgis_plugin_manager.remote import Remote
from qgis_plugin_manager.utils import (
    PluginManagerError,
    get_default_remote_repository,
    parse_version,
    pretty_table,
    similar_names,
    sources_file,
    to_bool,
)


class LocalDirectory:
    def __init__(self, folder: Path, qgis_version: Optional[str] = None):
        """Constructor"""
        self.folder = folder
        # Dictionary : folder : plugin name
        self._plugins: Dict[str, str] = {}
        self._plugins_metadata: Dict[str, configparser.SectionProxy] = {}

        self.qgis_version: Optional[List[int]] = None
        self.qgis_version_str: Optional[str] = None
        if qgis_version:
            try:
                version = [int(i) for i in qgis_version.split(".")]
            except ValueError:
                raise PluginManagerError(f"{version} is not a valid QGIS version") from None
            if len(version) == 2:
                version.append(0)
                self.qgis_version_str = f"{version[0]}.{version[1]}"
            elif len(version) == 3:
                self.qgis_version_str = f"{version[0]}.{version[1]}.{version[2]}"
            else:
                raise PluginManagerError(f"{version} is not a valid QGIS version")

            self.qgis_version = version

        self.list_plugins()

    def init(self) -> bool:
        """Init this qgis-plugin-manager by creating the default sources.list."""
        source_file = sources_file(self.folder)
        if source_file.exists():
            echo.alert(f"{source_file.absolute()} is already existing. Quit")
            return False

        repository = get_default_remote_repository()
        version = self.qgis_version_str or "[VERSION]"

        print(f"Init {repository}", file=sys.stderr)

        server = f"https://plugins.qgis.org/plugins/plugins.xml?qgis={version}\n"

        try:
            with open(source_file, "w", encoding="utf8") as f:
                f.write(server)
        except PermissionError:
            # https://github.com/3liz/qgis-plugin-manager/issues/53
            echo.critical("The directory is not writable.")
            return False

        echo.info(f"{source_file.absolute()} has been written.")
        return True

    def plugin_list(self) -> Dict[str, str]:
        return self._plugins

    def list_plugins(self):
        """Get the list of plugins installed in the current directory."""
        for folder in self.folder.iterdir():
            if not folder.is_dir():
                continue

            # Skip hidden folders
            if folder.name.startswith("."):
                continue

            have_python = folder.joinpath("__init__.py").exists()
            have_metadata = folder.joinpath("metadata.txt").exists()
            if have_python and have_metadata:
                try:
                    metadata = self._get_plugin_metadata(folder.name)
                    self._plugins[folder.name] = metadata["name"]
                    self._plugins_metadata[folder.name] = metadata
                except KeyError:
                    echo.alert(f"WARNING: invalid metadata found in {folder}")

    def _get_plugin_metadata(self, plugin_folder: str) -> configparser.SectionProxy:
        """For a given plugin installed, get a metadata item."""
        config_parser = configparser.ConfigParser()
        with self.folder.joinpath(f"{plugin_folder}", "metadata.txt").open(encoding="utf8") as f:
            config_parser.read_file(f)
            return config_parser["general"]

    def get_plugin_folder_from_name(self, plugin_name: str) -> Optional[str]:
        for folder, name in self._plugins.items():
            if plugin_name == name:
                return folder
        return None

    def plugin_info(self, plugin: str) -> Optional[Plugin]:
        """For a given plugin, retrieve all metadata."""
        if plugin in self._plugins:
            # It's plugin folder
            plugin_folder: Optional[str] = plugin
        else:
            plugin_folder = self.get_plugin_folder_from_name(plugin)

        # Type narrowing
        if not plugin_folder:
            # No plugin
            return None

        md = self._plugins_metadata[plugin_folder]
        return Plugin(
            name=md["name"],
            version=md.get("version") or "0.0.0",
            experimental=md.getboolean("experimental", False),
            qgis_minimum_version=md.get("qgisMinimumVersion"),
            qgis_maximum_version=md.get("qgisMaximumVersion"),
            author_name=md.get("author"),
            server=md.getboolean("server", False),
            has_processing=md.getboolean("hasProcessingProvider", False),
            has_wps=md.getboolean("wps", False),
            install_folder=plugin_folder,
        )

    def remove(self, plugin_name: str) -> bool:
        """Remove a plugin by its human name."""

        all_names: set[str] = set()

        for plugin_folder in self.plugin_list():
            info = self.plugin_info(plugin_folder)
            if not info:
                echo.alert(f"Cannot get plugin info for {plugin_folder}")
                continue

            # We fill all names available
            all_names.add(info.name)

            if info.name == plugin_name:
                plugin_path = self.folder.joinpath(plugin_folder)
                try:
                    shutil.rmtree(plugin_path)
                except Exception as e:
                    echo.critical(f"Plugin {plugin_name} could not be removed : {e!s}")

                if not Path(self.folder.joinpath(plugin_folder)).exists():
                    echo.success(f"Plugin {plugin_name} removed")
                    return True
                else:
                    echo.alert(
                        f"Plugin {plugin_name} using folder {plugin_folder} "
                        "could not be removed "
                        "for unknown reason."
                    )
                break
        echo.alert(f"Plugin name '{plugin_name}' not found")

        similarity = similar_names(plugin_name.lower(), list(all_names))
        for plugin in similarity:
            echo.info(f"Do you mean maybe '{plugin}' ?")

        return False

    def print_table(self):
        """Print all plugins installed as a table."""

        remote = Remote(self.folder, qgis_version=self.qgis_version_str)

        headers = [
            "Folder ⬇",
            "Name",
            "Version",
            "Flags",
            "QGIS min",
            "QGIS max",
            "Author",
            "Folder rights",
            "Action ⚠",
        ]
        headers = [f"  {i}  " for i in headers]
        data = []

        list_of_owners = []

        sorted_plugins = list(self.plugin_list().keys())
        sorted_plugins.sort()
        for folder in sorted_plugins:
            # Folder
            plugin_data = [str(folder)]

            info = self.plugin_info(folder)

            # Name
            plugin_data = [
                folder,
                info.name,
                info.version,
            ]

            # Flags column
            flags = []
            if info.server:
                flags.append("Server")
            if info.has_wps:
                flags.append("WPS")
            if info.experimental:
                flags.append("Experimental")
            if info.has_processing:
                flags.append("Processing")
            if info.deprecated:
                flags.append("Deprecated")
            plugin_data.append(",".join(flags))

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
            user_info = stat_info.st_uid
            try:
                import pwd

                try:
                    user_name = pwd.getpwuid(user_info)[0]
                except KeyError:
                    user_name = user_info
            except ModuleNotFoundError:
                # On Windows, pwd does not exist
                user_name = user_info
            permissions = f"{user_name} : {oct(perms)}"
            plugin_data.append(permissions)
            if permissions not in list_of_owners:
                list_of_owners.append(permissions)

            # Action
            latest = remote.latest(info.name)
            current = info.version

            extra_info = []

            if len(current.split(".")) == 1:
                extra_info.append("Not a semantic version")

            elif latest:
                if latest.startswith("v"):
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
                # "qgis-plugin-manager update" is missing.
                # We can't determine what to do
                if not to_bool(os.getenv("QGIS_PLUGIN_MANAGER_SKIP_SOURCES_FILE")):
                    extra_info.append("Remote unknown")

            plugin_data.append(echo.format_alert(";".join(extra_info)))
            data.append(plugin_data)

        if len(data):
            echo.echo(pretty_table(data, headers))
        else:
            echo.alert(
                f"No plugin found in the current directory {self.folder.absolute()}",
            )

        if len(list_of_owners) > 1:
            list_of_owners = [f"'{i}'" for i in list_of_owners]
            echo.alert(
                f"Different rights have been detected : {','.join(list_of_owners)}Please check user-rights.",
            )
