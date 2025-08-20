import os

from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterator, List, Optional, Union

from qgis_plugin_manager import echo

DEFAULT_REMOTE_REPOSITORY = "https://plugins.qgis.org"


class PluginManagerError(Exception):
    pass


def get_default_remote_repository() -> str:
    return os.getenv("QGIS_PLUGIN_MANAGER_REMOTE_REPOSITORY", DEFAULT_REMOTE_REPOSITORY)


def pretty_table(iterable: list, header: list) -> str:
    """Copy/paste from http://stackoverflow.com/a/40426743/2395485"""
    max_len = [len(x) for x in header]
    for row in iterable:
        row = [row] if type(row) not in (list, tuple) else row
        for index, col in enumerate(row):
            if max_len[index] < len(str(col)):
                max_len[index] = len(str(col))
    output = "-" * (sum(max_len) + 1) + "\n"
    output += (
        "|"
        + "".join(
            [a_header + " " * (a_line - len(a_header)) + "|" for a_header, a_line in zip(header, max_len)],
        )
        + "\n"
    )
    output += "-" * (sum(max_len) + 1) + "\n"
    for row in iterable:
        row = [row] if type(row) not in (list, tuple) else row
        output += (
            "|"
            + "".join(
                [str(c) + " " * (a_line - len(str(c))) + "|" for c, a_line in zip(row, max_len)],
            )
            + "\n"
        )
    output += "-" * (sum(max_len) + 1) + "\n"
    return output


def restart_qgis_server():
    """Restart QGIS Server tip."""
    echo.info(
        f"{echo.format_alert('Tip')} : Do not forget to restart QGIS Server to reload plugins 😎",
    )

    restart_file = os.getenv("QGIS_PLUGIN_MANAGER_RESTART_FILE")
    if not restart_file:
        return

    Path(restart_file).touch()


def similar_names(expected: str, available: List[str]) -> Iterator[str]:
    """Returns a list of similar names available."""
    for item in available:
        ratio = SequenceMatcher(None, expected.lower(), item.lower()).ratio()
        if ratio > 0.8:
            yield item


def to_bool(val: Optional[Union[str, int, float, bool]]) -> bool:
    """Convert a value to boolean"""
    if isinstance(val, str):
        # For string, compare lower value to True string
        return val.lower() in ("yes", "true", "t", "1")
    else:
        # For value like False, 0, 0.0, None, empty list or dict returns False
        return bool(val)


def parse_version(version_str: Optional[str]) -> Optional[List[int]]:
    if version_str is None or version_str == "":
        return None

    version = [int(i) for i in version_str.split(".")]
    if len(version) == 2:
        version.append(0)
    return version


def current_user() -> str:
    """Return the current user if possible."""
    import getpass

    user: Optional[Union[str, int]] = None

    try:
        user = getpass.getuser()
        if user:
            return user
    except KeyError:
        pass

    try:
        user = os.getlogin()
        if user:
            return user
    except OSError:
        pass

    user = os.getegid()
    if user:
        return str(user)

    user = os.environ.get("USER")
    if user:
        return user

    user = os.environ.get("UID")
    if user:
        return user

    return "Unknown"


def qgis_server_version() -> str:
    """Try to guess the QGIS Server version.

    On linux distro, qgis python packages are installed at standard location
    in /usr/lib/python3/dist-packages
    """
    try:
        from qgis.core import Qgis

        # 3.34.6
        return Qgis.QGIS_VERSION.split("-")[0]
    except ImportError:
        echo.alert("Cannot check version with PyQGIS, check your QGIS installation or your PYTHONPATH")
        echo.info(f"Current user : {current_user()}")
        echo.info(f"PYTHONPATH={os.getenv('PYTHONPATH')}")
        return ""


def sources_file(current_folder: Path) -> Path:
    """Return the default path to the "sources.list" file.

    The path by default or if it's defined with the environment variable.
    """
    env_path = os.getenv("QGIS_PLUGIN_MANAGER_SOURCES_FILE")
    if env_path:
        return Path(env_path)

    source_file = current_folder.joinpath("sources.list")
    return source_file
