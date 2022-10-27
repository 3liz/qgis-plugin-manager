__copyright__ = 'Copyright 2022, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

import os

from difflib import SequenceMatcher
from pathlib import Path
from typing import Union

from qgis_plugin_manager.definitions import Level

DEFAULT_QGIS_VERSION = "3.22"


def pretty_table(iterable, header) -> str:
    """ Copy/paste from http://stackoverflow.com/a/40426743/2395485 """
    max_len = [len(x) for x in header]
    for row in iterable:
        row = [row] if type(row) not in (list, tuple) else row
        for index, col in enumerate(row):
            if max_len[index] < len(str(col)):
                max_len[index] = len(str(col))
    output = '-' * (sum(max_len) + 1) + '\n'
    output += '|' + ''.join(
        [h + ' ' * (l - len(h)) + '|' for h, l in zip(header, max_len)]) + '\n'
    output += '-' * (sum(max_len) + 1) + '\n'
    for row in iterable:
        row = [row] if type(row) not in (list, tuple) else row
        output += '|' + ''.join(
            [
                str(c) + ' ' * (
                    l - len(str(c))) + '|' for c, l in zip(
                    row, max_len)
            ]
        ) + '\n'
    output += '-' * (sum(max_len) + 1) + '\n'
    return output


def restart_qgis_server():
    """ Restart QGIS Server tip. """
    print(f"{Level.Alert}Tip{Level.End} : Do not forget to restart QGIS Server to reload plugins 😎")

    restart_file = os.getenv("QGIS_PLUGIN_MANAGER_RESTART_FILE")
    if not restart_file:
        return

    Path(restart_file).touch()


def similar_names(expected: str, available: list) -> list:
    """ Returns a list of similar names available. """
    similar = []
    for item in available:
        ratio = SequenceMatcher(None, expected, item.lower()).ratio()
        if ratio > 0.8:
            similar.append(item)
    return similar


def to_bool(val: Union[str, int, float, bool], default_value: bool = True) -> bool:
    """ Convert a value to boolean """
    if isinstance(val, str):
        # For string, compare lower value to True string
        return val.lower() in ('yes', 'true', 't', '1')
    elif not val:
        # For value like False, 0, 0.0, None, empty list or dict returns False
        return False
    else:
        return default_value


def parse_version(version: str) -> Union[None, list]:
    if version is None or version == "":
        return None

    version = [int(i) for i in version.split(".")]
    if len(version) == 2:
        version.append(0)
    return version


def current_user() -> str:
    """ Return the current user if possible. """
    import getpass

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

    user = os.environ.get('USER')
    if user:
        return user

    user = os.environ.get('UID')
    if user:
        return user

    return 'Unknown'


def qgis_server_version() -> str:
    """ Try to guess the QGIS Server version.

        On linux distro, qgis python packages are installed at standard location
        in /usr/lib/python3/dist-packages
    """
    try:
        from qgis.core import Qgis
        return Qgis.QGIS_VERSION.split('-')[0]
    except ImportError:
        print(
            f"{Level.Alert}"
            f"Cannot check version with PyQGIS, check your QGIS installation or your PYTHONPATH"
            f"{Level.End}"
        )
        print(f"Current user : {current_user()}")
        print(f'PYTHONPATH={os.getenv("PYTHONPATH")}')
        return ''


def sources_file(current_folder) -> Path:
    """ Return the default path to the "sources.list" file.

    The path by default or if it's defined with the environment variable.
    """
    env_path = os.getenv("QGIS_PLUGIN_MANAGER_SOURCES_FILE")
    if env_path:
        return Path(env_path)

    source_file = current_folder.joinpath('sources.list')
    return source_file
