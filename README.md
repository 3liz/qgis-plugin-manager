# QGIS-Plugin-Manager

[![Tests](https://github.com/3liz/qgis-plugin-manager/actions/workflows/release.yml/badge.svg)](https://github.com/3liz/qgis-plugin-manager/actions/workflows/release.yml)
[![PyPi version badge](https://badgen.net/pypi/v/qgis-plugin-manager)](https://pypi.org/project/qgis-plugin-manager/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/qgis-plugin-manager)](https://pypi.org/project/qgis-plugin-manager/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qgis-plugin-manager)](https://pypi.org/project/qgis-plugin-manager/)

Mainly designed for QGIS Server plugins.

Not tested on Windows.

The **CLI** API is not stable yet.

## Installation

Python 3.6 minimum, you can make a Python venv if needed.
```bash
python3 --version
```

```bash
pip3 install qgis-plugin-manager
python3 -m pip install qgis-plugin-manager
```



## Utilisation

```bash
cd /path/where/you/have/plugins
```

```bash
$ qgis-plugin-manager --help
usage: qgis-plugin-manager [-h] [-v] {init,list,remote,update,cache,install} ...

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         Print the version and exit (default: False)

commands:
  qgis-plugin-manager command

  {init,list,remote,update,cache,install}
    init                Create the `sources.list` with plugins.qgis.org as remote
    list                List all plugins in the directory
    remote              List all remote server
    update              Update all index files
    cache               Look for a plugin in the cache
    install             Install a plugin
```

### Init

To create the first `sources.list` in the directory with at least the default repository https://plugins.qgis.org :
```bash
$ qgis-plugin-manager init
$ cat sources.list 
https://plugins.qgis.org/plugins/plugins.xml?qgis=3.19
```

You can have one or many servers, one on each line.

### List

List all plugins installed :

```bash
$ qgis-plugin-manager list
QGIS server version 3.19.0
List all plugins in /home/etienne/dev/qgis/server_plugin

----------------------------------------------------------------------------------------
|  Name            |  Version  |  QGIS min  |  QGIS max  |  Author         |  Action ⚠       |
----------------------------------------------------------------------------------------
|Lizmap            |master     |3.4         |3.99        |3Liz             |Unkown version   |
|wfsOutputExtension|1.5.3      |3.0         |            |3Liz             |                 |
|QuickOSM          |1.14.0     |3.4         |3.99        |Etienne Trimaille|Upgrade to 1.16.0|
|cadastre          |1.6.2      |3.0         |3.99        |3liz             |                 |
|atlasprint        |3.2.2      |3.10        |            |3Liz             |                 |
----------------------------------------------------------------------------------------
```

### Remote

```bash
$ qgis-plugin-manager remote
List of remotes :

https://plugins.qgis.org/plugins/plugins.xml?qgis=3.19

```

### Update

To fetch the XML files from each repository :

```bash
$ qgis-plugin-manager update
Downloading https://plugins.qgis.org/plugins/plugins.xml?qgis=3.19...
	Ok
$ ls .cache_qgis_plugin_manager/
https-plugins-qgis-org-plugins-plugins-xml-qgis-3-19.xml
```

### Cache

Check if a plugin is available :

```bash
$ qgis-plugin-manager cache atlasprint
Plugin atlasprint : v3.2.2 available
```

### Install

Install the latest version :
```bash
$ qgis-plugin-manager install QuickOSM
Installation QuickOSM latest
	Ok QuickOSM.1.16.0.zip
```

or a specific version :

```bash
$ qgis-plugin-manager install QuickOSM==1.14.0
Installation QuickOSM 1.14.0
	Ok QuickOSM.1.14.0.zip
```

## Run tests

```bash
export PYTHONPATH=/home/etienne/dev/app/qgis-master/share/qgis/python/:/usr/lib/python3/dist-packages/
cd test
python3 -m unittest
```

## TODO

* proper exit code
* API
* documentation
