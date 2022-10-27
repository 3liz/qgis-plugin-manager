from typing import NamedTuple

__copyright__ = 'Copyright 2021, 3Liz'
__license__ = 'GPL version 3'
__email__ = 'info@3liz.org'


class Plugin(NamedTuple):
    """ Definition of a plugin in the XML file. """
    name: str = None
    description: str = None
    version: str = None
    search: list = []
    qgis_minimum_version: str = None
    qgis_maximum_version: str = None
    homepage: str = None
    pre_release: str = None
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
    server: bool = False
    has_processing: bool = False
    has_wps: bool = False


class Level:
    """ Color in terminal. """
    Success = '\033[92m'
    Alert = '\033[93m'
    Critical = '\033[91m'
    End = '\033[0m'
