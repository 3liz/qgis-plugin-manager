# QGIS-Plugin-Manager

[![Tests](https://github.com/3liz/qgis-plugin-manager/actions/workflows/release.yml/badge.svg)](https://github.com/3liz/qgis-plugin-manager/actions/workflows/release.yml)
[![PyPi version badge](https://badgen.net/pypi/v/qgis-plugin-manager)](https://pypi.org/project/qgis-plugin-manager/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/qgis-plugin-manager)](https://pypi.org/project/qgis-plugin-manager/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qgis-plugin-manager)](https://pypi.org/project/qgis-plugin-manager/)

A cli tool for handling installed QGIS plugins. 

Mainly designed for managing QGIS Server plugins, it also works for QGIS  desktop
plugins.

Not tested on Windows.

## Installation

Python 3.9 **minimum**, you can make a Python venv if needed.
```bash
python3 --version
```

```bash
pip3 install qgis-plugin-manager
python3 -m pip install qgis-plugin-manager
```

## Environment variables

QGIS-Plugin-Manager will take care of following variables :

* `QGIS_PLUGIN_MANAGER_SOURCES_FILE` for storing a path to the `sources.list` otherwise, the current folder will be used.
* `QGIS_PLUGIN_MANAGER_CACHE_DIR` for storing all XML files downloaded otherwise, the current folder will be used `.cache_qgis_plugin_manager`
* `QGIS_PLUGIN_MANAGER_RESTART_FILE`, path where the file must be created if QGIS server needs to be restarted.
* `QGIS_PLUGIN_MANAGER_INCLUDE_PRERELEASE`, boolean for including prerelease, development 
or experimental versions of plugins.
  Read [the documentation](README.md#notify-upstream-if-a-restart-is-needed).
* `QGIS_PLUGINPATH` for storing plugins, from [QGIS Server documentation](https://docs.qgis.org/latest/en/docs/server_manual/config.html#environment-variables)
* `PYTHONPATH` for importing QGIS libraries

## Utilisation

**Either** you need to go in the directory where you are storing plugins, **or** you can use the environment variable `QGIS_PLUGINPATH`.
You can read the [documentation](https://docs.qgis.org/latest/en/docs/server_manual/config.html#environment-variables)
on QGIS Server about this variable.

```bash
cd /path/where/you/have/plugins
# usually on a server
cd /usr/lib/qgis/plugins
# on unix desktop with the default QGIS profile
cd /home/${USER}/.local/share/QGIS/QGIS3/profiles/default/python/plugins
# or
export QGIS_PLUGINPATH=/path/where/you/have/plugins
```

```bash
$ qgis-plugin-manager --help
usage: qgis-plugin-manager [-h] [-v] {version,init,list,remote,remove,update,upgrade,cache,search,install} ...

options:
  -h, --help            show this help message and exit
  -v, --verbose         Activate verbose (debug) mode (default: False)

commands:
  qgis-plugin-manager command

  {version,init,list,remote,remove,update,upgrade,cache,search,install}
    version             Show version informations and exit
    init                Create the `sources.list` with plugins.qgis.org as remote
    list                List all plugins in the directory
    install             Install a plugin
    remove              Remove a plugin by its name
    upgrade             Upgrade all plugins installed
    remotes             List all remote server
    update              Update all index files
    versions            Look for available plugin versions
    search              Search for plugins
    check               Check compatibility of installed plugins with QGIS version
```

### Init

To create the first `sources.list` in the directory with at least the default repository https://plugins.qgis.org :
```bash
$ qgis-plugin-manager init
$ cat sources.list 
https://plugins.qgis.org/plugins/plugins.xml?qgis=3.34
```

You can have one or many servers, one on each line.

### List

List all plugins installed :

```bash
$ qgis-plugin-manager list

Name               Version Folder
------------------ ------- -------------
Lizmap server      2.13.1  lizmap_server
atlasprint         3.4.3                
cadastre           2.1.1                
wfsOutputExtension 1.8.3 
```

List outdated plugins including prerelease/experimental versions


```bash
$ qgis-plugin-manager list --outdated --pre

Name          Version Latest       Folder
------------- ------- ------------ -------------
Lizmap server 2.13.1  2.13.2-alpha lizmap_server
cadastre      2.1.1   2.1.2-alpha            
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

https://plugins.qgis.org/plugins/plugins.xml?qgis=3.34

$ cat sources.list 
https://plugins.qgis.org/plugins/plugins.xml?qgis=[VERSION]
```

`[VERSION]` is a token in the `sources.list` file that is  to be replaced by the current QGIS version available on your system (ex: 3.40)

If QGIS is upgraded, the XML file will be updated as well.

You don't have to set the TOKEN for all URL : 

`https://docs.3liz.org/plugins.xml` is valid.

#### Basic authentication

It's possible to add a login and password in the remote URL, with `username` and `password` in the query string :

```bash
https://docs.3liz.org/private/repo.xml?username=login&password=pass
```

Every URL is parsed, and if some credentials are found, the URL is cleaned and the request is done using the
basic authentication.

### Update

To fetch the XML files from each repository :

```bash
$ qgis-plugin-manager update
Downloading https://plugins.qgis.org/plugins/plugins.xml?qgis=3.34...
	Ok
$ ls .cache_qgis_plugin_manager/
https-plugins-qgis-org-plugins-plugins-xml-qgis-3-34.xml
```

### Versions

Check available versions of a plugin including prerelease/experimental versions:

```bash
$ qgis-plugin-manager versions cadastre --pre

cadastre

Version QGIS min Status Source
------- -------- ------ ------------------------------------------------------
2.2.0   3.28.0   ST     https://plugins.qgis.org/plugins/plugins.xml?qgis=3.40
1.6.2   3.0.0    SXT    https://plugins.qgis.org/plugins/plugins.xml?qgis=3.40

Status: S = Server, X = Experimental, D = Deprecated, T = Trusted
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

#### Enable a plugin

On QGIS **server**, there isn't any setting to enable/disable a plugin.

However, on **desktop**, you still need to enable a plugin, the equivalent of the checkbox in the QGIS graphical plugin
manager.

For instance, with the default profile, usually located in :

```bash
/home/${USER}/.local/share/QGIS/QGIS3/profiles/default/QGIS/
```

you need to edit the `QGIS.ini` file with :

```ini
[PythonPlugins]
nameOfThePlugin=true
```

### Upgrade

Upgrade all plugins installed :

```bash
$ qgis-plugin-manager upgrade
```

You can use `--force` or `-f` to force the upgrade for all plugins despite their version.

*Note*, like APT, `update` is needed before to refresh the cache.

#### Ignore plugins from the upgrade

Some plugins might be installed by hand, without being installed with a remote. This command will try to upgrade
**all valid** plugins found in the directory. However, the command will fail because the plugin has been installed 
without a remote.

It's possible to ignore such plugin by adding a file `ignorePlugins.list`, in your plugins' folder,
with a list of **plugin name** on each line. The `upgrade` will not try to upgrade them.

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

This is useful for a deployment with [Ansible](https://www.ansible.com/) for instance.

Note that you must manually remove this file.

## Run tests

NOTE: Use a virtual env (python3 -m venv)

```bash
pip install -e .
cd tests
pytest -v
```
