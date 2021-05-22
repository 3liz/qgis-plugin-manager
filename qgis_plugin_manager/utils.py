import os
import re
import subprocess
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


def parse_ldd(command_output: str):
    if isinstance(command_output, str):
        command_output = command_output.split('\n')

    for line in command_output:
        # line = [i.strip() for i in line.split("=>")]

        if isinstance(line, list):
            line = line[0]

        exp = re.search(r"\d+.\d+.\d+", line)
        if exp:
            return exp.group()

    return None


def qgis_server_version():
    """ Try to guess the QGIS Server version. """
    # Using ldd :(
    exec_path = os.getenv('QGIS_EXEC_PATH')
    if not exec_path:
        exec_path = "/usr/lib/cgi-bin/qgis_mapserv.fcgi"

    output = subprocess.run(["ls", exec_path], capture_output=True)

    if output.returncode != 0:
        print(f"{exec_path} is not found, not possible to determine QGIS version. Try QGIS_EXEC_PATH")
        return None

    output = subprocess.run(
        ["ldd", exec_path],
        capture_output=True,
        text=True,
    )
    output = [i for i in output.stdout.split('\n') if 'qgis' in i]
    return parse_ldd(output)
