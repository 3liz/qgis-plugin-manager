#!/usr/bin/env python3

__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import argparse

from pathlib import Path

from qgis_plugin_manager.local_directory import LocalDirectory
from qgis_plugin_manager.remote import Remote
from qgis_plugin_manager.utils import qgis_server_version


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-v", "--version", help="Print the version and exit", action="store_true"
    )

    subparsers = parser.add_subparsers(
        title="commands", description="qgis-plugin-manager command", dest="command"
    )

    subparsers.add_parser("init", help="Create the `sources.list` with plugins.qgis.org as remote")

    subparsers.add_parser("list", help="List all plugins in the directory")

    subparsers.add_parser("remote", help="List all remote server")

    subparsers.add_parser('update', help="Update all index files")

    cache = subparsers.add_parser("cache", help="Look for a plugin in the cache")
    cache.add_argument("plugin_name", help="The plugin to look for")

    install = subparsers.add_parser('install', help="Install a plugin")
    install.add_argument("plugin_name", help="The plugin to install, suffix '==version' is optional")

    args = parser.parse_args()

    # print the version and exit
    if args.version:
        import pkg_resources

        print(
            "qgis-plugin-manager version: {}".format(
                pkg_resources.get_distribution("qgis-plugin-manager").version
            )
        )
        qgis = qgis_server_version()
        if qgis:
            print(f"QGIS server version {qgis_server_version()}")
        parser.exit()

    # if no command is passed, print the help and exit
    if not args.command:
        parser.print_help()
        parser.exit()

    exit_val = 0

    if args.command == "update":
        remote = Remote(Path('.'))
        remote.update()
    elif args.command in ["list", "init"]:
        qgis = qgis_server_version()
        if qgis:
            print(f"QGIS server version {qgis}")
        else:
            print(f"QGIS server version unknown")

        plugins = LocalDirectory(Path('.'), qgis_version=qgis)

        if args.command == "list":
            plugins.print_table()
        else:
            plugins.init()

    elif args.command == "remote":
        remote = Remote(Path('.'))
        remote.print_list()

    elif args.command == "cache":
        remote = Remote(Path('.'))
        latest = remote.latest(args.plugin_name)
        if latest is None:
            print("Plugin not found")
        else:
            print(f"Plugin {args.plugin_name} : {latest} available")

    elif args.command == "install":
        remote = Remote(Path('.'))
        parameter = args.plugin_name.split('==')
        result = remote.install(*parameter)
        if result is None:
            exit_val = 1

    return exit_val


if __name__ == "__main__":
    exit(main())
