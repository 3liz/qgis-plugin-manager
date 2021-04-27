from typing import NamedTuple


class Plugin(NamedTuple):
    name: str = None
    description: str = None
    version: str = None
    qgis_minimum_version: str = None
    homepage: str = None
    prerelease: str = None
    file_name: str = None
    icon: str = None
    author_name: str = None
    download_url: str = None
    uploaded_by: str = None
    create_date: str = None
    update_date: str = None
    experimental: str = None
    deprecated: str = None
    tracker: str = None
    repository: str = None
    tags: str = None
