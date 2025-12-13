import os

from difflib import SequenceMatcher
from itertools import takewhile
from pathlib import Path
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

from semver import Version

from qgis_plugin_manager import echo


class PluginManagerError(Exception):
    pass


def restart_qgis_server():
    """Restart QGIS Server tip."""
    restart_file = os.getenv("QGIS_PLUGIN_MANAGER_RESTART_FILE")
    if restart_file:
        Path(restart_file).touch()
    else:
        echo.info(f"{echo.format_alert('Tip')} : Do not forget to restart QGIS Server to reload plugins 😎")
        return


def install_epilog():
    # Installation done !
    echo.info("\nInstallation done...")
    echo.info(
        "Note: check file permissions and owner according to the user running QGIS Server.",
    )

    restart_qgis_server()


def similar_names(expected: str, available: Iterable[str]) -> Iterator[str]:
    """Returns a list of similar names available."""
    matcher = SequenceMatcher(None, expected.lower())
    for item in available:
        matcher.set_seq2(item.lower())
        if matcher.ratio() > 0.8:
            yield item


def qgis_server_version() -> Optional[str]:
    """Try to guess the QGIS Server version.

    On linux distro, qgis python packages are installed at standard location
    in /usr/lib/python3/dist-packages
    """
    qgis_version = os.getenv("QGIS_PLUGIN_MANAGER_QGIS_VERSION")
    if qgis_version is None:
        try:
            from qgis.core import Qgis

            qgis_version = Qgis.QGIS_VERSION.split("-")[0]
        except ImportError:
            echo.alert(
                "Cannot check QGIS version, check your QGIS installation "
                "or your PYTHONPATH or set the QGIS_PLUGIN_MANAGER_QGIS_VERSION "
                "environment variable\n"
            )
    return qgis_version


def sources_file(current_folder: Path) -> Path:
    """Return the default path to the "sources.list" file.

    The path by default or if it's defined with the environment variable.
    """
    env_path = os.getenv("QGIS_PLUGIN_MANAGER_SOURCES_FILE")
    if env_path:
        source_file = Path(env_path)
    else:
        source_file = current_folder.joinpath("sources.list")

    return source_file


def get_semver_version(version_str: str) -> Version:
    """Ensure that we get a SemvVer compatible version

    QGIS does not enforce plugin version to be SemVer
    compatible.

    This represents a best effort to convert version strings
    to compatible SemVer version scheme.

    See https://semver.org/

    Examples:
        2.4.0.1    -> 2.4.0+1
        23.2a      -> 23.0.0+2a
        release    -> 0.0.0+release
        0.6-beta.3 -> 0.6.0-beta.3
    """
    for prefix in ("ver.", "ver", "v.", "v"):
        version_str = version_str.removeprefix(prefix)

    # Check if this is SemVer compatible
    try:
        return Version.parse(version_str)
    except ValueError:
        pass

    source_str = version_str

    # Split at hyphen, it may be a prerelease definition
    parts, *pre = version_str.split("-", maxsplit=1)
    pre = f"-{pre[0]}" if pre else ""  # type: ignore [assignment]

    # Split parts of the version string
    parts = parts.split(".", maxsplit=3)  # type: ignore [assignment]

    # Collect at most the three first parts that represent a number up to a
    # non-decimal parts.
    ver = tuple(takewhile(lambda part: part.isdecimal(), parts[:3]))
    # Coalesce remaining parts as a build tag if it does not starts
    # with a dash (like a prerelease tag do)
    rest = ".".join(parts[len(ver) :]) + pre  # type: ignore [operator]
    if rest and not rest.startswith("-"):
        rest = f"+{rest}"

    try_again = 2

    while try_again:
        try_again -= 1

        n = len(ver)
        if n == 3:
            version_str = f"{ver[0]}.{ver[1]}.{ver[2]}{rest}"
        elif n == 2:
            version_str = f"{ver[0]}.{ver[1]}.0{rest}"
        elif n == 1:
            version_str = f"{ver[0]}.0.0{rest}"
        elif n == 0:
            version_str = f"0.0.0{rest}"

        try:
            version = Version.parse(version_str)
            if rest:
                echo.debug(
                    "WARNING: using semver compatible scheme: {} (was {})",
                    version_str,
                    source_str,
                )
            break
        except ValueError:
            if not try_again:
                raise

            def replace(c: str) -> str:
                return "-" if c == "_" or not c.isalnum() or not c.isascii() else c

            # Semver error
            # Replace non hyphen/no alphanumeric characters
            rest = "".join(replace(c) for c in rest[1:])
            rest = f"+{rest}"

    return version


# Infaillible method that attempts to convert
# version string as a SemVer compatible string
def get_semver_version_str(v: str) -> str:
    try:
        return str(get_semver_version(v))
    except ValueError:
        return v


def getenv_bool(name: str) -> bool:
    return os.getenv(name, "").lower() in ("t", "true", "y", "yes", "1")


T = TypeVar("T")


def print_table(seq: Sequence[T], columns: Sequence[Tuple[str, Callable[[T], str]]]):
    def colw(col: str, key: Callable[[T], str]) -> int:
        return max(max((len(key(n)) for n in seq), default=0), len(col))

    cols = tuple((col, colw(col, key), key) for col, key in columns)
    echo.echo(" ".join("{:<{}}".format(col, w) for col, w, _ in cols))
    echo.echo(" ".join(f"{'':-<{w}}" for _, w, _ in cols))
    for n in seq:
        echo.echo(" ".join("{:<{}}".format(key(n), w) for _, w, key in cols))


def print_json(seq: Iterable[T], columns: Sequence[Tuple[str, Callable[[T], Any]]]):
    import json

    def records():
        for n in seq:
            yield {col: key(n) for col, key in columns}

    echo.echo(json.dumps(tuple(records()), indent=4))
