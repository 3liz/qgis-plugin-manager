__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'

from typing import Union


def pretty_table(iterable, header):
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
                    row, max_len)]) + '\n'
    output += '-' * (sum(max_len) + 1) + '\n'
    return output


def parse_version(version: str) -> Union[None, list]:
    if version is None or version == "":
        return None

    version = [int(i) for i in version.split(".")]
    if len(version) == 2:
        version.append(0)
    return version


def qgis_server_version():
    """ Try to guess the QGIS Server version. 
    
        On linux distro, qgis python packages are installed at standard location
        in /usr/lib/python3/dist-packages
    """
    try:
        from qgis.core import Qgis
        return Qgis.QGIS_VERSION.split('-')[0]
    except ImportError:
        print("Cannot check version with PyQGIS, check your QGIS installation or your PYTHONPATH")
