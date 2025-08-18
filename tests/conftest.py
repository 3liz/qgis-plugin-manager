from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def rootdir(request: pytest.FixtureRequest) -> Path:
    return Path(request.config.rootdir.strpath)  # type: ignore [attr-defined]


@pytest.fixture(scope="session")
def fixtures(rootdir: Path) -> Path:
    return rootdir.joinpath("fixtures")


@pytest.fixture(scope="session")
def plugins(fixtures: Path) -> Path:
    return fixtures.joinpath("plugins")
