# Changelog

## Unreleased

* Add a new `remove` command to use the plugin name
* Review some exit code when using as a CLI tool
* Manage ZIP files which are using `file:` protocol
* Bump Python minimum version to 3.8

## 1.2.1 - 2022-09-30

* Better wording when the remote XML has not been fetched and show the list of plugins
* New environment variable `QGIS_PLUGIN_MANAGER_SKIP_SOURCES_FILE` to show a warning when we don't need a `sources.list`

## 1.2.0 - 2022-09-23

* Switch to QGIS 3.22 for the default version
* If a development version of QGIS is detected (eg 3.27), use the next stable version of QGIS (3.28).
* New environment variable `QGIS_PLUGIN_MANAGER_SOURCES_FILE` and `QGIS_PLUGIN_MANAGER_CACHE_DIR` to store settings.

## 1.1.4 - 2022-06-16

* Display if the plugin has a WPS provider in its metadata.txt file
* Fix Python error if the username is not found, when it's used in Docker for instance

## 1.1.3 - 2022-06-16

* If the environment variable `QGIS_PLUGINPATH` is set, this directory is used instead of the current directory
* Fix display issue when the error was printed many times in the terminal

## 1.1.2 - 2022-06-13

* Fix Python exception if the "init" or "update" commands were not executed

## 1.1.1 - 2022-05-19

* Fix the search when there is a space in the plugin name
* Fix some Python errors and typo

## 1.1.0 - 2022-05-10

* Show different flags about plugins : server, deprecated, processing

## 1.0.3 - 2022-03-09

* Order the plugin list by folder name
* Show file permissions warning if there are more than 2 different values

## 1.0.2 - 2022-03-09

* Display `PYTHONPATH` when QGIS library is not found
* Display tip to restart QGIS Server after a plugin installation

## 1.0.1 - 2022-03-02

* Better warning when we are not in the correct directory without any plugin
* Better warning when the user can not extract the ZIP in the folder

## 1.0.0 - 2022-02-24

* Add a `search` command to search plugins among tags and names
* Add an `upgrade` command to upgrade all plugins installed
* Add an example with a plugin having a space in its name
* Add some information about the user and file permissions when showing plugins
* Display plugin name similarity when installing if the given name is not found
* Display a better error message if the folder/file can not be removed

## 0.4.1 - 2022-02-14

* Fix a Python error when not the encoding was not set when opening files

## 0.4.0 - 2022-01-10

* Adds some colors in the terminal
* Better management of QGIS upgrade when the version was hardcoded in the `sources.list` file
* Fix an issue about version name
* Refactoring the code

## 0.3.0 - 2021-08-09

* Better error message if the plugin is not found and return 1 for return code
* Use the QGIS API to determine the QGIS installed version

## 0.2.0 - 2021-06-24

* Fix some issues, CLI still in beta
* Fix Python error when the cache directory was not existing
* Fix when the cache was empty to fetch new plugins

## 0.1.0 - 2021-05-25

* First beta version
