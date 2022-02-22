# Changelog

## Unreleased

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
