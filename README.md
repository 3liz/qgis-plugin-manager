# QGIS-Plugin-Manager

[![Tests](https://github.com/3liz/qgis-plugin-manager/actions/workflows/release.yml/badge.svg)](https://github.com/3liz/qgis-plugin-manager/actions/workflows/release.yml)
[![PyPi version badge](https://badgen.net/pypi/v/qgis-plugin-manager)](https://pypi.org/project/qgis-plugin-manager/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/qgis-plugin-manager)](https://pypi.org/project/qgis-plugin-manager/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qgis-plugin-manager)](https://pypi.org/project/qgis-plugin-manager/)

Mainly designed for QGIS Server plugins, but it works also for desktop.

Not tested on Windows.

The **CLI** API is not stable yet.

## Installation

Python 3.7 **minimum**, you can make a Python venv if needed.
```bash
python3 --version
```

```bash
pip3 install qgis-plugin-manager
python3 -m pip install qgis-plugin-manager
```

## Environment variable

QGIS-Plugin-Manager will take care of following variables :

* `QGIS_PLUGIN_MANAGER_SOURCES_FILE` for storing a path to the `sources.list` otherwise, the current folder will be used.
* `QGIS_PLUGIN_MANAGER_CACHE_DIR` for storing all XML files downloaded otherwise, the current folder will be used `.cache_qgis_plugin_manager`
* `QGIS_PLUGIN_MANAGER_SKIP_SOURCES_FILE`, boolean when we do not need a `sources.list` file, for instance to list plugins only
* `QGIS_PLUGIN_MANAGER_RESTART_FILE`, path where the file must be created if QGIS server needs to be restarted.
  Read [the documentation](README.md#notify-upstream-if-a-restart-is-needed).
* `QGIS_PLUGINPATH` for storing plugins, from [QGIS Server documentation](https://docs.qgis.org/latest/en/docs/server_manual/config.html#environment-variables)
* `PYTHONPATH` for importing QGIS libraries

## Utilisation

**Either** you need to go in the directory where you are storing plugins, **or** you can use the environment variable `QGIS_PLUGINPATH`.
You can read the [documentation](https://docs.qgis.org/3.22/en/docs/server_manual/config.html#environment-variables)
on QGIS Server about this variable.

```bash
cd /path/where/you/have/plugins
# usually
cd /usr/lib/qgis/plugins
```

```bash
$ qgis-plugin-manager --help
usage: qgis-plugin-manager [-h] [-v] {init,list,remote,remove,update,upgrade,cache,search,install} ...

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit

commands:
  qgis-plugin-manager command

  {init,list,remote,remove,update,upgrade,cache,search,install}
    init                Create the `sources.list` with plugins.qgis.org as remote
    list                List all plugins in the directory
    remote              List all remote server
    remove              Remove a plugin by its name
    update              Update all index files
    upgrade             Upgrade all plugins installed
    cache               Look for a plugin in the cache
    search              Search for plugins
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

------------------------------------------------------------------------------------------------------------------------------------
|  Name            |  Version  | Flags           |  QGIS min  |  QGIS max  |  Author         | Folder owner     | Action ⚠         |
------------------------------------------------------------------------------------------------------------------------------------
|Lizmap            |master     |                 |3.4         |3.99        |3Liz             | root : 0o755     | Unkown version   |
|wfsOutputExtension|1.5.3      |Server           |3.0         |            |3Liz             | etienne : 0o755  |                  |
|QuickOSM          |1.14.0     |Processing       |3.4         |3.99        |Etienne Trimaille| etienne : 0o755  | Upgrade to 1.16.0|
|cadastre          |1.6.2      |Server,Processing|3.0         |3.99        |3liz             | www-data : 0o755 |                  |
|atlasprint        |3.2.2      |Server           |3.10        |            |3Liz             | www-data : 0o755 |                  |
------------------------------------------------------------------------------------------------------------------
```

#### Install needed plugins only, mainly on QGIS server

**Important note**, install **only** plugins you need **you**. On QGIS **desktop**, plugins can slow down your computer.
On QGIS **server**, plugins are like **hooks** into QGIS server, they can alter input or output of QGIS server.
They can produce **unexpected** result if you don't know how the plugin works. Please refer to their respective documentation
or the application that needs QGIS server plugins (for instance,
[plugins for Lizmap Web Client](https://docs.lizmap.com/current/en/install/pre_requirements.html#qgis-server-plugins))

### Remote

```bash
$ qgis-plugin-manager remote
List of remotes :

https://plugins.qgis.org/plugins/plugins.xml?qgis=3.22

$ cat sources.list 
https://plugins.qgis.org/plugins/plugins.xml?qgis=[VERSION]
```

`[VERSION]` is a token in the `sources.list` file to be replaced by the QGIS version, for instance `3.22`.
If QGIS is upgraded, the XML file will be updated as well.

You don't have to set the TOKEN for all URL : 

`https://docs.3liz.org/plugins.xml` is valid.

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

### Search

Look for plugins according to tags and title :

```bash
$ qgis-plugin-manager search dataviz
Data Plotly
QSoccer
```

### Install

Plugins are case-sensitive and might have spaces in its name :
```bash
$ qgis-plugin-manager install dataplotly
Plugin dataplotly latest not found.
Do you mean maybe 'Data Plotly' ?
$ qgis-plugin-manager install 'Data Plotly'
```

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

You can use `--force` or `-f` to force the installation even if the plugin with the same version is already installed.

### Upgrade

Upgrade all plugins installed :

```bash
$ qgis-plugin-manager upgrade
```

You can use `--force` or `-f` to force the upgrade for all plugins despite their version.

*Note*, like APT, `update` is needed before to refresh the cache.

### Remove

It's possible to use `rm -rf folder_dir` but you can also remove by the plugin name.
It will take care of the `QGIS_PLUGINPATH` environment variable.

```bash
$ qgis-plugin-manager remove Quickosm
Plugin name 'Quickosm' not found
Do you mean maybe 'QuickOSM' ?
$ qgis-plugin-manager remove QuickOSM
Plugin QuickOSM removed
Tip : Do not forget to restart QGIS Server to reload plugins 😎
```

### Notify upstream if a restart is needed

When a plugin is installed or removed and if the environment variable `QGIS_PLUGIN_MANAGER_RESTART_FILE` is set,
an empty file will be created or touched. It can notify you if QGIS Server needs to be restarted for instance.

Note that you must manually remove this file.

## Run tests

```bash
export PYTHONPATH=/home/etienne/dev/app/qgis-master/share/qgis/python/:/usr/lib/python3/dist-packages/
cd test
python3 -m unittest
flake8
```
