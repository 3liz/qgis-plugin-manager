import argparse
import os
import sys

from argparse import Namespace
from pathlib import Path
from typing import (
    Callable,
)

from qgis_plugin_manager.__about__ import __version__
from qgis_plugin_manager.definitions import Level
from qgis_plugin_manager.local_directory import LocalDirectory
from qgis_plugin_manager.remote import PluginNotFoundError, Remote
from qgis_plugin_manager.utils import PluginManagerError, qgis_server_version

cli = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

cli.add_argument("-v", "--version", action="version", version=__version__)

subparsers = cli.add_subparsers(
    title="commands",
    description="qgis-plugin-manager command",
)


def command(name: str, **kwargs) -> Callable:
    """Wrap subcommand function"""

    def decorator(fun):
        if isinstance(fun, tuple):
            func, options = fun
        else:
            func = fun
            options = ()
        parser = subparsers.add_parser(name, description=func.__doc__, **kwargs)
        for opt in options:
            parser.add_argument(*opt[0], **opt[1])
        parser.set_defaults(func=func)

    return decorator


def argument(*args, **kwargs):
    arg = (args, kwargs)

    def decorator(fun):
        if isinstance(fun, tuple):
            # tuple(Callable, tuple[option])
            return (fun[0], (*fun[1], arg))
        else:
            return (fun, (arg,))

    return decorator


#
# Context utils
#


def get_plugin_path() -> Path:
    """Get the plugin path"""
    qgis_plugin_path = os.environ.get("QGIS_PLUGINPATH")
    if qgis_plugin_path:
        # Except if the QGIS_PLUGINPATH is set
        plugin_path = Path(qgis_plugin_path)
        print(f"Plugin's directory set by environment variable : {plugin_path.absolute()}\n")
    else:
        plugin_path = Path(".")
        print(f"Plugin's directory set to current directory : {plugin_path.absolute()}\n")
    return plugin_path


#
# Commands
#


# List
@command("list", help="List all plugins in the directory")
def list_plugins(args: Namespace):
    qgis = qgis_server_version()
    if qgis:
        print(f"QGIS version : {qgis}")
    plugins = LocalDirectory(get_plugin_path(), qgis_version=qgis)
    plugins.print_table()


# Init
@command(
    "init",
    help="Create the `sources.list` with plugins.qgis.org as remote",
)
@argument("--qgis-version", help="Set the qgis version")
def init_sources(args: Namespace):
    """If qgis-version is set to 'auto', then detect the current QGIS version"""
    # Local needed only, with QGIS version
    qgis_version = args.qgis_version
    if qgis_version == "auto":
        qgis_version = qgis_server_version()
    plugins = LocalDirectory(get_plugin_path(), qgis_version=qgis_version)
    plugins.init()


# Remote
@command("remote", help="List all remote servers")
def list_remote_servers(args: Namespace):
    remote = Remote(get_plugin_path(), qgis_server_version())
    remote.print_list()


# Remove
@command("remove", help="Remove a plugin by its name")
@argument("plugin_name", help="The plugin to remove")
def remove_plugin(args: Namespace):
    # Local needed only, without QGIS version
    plugins = LocalDirectory(get_plugin_path())
    if not plugins.remove(args.plugin_name):
        cli.exit(1)


# Cache
@command("cache", help="Look for a plugin in the cache")
@argument("plugin_name", help="The plugin to look for")
def look_for_plugin(args: Namespace):
    remote = Remote(get_plugin_path(), qgis_server_version())
    latest = remote.latest(args.plugin_name)
    if latest is None:
        print(f"{Level.Alert}Plugin not found{Level.End}")
        cli.exit(1)
    else:
        print(f"Plugin {args.plugin_name} : {latest} available")


# Update
@command("update", help="Update all index files")
def update_index(args: Namespace):
    remote = Remote(get_plugin_path(), qgis_server_version())
    if not remote.update():
        cli.exit(1)


# Upgrade
@command("upgrade", help="Upgrade all plugins installed")
@argument(
    "-f",
    "--force",
    action="store_true",
    help="Force reinstall all plugins",
)
def upgrade_plugins(args: Namespace):
    """Upgrade all plugins for which a
    newer version is available
    """
    plugin_path = get_plugin_path()

    qgis = qgis_server_version()
    remote = Remote(plugin_path, qgis_version=qgis)
    plugins = LocalDirectory(plugin_path, qgis_version=qgis)
    folders = plugins.plugin_list()

    # Check for ignored plugins
    ignored_plugins = []
    plugin_ignore_file = plugin_path.joinpath("ignorePlugins.list")
    if plugin_ignore_file.exists():
        with open(plugin_ignore_file, encoding="utf8") as f:
            ignored_plugins = [plugin.rstrip() for plugin in f.readlines()]

    for folder in folders:
        plugin_object = plugins.plugin_info(folder)

        if plugin_object.name in ignored_plugins:
            print(
                f"{Level.Alert}{plugin_object.name}: Ignored{Level.End}",
            )
            continue

        # Need to check version
        try:
            remote.install(
                plugin_name=plugin_object.name,
                current_version=plugin_object.version,
                force=args.force,
            )
        except PluginNotFoundError:
            print(
                f"{Level.Alert}{plugin_object.name}: Removed, not updating{Level.End}",
            )


# Search
@command("search", help="Search for plugins")
@argument("plugin_name", help="Search in tags and plugin names")
def search_plugin(args: Namespace):
    remote = Remote(get_plugin_path(), qgis_server_version())
    found = False
    for result in remote.search(args.plugin_name):
        print(result)
        found = True
    if not found:
        print("No plugins found", file=sys.stderr)


# Install
@command("install", help="Install a plugin")
@argument("plugin_name", help="The plugin to install")
@argument(
    "-f",
    "--force",
    action="store_true",
    help="Force installation",
)
def install_plugin(args: Namespace):
    """The version may be specified by appending the suffix '==version'.
    'plugin_name' might require quotes if there is space in its name.
    """
    plugin_path = get_plugin_path()

    qgis = qgis_server_version()
    if qgis:
        print(f"QGIS version : {qgis}")
    remote = Remote(plugin_path, qgis_version=qgis)
    plugins = LocalDirectory(plugin_path, qgis_version=qgis)

    parameter = args.plugin_name.split("==")
    plugin_name = parameter[0]
    if len(parameter) >= 2:
        plugin_version = parameter[1]
    else:
        plugin_version = "latest"

    current_version = plugins.plugin_installed_version(plugin_name)
    try:
        remote.install(
            plugin_name=plugin_name,
            version=plugin_version,
            current_version=current_version,
            force=args.force,
        )
    except PluginNotFoundError:
        similars = remote.check_similar_names(plugin_name)
        name = next(similars, None)
        if name:
            print("\nPlugins with similar name:")
            print("\t", name)
            for name in similars:
                print(name)
        cli.exit(1)


def main() -> None:
    """Main function for the CLI menu."""

    args = cli.parse_args()
    if "func" not in args:
        cli.print_help()
        cli.exit(1)
    else:
        try:
            args.func(args)
        except PluginManagerError as e:
            print(f"{Level.Critical}{e}{Level.End}", file=sys.stderr)


if __name__ == "__main__":
    exit(main())
