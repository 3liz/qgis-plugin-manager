import os
import shutil

from pathlib import Path

import pytest

from qgis_plugin_manager.local_directory import LocalDirectory
from qgis_plugin_manager.remote import Remote


@pytest.fixture
def remote_sources(fixtures: Path):
    sources_file = fixtures.joinpath("remote_sources.list")
    os.environ["QGIS_PLUGIN_MANAGER_SOURCES_FILE"] = str(sources_file)
    yield sources_file
    del os.environ["QGIS_PLUGIN_MANAGER_SOURCES_FILE"]


@pytest.fixture
def teardown_downloaded_plugins(plugins: Path):
    yield

    plugin_path = plugins.joinpath("QuickOSM")
    if plugin_path.exists():
        print("\n::removing", plugin_path)
        shutil.rmtree(plugin_path)


@pytest.mark.skipif(os.getenv("CI") != "true", reason="Only run on CI")
def test_install_network(
    plugins: Path,
    remote_sources: Path,
    teardown_downloaded_plugins: None,
):
    plugin_name = "QuickOSM"
    plugin_path = plugins.joinpath(plugin_name)

    """ Test install QuickOSM with a specific version, remove and try the latest. """
    assert not plugin_path.exists()

    local = LocalDirectory(plugins)
    assert plugin_name not in local.plugin_list()

    remote = Remote(plugins, qgis_version="3.34")
    remote.update()

    versions = remote.available_plugins().get(plugin_name)
    assert versions is not None

    print("\n::teardown_local::", plugin_name, "versions:", ",".join(str(p.version) for p in versions))

    assert len(versions) >= 2

    version = versions[1].version
    remote.install(plugin_name, str(version))
    assert plugin_path.exists()

    local.list_plugins()
    assert version == local.plugin_info(plugin_name).version

    latest = remote.latest(plugin_name, include_prerelease=True)
    assert latest.version != version
    assert latest.version == versions[0].version

    remote.install(plugin_name, include_prerelease=True)
    local.list_plugins()
    assert plugin_path.exists()
    assert latest.version == local.plugin_info(plugin_name).version


@pytest.fixture
def protocols(fixtures: Path) -> Path:
    return fixtures.joinpath("xml_files", "file_protocol")


@pytest.fixture
def teardown_local(protocols: Path):
    yield

    destinations = protocols.joinpath("minimal_plugin")
    if destinations.exists():
        shutil.rmtree(destinations)

    cache_folder = protocols.joinpath(".cache_qgis_plugin_manager")
    if cache_folder.exists():
        shutil.rmtree(cache_folder)

    sources_list = protocols.joinpath("sources.list")
    if sources_list.exists():
        sources_list.unlink()


def test_install_local(protocols: Path, teardown_local: None):
    """Test install local file."""
    folder = protocols
    folder.joinpath("sources.list").touch()
    folder.joinpath(".cache_qgis_plugin_manager").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        folder.joinpath("plugin.xml"),
        folder.joinpath(".cache_qgis_plugin_manager/plugins.xml"),
    )

    remote = Remote(folder)
    remote._parse_xml(folder.joinpath("plugin.xml"), remote._list_plugins)
    assert "1.0.0" == remote._list_plugins["Minimal"][0].version

    local = LocalDirectory(folder)
    assert local.plugin_info("Minimal") is None

    remote.install("Minimal", remove_zip=False)

    local.list_plugins()
    assert local.plugin_info("Minimal").version == "1.0.0"
    assert "minimal_plugin" in list(local.plugin_list().keys())

    # Test to remove the plugin
    assert not local.remove("minimal")
    assert local.remove("Minimal")

    local = LocalDirectory(folder)
    assert local.plugin_info("Minimal") is None
