from typing import (
    List,
    NamedTuple,
    Optional,
)


class Plugin(NamedTuple):
    """Definition of a plugin in the XML file."""

    file_name: Optional[str] = None
    name: Optional[str] = None
    description: str = ""
    version: str = ""
    search: List[str] = []  # noqa RUF012
    qgis_minimum_version: Optional[str] = None
    qgis_maximum_version: Optional[str] = None
    homepage: Optional[str] = None
    pre_release: Optional[str] = None
    icon: Optional[str] = None
    author_name: Optional[str] = None
    download_url: Optional[str] = None
    uploaded_by: Optional[str] = None
    create_date: Optional[str] = None
    update_date: Optional[str] = None
    experimental: Optional[str] = None
    deprecated: Optional[str] = None
    tracker: Optional[str] = None
    repository: Optional[str] = None
    tags: Optional[str] = None
    server: bool = False
    has_processing: bool = False
    has_wps: bool = False


class Level:
    """Color in terminal."""

    Success = "\033[92m"
    Alert = "\033[93m"
    Critical = "\033[91m"
    End = "\033[0m"
