from pathlib import Path
from unittest import TestCase

import pytest

from qgis_plugin_manager.local_directory import LocalDirectory


@pytest.fixture
def local_dir(plugins: Path) -> LocalDirectory:
    yield LocalDirectory(plugins)


def test_list_existing_plugins(local_dir: LocalDirectory):
    """Test to find existing plugins."""
    case = TestCase()
    case.assertCountEqual(["plugin_a", "plugin_b"], local_dir.plugin_list())
    assert local_dir.plugin_info("Plugin A") is not None
    assert local_dir.plugin_info("Plugin Z") is None


def test_read_metadata(local_dir: LocalDirectory):
    """Test read metadata."""
    assert local_dir._plugins_metadata.get("do_not_exist") is None
    assert local_dir._plugins_metadata.get("missing_init") is None
    assert local_dir._plugins_metadata.get("missing_metadata") is None

    assert "Hazel Nutt" == local_dir._plugins_metadata["plugin_a"]["author"]
    assert local_dir._plugins_metadata["plugin_a"].get("do_not_exist") is None

    # Plugin A
    plugin = local_dir.plugin_info("plugin_a")
    assert "Plugin A" == plugin.name
    assert "1.0.0" == plugin.version
    assert not plugin.experimental
    assert "3.0" == plugin.qgis_minimum_version
    assert plugin.qgis_maximum_version is None
    assert "Hazel Nutt" == plugin.author_name
    assert plugin.server
    assert plugin.has_processing
    assert not plugin.deprecated

    # Plugin B
    plugin = local_dir.plugin_info("plugin_b")
    assert not plugin.server
    assert not plugin.has_processing
    assert not plugin.deprecated
