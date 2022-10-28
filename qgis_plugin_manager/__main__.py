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
from qgis_plugin_manager.utils import qgis_server_version


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

    upgrade_parser = subparsers.add_parser('upgrade', help="Upgrade all plugins installed")
    upgrade_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help=(
            "If specified, the upgrade will be forced for all plugins. Otherwise, it will be done only if "
            "the version is different."
        ),
    )

    cache = subparsers.add_parser("cache", help="Look for a plugin in the cache")
    cache.add_argument("plugin_name", help="The plugin to look for")

    search = subparsers.add_parser('search', help="Search for plugins")
    search.add_argument("plugin_name", help="Search in tags and plugin names")

    install = subparsers.add_parser('install', help="Install a plugin")
    install.add_argument(
        "plugin_name",
        help=(
            "The plugin to install, suffix '==version' is optional. The plugin might require quotes if "
            "there is a space in its name."))
    install.add_argument(
        "-f",
        "--force",
        action="store_true",
        help=(
            "If specified, the install will be forced for the plugin, even if the version is already "
            "installed."
        ),
    )

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

    if args.command in ("remote", "cache", "search"):
        # Remote only needed, no QGIS version needed
        remote = Remote(plugin_path)
        if args.command == "remote":
            remote.print_list()
        elif args.command == "cache":
            latest = remote.latest(args.plugin_name)
            if latest is None:
                print(f"{Level.Alert}Plugin not found{Level.End}")
            else:
                print(f"Plugin {args.plugin_name} : {latest} available")
        elif args.command == "search":
            results = remote.search(args.plugin_name)
            for result in results:
                print(result)

    elif args.command in ("update", ):
        # Remote only needed, QGIS version needed
        remote = Remote(plugin_path, qgis_server_version())
        if args.command == "update":
            exit_val = remote.update()

    elif args.command in ("remove", ):
        # Local needed only, without QGIS version
        plugins = LocalDirectory(plugin_path)
        exit_val = plugins.remove(args.plugin_name)

    elif args.command in ("list", "init"):
        # Local needed only, with QGIS version
        qgis = qgis_server_version()
        if qgis:
            print(f"QGIS version : {qgis}")
        plugins = LocalDirectory(plugin_path, qgis_version=qgis)

        if args.command == "list":
            # The remote will be used inside this function
            plugins.print_table()

        elif args.command == "init":
            exit_val = plugins.init()

    elif args.command in ("upgrade", "install"):
        # Local and remote needed
        qgis = qgis_server_version()
        if qgis:
            print(f"QGIS version : {qgis}")
        remote = Remote(plugin_path, qgis_version=qgis)
        plugins = LocalDirectory(plugin_path, qgis_version=qgis)
        folders = plugins.plugin_list()

        if args.command == "install":
            parameter = args.plugin_name.split('==')
            plugin_name = parameter[0]
            if len(parameter) >= 2:
                plugin_version = parameter[1]
            else:
                plugin_version = 'latest'

            current_version = plugins.plugin_installed_version(plugin_name)
            exit_val = remote.install(
                plugin_name=plugin_name,
                version=plugin_version,
                current_version=current_version,
                force=args.force,
            )

        elif args.command == "upgrade":
            for folder in folders:
                plugin_object = plugins.plugin_info(folder)
                # Need to check version
                result = remote.install(
                    plugin_name=plugin_object.name,
                    current_version=plugin_object.version,
                    force=args.force,
                )
                if not result:
                    exit_val = False

    if exit_val is None:
        exit_val = 0
    elif isinstance(exit_val, bool):
        exit_val = 0 if exit_val else 1

    return exit_val


if __name__ == "__main__":
    exit(main())
