#!/usr/bin/env python3

__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import argparse
import os

from pathlib import Path

from qgis_plugin_manager.__about__ import __version__
from qgis_plugin_manager.definitions import Level
from qgis_plugin_manager.local_directory import LocalDirectory
from qgis_plugin_manager.remote import Remote
from qgis_plugin_manager.utils import qgis_server_version, restart_qgis_server


def main() -> int:  # noqa: C901
    """ Main function for the CLI menu. """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(
        title="commands", description="qgis-plugin-manager command", dest="command"
    )

    subparsers.add_parser("init", help="Create the `sources.list` with plugins.qgis.org as remote")

    subparsers.add_parser("list", help="List all plugins in the directory")

    subparsers.add_parser("remote", help="List all remote server")

    remove = subparsers.add_parser("remove", help="Remove a plugin by its name")
    remove.add_argument("plugin_name", help="The plugin to remove")

    subparsers.add_parser('update', help="Update all index files")

    subparsers.add_parser('upgrade', help="Upgrade all plugins installed")

    cache = subparsers.add_parser("cache", help="Look for a plugin in the cache")
    cache.add_argument("plugin_name", help="The plugin to look for")

    search = subparsers.add_parser('search', help="Search for plugins")
    search.add_argument("plugin_name", help="Search in tags and plugin names")

    install = subparsers.add_parser('install', help="Install a plugin")
    install.add_argument(
        "plugin_name",
        help=(
            "The plugin to install, suffix '==version' is optional. The plugin might require quotes if there "
            "is a space in its name."))

    args = parser.parse_args()

    # if no command is passed, print the help and exit
    if not args.command:
        parser.print_help()
        parser.exit()

    exit_val = 0

    # Default to the current directory
    plugin_path = Path('.')
    if os.environ.get('QGIS_PLUGINPATH'):
        # Except if the QGIS_PLUGINPATH is set
        plugin_path = Path(os.environ.get('QGIS_PLUGINPATH'))

    if args.command == "update":
        remote = Remote(plugin_path)
        exit_val = remote.update()
    elif args.command in ("list", "init", "upgrade"):
        qgis = qgis_server_version()
        if qgis:
            print(f"QGIS version : {qgis}")
        plugins = LocalDirectory(plugin_path, qgis_version=qgis)

        if args.command == "list":
            plugins.print_table()
        elif args.command == "init":
            exit_val = plugins.init()
        elif args.command == "upgrade":
            remote = Remote(plugin_path)
            folders = plugins.plugin_list()
            for folder in folders:
                plugin_object = plugins.plugin_info(folder)
                result = remote.install(plugin_object.name)
                if not result:
                    exit_val = 1
            print(f"{Level.Alert}Tip{Level.End} : Do not forget to restart QGIS Server to reload plugins 😎")

    elif args.command == "remote":
        remote = Remote(plugin_path)
        remote.print_list()

    elif args.command == "remove":
        plugins = LocalDirectory(plugin_path)
        exit_val = plugins.remove(args.plugin_name)

    elif args.command == "cache":
        remote = Remote(plugin_path)
        latest = remote.latest(args.plugin_name)
        if latest is None:
            print(f"{Level.Alert}Plugin not found{Level.End}")
        else:
            print(f"Plugin {args.plugin_name} : {latest} available")

    elif args.command == "search":
        remote = Remote(plugin_path)
        results = remote.search(args.plugin_name)
        for result in results:
            print(result)

    elif args.command == "install":
        remote = Remote(plugin_path)
        parameter = args.plugin_name.split('==')
        exit_val = remote.install(*parameter)
        if exit_val:
            restart_qgis_server()

    if exit_val is None:
        exit_val = 0
    elif isinstance(exit_val, bool):
        exit_val = 0 if exit_val else 1

    return exit_val


if __name__ == "__main__":
    exit(main())
