import json
import os
import shutil

from io import StringIO
from pathlib import Path
from typing import (
    Sequence,
)

import pytest

from qgis_plugin_manager import echo
from qgis_plugin_manager.__main__ import (
    LocalDirectory,
    Remote,
    cli,
    get_plugin_path,
    qgis_server_version,
)
from qgis_plugin_manager.utils import getenv_bool


@pytest.fixture(scope="session")
def cli_plugindir(rootdir: Path) -> Path:
    return rootdir.joinpath(".cli_artifacts")


@pytest.fixture(scope="module")
def cli_setup_cache(rootdir: Path, cli_plugindir: Path):
    workdir = cli_plugindir
    os.environ["QGIS_PLUGINPATH"] = str(workdir)
    workdir.mkdir(exist_ok=True)

    plugin_path = get_plugin_path()
    assert plugin_path == workdir

    # Cleanup plugin folders
    if getenv_bool("CI_CLI_TESTS_REMOVE_PLUGINS"):
        localdir = LocalDirectory(plugin_path)
        for folder in localdir.plugin_list():
            path = cli_plugindir.joinpath(folder)
            if path.exists():
                echo.alert(f"::Removing folder: {path}")
                shutil.rmtree(path)

    if not workdir.joinpath("sources.list").exists():
        Remote.create_sources_file(workdir, None)

    remote = Remote(plugin_path, qgis_server_version() or "3.40")
    if not remote.cache_directory().exists():
        remote.update()

    yield

    del os.environ["QGIS_PLUGINPATH"]


@pytest.fixture
def cli_output(cli_setup_cache: None) -> StringIO:
    buf = StringIO()

    def redirect_echo(msg: str):
        buf.write(msg)
        buf.write("\n")
        print(msg)

    saved = echo.echo
    echo.echo = redirect_echo
    yield buf
    echo.echo = saved


def run_cli(arguments: Sequence[str]):
    args = cli.parse_args(arguments)
    assert "func" in args
    args.func(args)


def test_cmd_version(cli_output: StringIO):
    run_cli(["version"])


def test_cmd_install(cli_output: StringIO, cli_plugindir: Path):
    run_cli(["install", "-U", "-f", "Lizmap server", "wfsOutputExtension"])

    localdir = LocalDirectory(get_plugin_path())
    for folder in localdir.plugin_list():
        assert cli_plugindir.joinpath(folder).exists()


def test_cmd_install_plugin_version(cli_output: StringIO):
    run_cli(["install", "-f", "atlasprint==3.3.2"])

    localdir = LocalDirectory(get_plugin_path())
    assert "atlasprint" in tuple(localdir.plugin_list().values())


def test_cmd_list(cli_output: StringIO):
    run_cli(["list", "--format=columns"])
    run_cli(["list", "--format=list"])

    cli_output.seek(0)
    cli_output.truncate(0)

    run_cli(["list", "--format=json"])

    plugins = json.loads(cli_output.getvalue())
    assert len(plugins) == 3
    assert plugins[0]["name"] == "atlasprint"
    assert plugins[1]["name"] == "Lizmap server"
    assert plugins[2]["name"] == "wfsOutputExtension"


def test_cmd_list_outdated(cli_output: StringIO):
    run_cli(["list", "-o", "--format=json"])

    plugins = json.loads(cli_output.getvalue())
    # Should be one outdated 'atlasprint'
    assert len(plugins) == 1
