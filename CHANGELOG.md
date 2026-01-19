# Changelog

## Unreleased

* Fix default 'format' for deprecated 'cache' command 

## 1.7.4 - 2025-12-15

### Fixed

* Fix crash when checking for already installed plugin on 'install' command"

## 1.7.3

### Fixed

* Dont fail install on non-semver version request [FIX #86]

## 1.7.2

### Added

* Allow overriding/faking QGIS installation with the 
  `QGIS_PLUGIN_MANAGER_QGIS_VERSION` environment variable.

### Changed

* Removed the needs for `QGIS_PLUGIN_MANAGER_SKIP_SOURCES_FILE`
* Deprecate the `freeze` format in `list` command
* List's `list` format output the installed plugin version or the
  latest plugin version with the `--outdated` option.

### Fixed

* Fix request for specific plugin version.

## 1.7.1 - 2025-09-01

### Fixed

* Handle empty sequence in `print_table`

## 1.7.0 - 2025-09-01

### Added

* Added 'check' command for checking QGIS compatibility of installed plugins 
* Added 'versions' command that output all available versions 
  for the same plugin
* Added options '--fix-permissions', '--upgrade'  for the 'install' command
* Changed the 'list' command output: the command now support multiple output
  formats: 'list', 'freeze', 'columns', 'json'.
* Added '--pre' option for including prerelease, development or experimental version
  in 'install', 'search' and 'list' commands

### Changed

* The 'cache' command is now deprecated.
* Move packaging configuration to pyproject.toml 

### Fixed

* Handle plugin versions as SemVer version schemes
* Fix installation of experimental plugins
* Improve output of 'update' command
* Use templated remote definition in 'init' as default
* Allow forcing QGIS version in the 'init' command

### Removed

* Dropped support for Python 3.8

## 1.6.5 - 2025-06-13

### Fixed

* Fix for installing a specific version of a plugin, contribution from @benz0li

## 1.6.4 - 2025-05-20

### Added

* Support for Python 3.13

### Removed

* Drop support for Python 3.7

## 1.6.3 - 2024-05-15

### Fixed

* Fix packaging issue

## 1.6.2 - 2024-05-15

### Added

* Support for Python 3.12

### Changed

* Change the User-Agent to be compliant with https://plugins.qgis.org
* Change from `X` to `*` for passwords when showing them

## 1.6.1 - 2023-07-06

### Fixed

* Always provide a QGIS version when using `remote`, `cache` and `search`

## 1.6.0 - 2023-06-12

### Added

* Add support for basic authentication when downloading XML and ZIP files which are in a private repository.

## 1.5.0 - 2023-01-24

### Added

* Add a new `ignorePlugins.list` file to ignore some plugins when using the `upgrade` command.

### Fixed

* Update the readme about QGIS desktop and plugin activation
* Catch Python exception if :
  * the remote does not exist when downloading
  * the directory is not writable

## 1.4.2 - 2022-12-13

### Fixed

* Improve compatibility with Windows
* Improve wording when the `QGIS_PLUGINPATH` environment variable was used or not

### Added

* Support for Python 3.11

## 1.4.1 - 2022-11-08

### Fixed

* Fix display of plugin name when the plugin was not found

## 1.4.0 - 2022-10-27

### Added

* Add new `--force` or `-f` to `install` and `upgrade` commands

### Fixed

* Fix QGIS version detection when showing the list of plugin

## 1.3.2 - 2022-10-27

### Fixed

* Regression from 1.3.0 about the `update` command

## 1.3.1 - 2022-10-27

### Fixed

* Regression from 1.3.0 about the `update` command

## 1.3.0 - 2022-10-27

### Added

* Add a new `remove` command with the plugin name (not the folder name)
* New environment variable `QGIS_PLUGIN_MANAGER_RESTART_FILE` to notify if a restart of QGIS Server is needed
* Manage ZIP files which are using `file:` protocol

### Changed

* Do not try to replace QGIS version when installing/upgrading a plugin. This will impact remotes having `[VERSION]`
  and no QGIS version could be detected at runtime
* The `update` is not done anymore automatically when the cache was not present

### Fixed

* Review some exit codes when using as a CLI tool with Ansible for instance
* Only install or upgrade plugins if it's needed, compared to the plugin already installed

### Changed

* Bump Python minimum version to 3.7

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
