# QGIS-Plugin-Manager

Mainly designed for QGIS Server plugins.

## TODO

**WIP** for now.

Not tested on Windows.

todo list :
* exit code
* API
* publish pypi.org

`QGIS_EXEC_PATH` environment variable if QGIS Server is not located at `/usr/lib/cgi-bin/qgis_mapserv.fcgi`

## Installation

Python 3.6 minimum
```bash
python3 --version
```

```bash
pip3 install git+https://github.com/Gustry/qgis-plugin-manager.git
# Soon
# pip3 install qgis-plugin-manager
# python3 -m pip install qgis-plugin-manager
```

```bash
cd /path/where/you/have/plugins
qgis-plugin-manager init
qgis-plugin-manager list
```

## Utilisation

Have a `sources.list` in the directory with at least a line, like the default https://plugins.qgis.org :
```
https://plugins.qgis.org/plugins/plugins.xml?qgis=3.10
```

You can have one or many servers, one on each line.

```bash
qgis-plugin-manager list
qgis-plugin-manager remote
qgis-plugin-manager update
qgis-plugin-manager cache PLUGIN_NAME
qgis-plugin-manager install PLUGIN_NAME
qgis-plugin-manager install PLUGIN_NAME==VERSION
# qgis-plugin-manager info PLUGIN_NAME
```
