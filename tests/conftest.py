from pathlib import Path

import pytest

from qgis_plugin_manager import echo


@pytest.fixture(scope="session", autouse=True)
def verbose() -> None:
    echo.set_verbose_mode(True)


@pytest.fixture(scope="session")
def rootdir(request: pytest.FixtureRequest) -> Path:
    return Path(request.config.rootdir.strpath)  # type: ignore [attr-defined]


@pytest.fixture(scope="session")
def fixtures(rootdir: Path) -> Path:
    return rootdir.joinpath("fixtures")


@pytest.fixture(scope="session")
def plugins(fixtures: Path) -> Path:
    return fixtures.joinpath("plugins")
