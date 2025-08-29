import os

from difflib import SequenceMatcher
from itertools import takewhile
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Union

from semver import Version

from qgis_plugin_manager import echo

DEFAULT_REMOTE_REPOSITORY = "https://plugins.qgis.org"


class PluginManagerError(Exception):
    pass


def get_default_remote_repository() -> str:
    return os.getenv("QGIS_PLUGIN_MANAGER_REMOTE_REPOSITORY", DEFAULT_REMOTE_REPOSITORY)


def restart_qgis_server():
    """Restart QGIS Server tip."""
    restart_file = os.getenv("QGIS_PLUGIN_MANAGER_RESTART_FILE")
    if restart_file:
        Path(restart_file).touch()
    else:
        echo.info(f"{echo.format_alert('Tip')} : Do not forget to restart QGIS Server to reload plugins 😎")
        return


def install_prolog():
    # Get current users
    sudo_user = os.environ.get("SUDO_USER")
    user = current_user()
    # Installation done !
    if sudo_user:
        echo.info(f"\nPlugin(s) Installed with super user '{user}'")
    else:
        echo.info(f"\nPlugin(s) Installed with user '{user}'")

    echo.info(
        "Note: check file permissions and owner according to the user running QGIS Server.",
    )

    restart_qgis_server()


def similar_names(expected: str, available: Iterable[str]) -> Iterator[str]:
    """Returns a list of similar names available."""
    for item in available:
        ratio = SequenceMatcher(None, expected.lower(), item.lower()).ratio()
        if ratio > 0.8:
            yield item


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
        source_file = Path(env_path)
    else:
        source_file = current_folder.joinpath("sources.list")

    return source_file


def get_semver_version(version_str: str) -> Version:
    """Ensure that we get a SemvVer compatible version

    Otherwise convert to a compatible SemVer version scheme.
    See https://semver.org/
    """
    for prefix in ("ver.", "ver", "v.", "v"):
        version_str = version_str.removeprefix(prefix)

    # Check if this is semver
    try:
        return Version.parse(version_str)
    except Exception:
        pass

    source_str = version_str

    # Convert to compatible SEMVER version

    # Split at hyphen
    parts, *pre = version_str.split("-", maxsplit=1)
    pre = f"-{pre[0]}" if pre else ""  # type: ignore [assignment]

    parts = parts.split(".", maxsplit=3)  # type: ignore [assignment]

    ver = tuple(takewhile(lambda part: part.isdecimal(), parts[:3]))
    rest = ".".join(parts[len(ver) :]) + pre  # type: ignore [operator]
    if rest and not rest.startswith("-"):
        rest = f"+{rest}"  # Take it as build tag

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
        except Exception:
            if not try_again:
                raise

            def replace(c: str) -> str:
                return "-" if c == "_" or not c.isalnum() else c

            # Semver error
            # Replace non hyphen/no alphanumeric characters
            rest = "".join(replace(c) for c in rest[1:])
            rest = f"+{rest}"

    return version


def getenv_bool(name: str) -> bool:
    return os.getenv(name, "") in ("t", "true", "y", "yes", "1")
