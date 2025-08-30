import argparse
import os

from argparse import Namespace
from pathlib import Path
from typing import (
    Callable,
    Optional,
)

from semver import Version

from qgis_plugin_manager import echo
from qgis_plugin_manager.definitions import Plugin
from qgis_plugin_manager.local_directory import LocalDirectory
from qgis_plugin_manager.remote import PluginNotFoundError, Remote
from qgis_plugin_manager.utils import (
    PluginManagerError,
    get_semver_version,
    install_epilog,
    print_json,
    print_table,
    qgis_server_version,
)

cli = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)


cli.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Activate verbose (debug) mode",
)


subparsers = cli.add_subparsers(
    title="commands",
    description="qgis-plugin-manager command",
)


def set_default_from_env(kwargs: dict):
    env = kwargs.pop("env", None)
    if env:
        value = os.getenv(env)
        if value is not None:
            if kwargs.get("action") == "store_true":
                kwargs["default"] = value.lower() in ("yes", "1", "y", "true", "t")
            else:
                kwargs["default"] = value


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
            set_default_from_env(opt[1])
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
        echo.info(f"Plugin's directory set by environment variable : {plugin_path.absolute()}\n")
    else:
        plugin_path = Path(".")
        echo.info(f"Plugin's directory set to current directory : {plugin_path.absolute()}\n")
    return plugin_path


#
# Commands
#


# Version
@command("version", help="Show version informations and exit")
def show_version(args):
    from importlib.metadata import version

    from . import __about__

    echo.echo(
        f"{__about__.__title__}\n"
        f"{__about__.__summary__}\n"
        f"Version: {version('qgis-plugin-manager')}\n"
        f"Author: {__about__.__author__}\n"
        f"Maintainer: {__about__.__maintainer__}\n"
        f"Copyright: {__about__.__copyright__}\n"
        f"Released under {__about__.__license__}\n"
        f"Url: {__about__.__uri__}\n"
    )


# Init
@command(
    "init",
    help="Create the `sources.list` with plugins.qgis.org as remote",
)
@argument("--qgis-version", help="Set the qgis version")
@argument("-u", "--update", action="store_true", help="Update index file")
def init_sources(args: Namespace):
    """If qgis-version is set to 'auto', then detect the current QGIS version"""
    # Local needed only, with QGIS version
    qgis_version = args.qgis_version
    if qgis_version == "auto":
        qgis_version = qgis_server_version()

    plugin_path = get_plugin_path()
    plugins = LocalDirectory(plugin_path)
    if plugins.init(qgis_version) and args.update:
        remote = Remote(plugin_path, qgis_version or qgis_server_version())
        if not remote.update():
            cli.exit(1)


# List
@command("list", help="List all plugins in the directory")
@argument("-o", "--outdated", action="store_true", help="List outdated plugins")
@argument(
    "--outdated-target",
    metavar="VERSION",
    help="""
        With the 'outdated' option, display the last version compatible with
        the QGIS version VERSION.
    """,
)
@argument(
    "--format",
    choices=("columns", "freeze", "list", "json"),
    default="columns",
    help="Select the output format",
)
@argument(
    "--pre",
    action="store_true",
    env="QGIS_PLUGIN_MANAGER_INCLUDE_PRERELEASE",
    help="""
        Include pre-release, development and experimental versions.
        Useful in conjonction with the 'outdated' option."
    """,
)
def list_plugins(args: Namespace):
    qgis = qgis_server_version()
    echo.info(f"QGIS version:  {qgis or 'Unknown'}")

    if not (args.outdated_target is None or args.outdated):
        echo.critical("'outdated-target' option is only usable with the '--outdated' option")
        exit(1)

    plugins = LocalDirectory(get_plugin_path())

    def infos():
        for folder, name in sorted(
            plugins.plugin_list().items(),
            key=lambda p: p[1],
        ):
            info = plugins.plugin_info(folder)
            if info:
                yield info

    if args.format == "freeze":
        if args.outdated:
            echo.critical("Youn cannot use the 'freeze' format with the 'outdated' option")
            exit(1)
        for info in infos():
            echo.echo(f"{info.name}=={info.version}")
    else:

        def install_folder(p: Plugin) -> str:
            if p.install_folder:
                return p.install_folder if p.install_folder != p.name else ""
            else:
                return ""

        if args.outdated:
            remote = Remote(plugins.folder, qgis_version=qgis)

            def outdated():
                for info in infos():
                    latest = remote.latest(
                        info.name,
                        include_prerelease=args.pre,
                        qgis_version=args.outdated_target,
                    )
                    if latest:
                        if latest.version <= info.version:
                            continue
                        latest_ver = str(latest.version)
                    else:
                        latest_ver = "Removed"
                    yield (info, latest_ver)

            outdated_list = tuple(outdated())
            if not outdated_list:
                echo.alert("No outdated plugins")
            else:
                if args.format == "list":
                    for info, _ in outdated_list:
                        echo.echo(info.name)
                elif args.format == "json":
                    print_json(
                        outdated_list,
                        (
                            ("name", lambda n: n[0].name),
                            ("version", lambda n: str(n[0].version)),
                            ("latest", lambda n: n[1]),
                            ("folder", lambda n: n[0].install_folder),
                        ),
                    )
                else:
                    print_table(
                        outdated_list,
                        (
                            ("Name", lambda n: n[0].name),
                            ("Version", lambda n: str(n[0].version)),
                            ("Latest", lambda n: n[1]),
                            ("Folder", lambda n: install_folder(n[0])),
                        ),
                    )
        else:
            if args.format == "list":
                for info in infos():
                    echo.echo(info.name)
            elif args.format == "json":
                print_json(
                    infos(),
                    (
                        ("name", lambda p: p.name),
                        ("version", lambda p: str(p.version)),
                        ("folder", lambda p: p.install_folder),
                    ),
                )
            else:
                print_table(
                    tuple(infos()),
                    (
                        ("Name", lambda p: p.name),
                        ("Version", lambda p: str(p.version)),
                        ("Folder", install_folder),
                    ),
                )


# Install
@command("install", help="Install a plugin")
@argument("plugin_name", nargs="+", help="The plugin(s) to install")
@argument(
    "-f",
    "--force",
    action="store_true",
    help="Force (re)installation",
)
@argument(
    "-U",
    "--upgrade",
    action="store_true",
    help="Upgrade plugin to latest version",
)
@argument(
    "--fix-permissions",
    action="store_true",
    help="Set files permissions to 0644",
)
@argument(
    "--pre",
    action="store_true",
    env="QGIS_PLUGIN_MANAGER_INCLUDE_PRERELEASE",
    help=(
        "Include pre-release, development and experimental versions. By default,\ninstall only stable version"
    ),
)
@argument("--deprecated", action="store_true", help="Include deprecated versions")
def install_plugin(args: Namespace):
    """The version may be specified by appending the suffix '==version'.
    'plugin_name' might require quotes if there is space in its name.
    """
    plugin_path = get_plugin_path()

    qgis = qgis_server_version()
    echo.info("QGIS version:  {qgis or 'Unknown'}")

    remote = Remote(plugin_path, qgis_version=qgis)
    plugins = LocalDirectory(plugin_path)

    installed = 0

    for arg in args.plugin_name:
        parameter = arg.split("==")
        plugin_name = parameter[0]

        plugin_info = plugins.plugin_info(plugin_name)

        if len(parameter) >= 2:
            plugin_version = parameter[1]
            if not plugin_version:
                echo.critical("Missing version")
                exit(1)
        else:
            plugin_version = None

        if plugin_info and not args.force:
            # Plugin already installed
            if plugin_version is None and args.upgrade:
                # Asked for upgrade
                latest = remote.latest(plugin_name, args.pre, args.deprecated)
                if latest and latest.version == plugin_info.version:
                    echo.alert(f"\t{plugin_name} is already at latest version")
                    continue
            elif plugin_version is None and plugin_info.version == plugin_version:
                echo.alert(f"\t{plugin_name}=={plugin_version} already installed")
                continue
            elif plugin_version is None:
                echo.alert(f"\t{plugin_name} already installed")
                continue

        try:
            install_version = remote.install(
                plugin_name=plugin_name,
                version=plugin_version,
                plugin_folder=plugin_info.install_folder if plugin_info else None,
                include_prerelease=args.pre,
                include_deprecated=args.deprecated,
                fix_permissions=args.fix_permissions,
            )

        except PluginNotFoundError:
            similars = remote.check_similar_names(plugin_name)
            name = next(similars, None)
            if name:
                echo.info(f"\n{plugin_name} not found. Plugins with similar name:")
                echo.info(f"\t{name}")
                for name in similars:
                    echo.info(name)
            cli.exit(1)
        except PluginManagerError as err:
            echo.critical(f"ERROR: {plugin_name}: {err}")
            cli.exit(1)
        else:
            echo.success(f"\tOk {plugin_name} {install_version}")
            installed += 1

    if installed > 0:
        install_epilog()


# Remove
@command("remove", help="Remove a plugin by its name")
@argument("plugin_name", help="The plugin to remove")
def remove_plugin(args: Namespace):
    # Local needed only, without QGIS version
    plugins = LocalDirectory(get_plugin_path())
    if not plugins.remove(args.plugin_name):
        cli.exit(1)


# Upgrade
@command("upgrade", help="Upgrade all plugins installed")
@argument(
    "-f",
    "--force",
    action="store_true",
    help="Force reinstall all plugins",
)
@argument(
    "--fix-permissions",
    action="store_true",
    help="Set files permissions to 0644",
)
@argument(
    "--pre",
    action="store_true",
    env="QGIS_PLUGIN_MANAGER_INCLUDE_PRERELEASE",
    help=(
        "Include pre-release, development and experimental versions. By default,\ninstall only stable version"
    ),
)
@argument("--deprecated", action="store_true", help="Include deprecated versions")
def upgrade_plugins(args: Namespace):
    """Upgrade all plugins for which a
    newer version is available
    """
    plugin_path = get_plugin_path()

    qgis = qgis_server_version()
    remote = Remote(plugin_path, qgis_version=qgis)
    plugins = LocalDirectory(plugin_path)
    folders = plugins.plugin_list()

    # Check for ignored plugins
    ignored_plugins = []
    plugin_ignore_file = plugin_path.joinpath("ignorePlugins.list")
    if plugin_ignore_file.exists():
        with open(plugin_ignore_file, encoding="utf8") as f:
            ignored_plugins = [plugin.rstrip() for plugin in f.readlines()]

    installed = 0
    failures = 0

    for folder in folders:
        plugin_info = plugins.plugin_info(folder)
        if not plugin_info:
            echo.debug(f"No plugin found for {folder}")
            continue

        if plugin_info.name in ignored_plugins:
            echo.alert(f"{plugin_info.name:<25}\tIgnored")
            continue

        if not args.force:
            latest = remote.latest(plugin_info.name, args.pre, args.deprecated)
            if latest and latest.version == plugin_info.version:
                echo.success(f"\t\u274e {plugin_info.name:<25} {plugin_info.version!s:<12}\tUnchanged")
                continue
            elif latest is None:
                echo.alert(f"\t\u26a0\ufe0f {plugin_info.name}\tRemoved from repository")
                continue
            version: Optional[str] = str(latest.version) if latest else None
        else:
            version = None

        # Need to check version
        try:
            install_version = remote.install(
                plugin_name=plugin_info.name,
                version=version,
                plugin_folder=plugin_info.install_folder,
                fix_permissions=args.fix_permissions,
                include_prerelease=args.pre,
                include_deprecated=args.deprecated,
            )
        except PluginNotFoundError:
            echo.alert(f"\t\u26a0\ufe0f {plugin_info.name:aa<25}\tNot found")
        except PluginManagerError as err:
            failures += 1
            echo.critical(f"\t\u274c {plugin_info.name:<25}\tError: {err}")
        else:
            installed += 1
            echo.success(f"\t\u2705 {plugin_info.name:<25} {install_version:<12}\tInstalled")

    if failures > 0:
        echo.alert(f"Command terminated with {failures} errors")
    if installed > 0:
        install_epilog()


@command("remotes", help="List all remote sources")
def list_remote_servers(args: Namespace):
    remote = Remote(get_plugin_path(), qgis_server_version())
    remote.print_list()


# Update
@command("update", help="Update all index files")
def update_index(args: Namespace):
    remote = Remote(get_plugin_path(), qgis_server_version())
    if not remote.update():
        cli.exit(1)


# Cache (Deprecated)
@command("cache", help="Look for available plugin is the cache - Deprecated")
@argument("plugin_name", help="The plugin to look for")
def plugin_versions_deprecated(args: Namespace):
    """This command is deprecated, please use the 'versions' command instead."""
    echo.alert("Warning: this command is deprecated in favor of the 'versions' command")
    args.pre = False
    args.deprecated = False
    plugin_versions_impl(args)


# Versions
@command("versions", help="Look for available plugin versions")
@argument("plugin_name", help="The plugin to look for")
@argument(
    "--pre",
    action="store_true",
    env="QGIS_PLUGIN_MANAGER_INCLUDE_PRERELEASE",
    help=(
        "Include pre-release, development and experimental versions. By default,\ndisplay only stable version"
    ),
)
@argument("--deprecated", action="store_true", help="Include deprecated versions")
def plugin_versions(args: Namespace):
    plugin_versions_impl(args)


def plugin_versions_impl(args: Namespace):
    remote = Remote(get_plugin_path(), qgis_server_version())
    plugins = remote.available_plugins()

    versions = plugins.get(args.plugin_name)
    if versions:
        for plugin in versions:
            if plugin.is_pre() and not args.pre:
                continue
            if plugin.deprecated and not args.deprecated:
                continue
            echo.echo(f"{args.plugin_name}=={plugin.version}")
    else:
        echo.alert(f"No versions found for '{args.plugin_name}'")
        cli.exit(1)


# Search
@command("search", help="Search for plugins")
@argument("plugin_name", help="Search in tags and plugin names")
@argument("--server", action="store_true", help="Consider only server plugins")
@argument("--trusted", action="store_true", help="Consider only trusted plugins")
@argument(
    "--pre",
    action="store_true",
    env="QGIS_PLUGIN_MANAGER_INCLUDE_PRERELEASE",
    help="""
        Include pre-release, development and experimental versions.
        By default, search only stable versions.
    """,
)
@argument("--deprecated", action="store_true", help="Include deprecated versions")
def search_plugin(args: Namespace):
    remote = Remote(get_plugin_path(), qgis_server_version())
    found = False

    def pred(p):
        if args.trusted and not p.trusted:
            return False
        if args.server and not p.server:
            return False
        if not args.pre and p.is_pre():
            return False
        if not args.deprecated and p.deprecated:
            return False
        return True

    for result in remote.search(args.plugin_name, predicat=pred):
        echo.echo(result)
        found = True
    if not found:
        echo.info("No plugins found")


# Check
@command("check", help="Check compatibility of installed plugins with QGIS version")
@argument("-v", "--version", help="QGIS version to check against")
@argument(
    "--format",
    choices=("columns", "json"),
    default="columns",
    help="Select the output format",
)
def check_qgis_compat(args: Namespace):
    """If version is not specified then check against the current QGIS
    installation
    """

    def get_version() -> Version:
        ver = args.version if args.version else qgis_server_version()
        if not ver:
            exit(1)
        try:
            return get_semver_version(ver)
        except Exception as e:
            echo.critical(f"{e}")
            exit(1)

    version = get_version()

    plugins = LocalDirectory(get_plugin_path())

    def infos():
        for folder, name in sorted(
            plugins.plugin_list().items(),
            key=lambda p: p[1],
        ):
            info = plugins.plugin_info(folder)
            if info:
                yield info

    if args.format == "json":
        print_json(
            infos(),
            (
                ("name", lambda p: p.name),
                ("version", lambda p: str(p.version)),
                ("qgisVersion", lambda _: str(version)),
                ("canUse", lambda p: p.check_qgis_version(version)),
            ),
        )
    else:
        print_table(
            tuple(infos()),
            (
                ("Name", lambda p: p.name),
                ("Version", lambda p: str(p.version)),
                (
                    f"QGIS {version}",
                    lambda p: "Yes" if p.check_qgis_version(version) else "No",
                ),
            ),
        )


def main() -> None:
    """Main function for the CLI menu."""

    args = cli.parse_args()
    if "func" not in args:
        cli.print_help()
        cli.exit(1)
    else:
        echo.set_verbose_mode(args.verbose)
        try:
            args.func(args)
        except PluginManagerError as e:
            echo.critical(f"{e}")


if __name__ == "__main__":
    main()
