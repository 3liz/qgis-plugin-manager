import configparser
import shutil

from pathlib import Path
from typing import Dict, Optional

from semver import Version

from qgis_plugin_manager import echo
from qgis_plugin_manager.definitions import Plugin
from qgis_plugin_manager.utils import (
    PluginManagerError,
    get_semver_version,
    similar_names,
)


class LocalDirectory:
    def __init__(self, folder: Path):
        """Constructor"""
        self.folder = folder
        # Dictionary : folder : plugin name
        self._plugins: Dict[str, str] = {}
        self._plugins_metadata: Dict[str, configparser.SectionProxy] = {}
        self.list_plugins()

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
        """Get the folder name from the plugin name"""
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

        version_str = md.get("version") or "0.0.0"

        return Plugin(
            name=md["name"],
            version=get_semver_version(version_str),
            version_str=version_str,
            experimental=md.getboolean("experimental", False),
            qgis_minimum_version=qgis_minimum_version,
            qgis_maximum_version=qgis_maximum_version,
            author_name=md.get("author"),
            server=md.getboolean("server", False),
            has_processing=md.getboolean("hasProcessingProvider", False),
            install_folder=plugin_folder,
        )

    def remove(self, plugin_name: str) -> bool:
        """Remove a plugin by its name."""

        folder = self.get_plugin_folder_from_name(plugin_name)
        if not folder:
            echo.alert(f"Plugin name '{plugin_name}' not found")

            similarity = similar_names(plugin_name.lower(), self._plugins.values())
            for plugin in similarity:
                echo.info(f"Do you mean maybe '{plugin}' ?")

            return False

        # Remove folder
        plugin_path = self.folder.joinpath(folder)
        try:
            echo.debug(f"Removing {plugin_path.absolute()}")
            shutil.rmtree(plugin_path)
        except Exception as e:
            raise PluginManagerError(f"Plugin {plugin_name} could not be removed : {e!s}")

        if Path(self.folder.joinpath(plugin_path)).exists():
            echo.alert(
                f"Plugin {plugin_name} using folder {plugin_path.absolute()} "
                "could not be removed for unknown reason."
            )
            return False

        echo.success(f"Plugin {plugin_name} removed")
        del self._plugins[folder]
        return True
