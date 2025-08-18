from pathlib import Path
from unittest import TestCase

import pytest

from qgis_plugin_manager.local_directory import LocalDirectory


@pytest.fixture
def local_dir(plugins: Path) -> LocalDirectory:
    yield LocalDirectory(plugins)


def test_list_existing_plugins(local_dir: LocalDirectory):
    """ Test to find existing plugins. """
    case = TestCase()
    case.assertCountEqual(['plugin_a', 'plugin_b'], local_dir.plugin_list())
    case.assertCountEqual(['missing_init', 'missing_metadata'], local_dir.invalid)
    assert local_dir.plugin_installed_version('Plugin A') == "1.0.0"
    assert local_dir.plugin_installed_version('Plugin Z') is None


def test_read_metadata(local_dir: LocalDirectory):
    """ Test read metadata. """
    local_dir.plugin_metadata('do_not_exist', 'author') is None
    local_dir.plugin_metadata('missing_init', 'author') is None
    local_dir.plugin_metadata('missing_metadata', 'author') is None

    assert "Hazel Nutt" == local_dir.plugin_metadata('plugin_a', 'author')
    assert "" == local_dir.plugin_metadata('plugin_a', 'do_not_exist')

    # Plugin A
    plugin = local_dir.plugin_info('plugin_a')
    assert 'Plugin A' == plugin.name
    assert '1.0.0' == plugin.version
    assert '' == plugin.experimental
    assert '3.0' == plugin.qgis_minimum_version
    assert '' == plugin.qgis_maximum_version
    assert 'Hazel Nutt' == plugin.author_name
    assert plugin.server
    assert plugin.has_processing
    assert not plugin.deprecated

    # Plugin B
    plugin = local_dir.plugin_info('plugin_b')
    assert not plugin.server
    assert not plugin.has_processing
    assert not plugin.deprecated
