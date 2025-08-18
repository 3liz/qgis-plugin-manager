from pathlib import Path
from unittest import TestCase

from qgis_plugin_manager.remote import Remote


def test_list_remote(plugins: Path):
    """ Test read the sources.list file. """
    remote = Remote(plugins)
    TestCase().assertCountEqual(
        ["https://my.url/plugins.xml", "https://my.repo/plugins.xml"],
        remote.remote_list(),
    )


def test_plugin_name_with_space_and_tags(fixtures: Path):
    """ Test plugin with different name, using tags. """
    xml_files = fixtures.joinpath("xml_files")
    remote = Remote(xml_files.joinpath("dataplotly"))
    plugins = remote._parse_xml(xml_files.joinpath("dataplotly/dataplotly.xml"), {})
    assert plugins == {'Data Plotly': "0.4"}
    assert len(remote.list_plugins) == 1

    plugin = remote.list_plugins.get('Data Plotly')
    assert plugin is not None
    assert plugin.name == "Data Plotly"
    assert plugin.tags == "vector,python,d3,plots,graphs,datavis,dataplotly,dataviz"
    assert plugin.search == [
        "data plotly", "dataplotly", "vector",
        "python", "d3", "plots", "graphs", "datavis", "dataviz", "data", "plotly",
    ]

    # Test the search
    assert remote.search("foo") == []
    assert remote.search("dataviz", strict=False) == ["Data Plotly"]
    assert remote.search("dataplotly", strict=False) == ["Data Plotly"]


def test_search_with_space_in_name(fixtures: Path):
    """ Test Lizmap should give 2 values : Lizmap and 'Lizmap server'. """
    xml_files = fixtures.joinpath("xml_files")
    remote = Remote(xml_files.joinpath("lizmap"))
    plugins = remote._parse_xml(xml_files.joinpath("lizmap/lizmap.xml"), {})
    assert len(remote.list_plugins) == 2
    assert plugins == {
        "Lizmap": "3.7.4",
        "Lizmap server": "1.0.0",
    }

    plugin = remote.list_plugins.get("Lizmap server")
    assert plugin is not None
    assert plugin.name == "Lizmap server"
    assert plugin.search == [
        "lizmap server", "lizmapserver", "web", "cloud", "lizmap", "server",
    ]

    # Test the search
    assert remote.search("lizmap", strict=False) == ['Lizmap', 'Lizmap server']


def test_qgis_dev_version():
    """ Test check QGIS dev version number. """
    assert ["3", "22", "11"] == Remote.check_qgis_dev_version('3.22.11')
    assert ["3", "24", "0"] == Remote.check_qgis_dev_version('3.23.0')


def test_user_agent(fixtures: Path):
    """ Test the User-Agent. """
    remote = Remote(fixtures.joinpath("xml_files", "lizmap"))
    assert "Mozilla/5.0 QGIS/" in remote.user_agent()


def test_parse_url():
    """ Test to parse a URL for login&password. """
    creds = Remote.credentials(
        "https://foo.bar/plugins.xml?qgis=3.10&username=login&password=pass",
    )
    assert creds == ('https://foo.bar/plugins.xml?qgis=3.10', 'login', 'pass')

    creds = Remote.credentials("https://foo.bar/plugins.xml?qgis=3.10")
    assert creds == ('https://foo.bar/plugins.xml?qgis=3.10', '', '')


def test_clean_remote():
    """ Test to clean a URL from login&password. """
    # "password", the keyword to look for
    name = Remote.public_remote_name(
        "https://foo.bar/plugins.xml?qgis=3.10&username=login&password=pass",
    )
    assert name == "https://foo.bar/plugins.xml?qgis=3.10&username=login&password=%2A%2A%2A%2A%2A%2A"

    # "pass", not the keyword to look for
    name = Remote.public_remote_name(
        "https://foo.bar/plugins.xml?qgis=3.10&username=login&pass=pass",
    )
    assert name == "https://foo.bar/plugins.xml?qgis=3.10&username=login&pass=pass"
    # Nothing
    name = Remote.public_remote_name("https://foo.bar/plugins.xml?qgis=3.10")
    assert name == "https://foo.bar/plugins.xml?qgis=3.10"
