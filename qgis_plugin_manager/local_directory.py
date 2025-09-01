import configparser
import shutil
import sys

from pathlib import Path
from typing import Dict, Optional

from semver import Version

from qgis_plugin_manager import echo
from qgis_plugin_manager.definitions import Plugin
from qgis_plugin_manager.utils import (
    PluginManagerError,
    get_default_remote_repository,
    get_semver_version,
    similar_names,
    sources_file,
)


class LocalDirectory:
    def __init__(self, folder: Path):
        """Constructor"""
        self.folder = folder
        # Dictionary : folder : plugin name
        self._plugins: Dict[str, str] = {}
        self._plugins_metadata: Dict[str, configparser.SectionProxy] = {}
        self.list_plugins()

    def init(self, qgis_version: Optional[str]) -> bool:
        """Init this qgis-plugin-manager by creating the default sources.list."""
        source_file = sources_file(self.folder)
        if source_file.exists():
            echo.alert(f"{source_file.absolute()} is already existing. Quit")
            return False

        if qgis_version:
            try:
                ver = get_semver_version(qgis_version)
                version = f"{ver.major}.{ver.minor}"
            except Exception:
                raise PluginManagerError(f"{qgis_version} is not a valid QGIS version") from None
        else:
            version = "[VERSION]"

        repository = get_default_remote_repository()

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

        def maybe_version(ver: Optional[str]) -> Optional[Version]:
            return get_semver_version(ver) if ver else None

        # Make sure that version is semver compatible
        qgis_minimum_version = maybe_version(md.get("qgisMinimumVersion"))
        qgis_maximum_version = maybe_version(md.get("qgisMaximumVersion"))

        return Plugin(
            name=md["name"],
            version=get_semver_version(md.get("version") or "0.0.0."),
            experimental=md.getboolean("experimental", False),
            qgis_minimum_version=qgis_minimum_version,
            qgis_maximum_version=qgis_maximum_version,
            author_name=md.get("author"),
            server=md.getboolean("server", False),
            has_processing=md.getboolean("hasProcessingProvider", False),
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
