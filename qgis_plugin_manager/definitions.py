from typing import (
    Dict,
    List,
    NamedTuple,
    Optional,
    Protocol,
    Union,
)

from semver import Version

from .utils import get_semver_version


class Element(Protocol):
    attrib: Dict[str, str]

    def __iter__(self): ...


TRUE_VALUES = ("true", "yes", "1")


class Plugin(NamedTuple):
    """Definition of a plugin in the XML file."""

    name: str
    version: Version
    version_str: str
    file_name: Optional[str] = None
    download_url: Optional[str] = None
    description: str = ""
    search: List[str] = []  # noqa RUF012
    qgis_minimum_version: Optional[Version] = None
    qgis_maximum_version: Optional[Version] = None
    homepage: Optional[str] = None
    pre_release: Optional[str] = None
    icon: Optional[str] = None
    author_name: Optional[str] = None
    uploaded_by: Optional[str] = None
    create_date: Optional[str] = None
    update_date: Optional[str] = None
    experimental: bool = False
    deprecated: bool = False
    tracker: Optional[str] = None
    repository: Optional[str] = None
    tags: Optional[str] = None
    server: bool = False
    has_processing: bool = False
    has_wps: bool = False
    trusted: bool = False
    install_folder: Optional[str] = None
    source: Optional[str] = None

    def is_pre(self) -> bool:
        return self.version.prerelease is not None or self.experimental

    def check_qgis_version(self, version: Union[str, Version]) -> bool:
        if self.qgis_minimum_version is not None and self.qgis_minimum_version > version:
            return False
        elif self.qgis_maximum_version is not None and self.qgis_maximum_version < version:
            return False
        else:
            return True

    @staticmethod
    def from_xml_element(elem: Element, source: Optional[str] = None) -> "Plugin":
        data: Dict = {"source": source}
        for element in elem:
            if element.tag in Plugin._fields:
                data[element.tag] = element.text

        experimental = data.get("experimental")
        if experimental:
            data["experimental"] = experimental.lower() in TRUE_VALUES

        deprecated = data.get("deprecated")
        if deprecated:
            data["deprecated"] = deprecated.lower() in TRUE_VALUES

        trusted = data.get("trusted")
        if trusted:
            data["trusted"] = trusted.lower() in TRUE_VALUES

        data["name"] = elem.attrib["name"]

        version_str = elem.attrib["version"]
        data["version_str"] = version_str
        data["version"] = get_semver_version(version_str)

        def maybe_version(ver: Optional[str]) -> Optional[Version]:
            return get_semver_version(ver) if ver else None

        data["qgis_minimum_version"] = maybe_version(data.get("qgis_minimum_version"))
        data["qgis_maximum_version"] = maybe_version(data.get("qgis_maximum_version"))

        # Add more search fields
        tags = []
        data_tags = data.get("tags")
        if data_tags:
            tags = data_tags.split(",")

        name = data["name"]
        search_text = (
            name.lower(),
            name.lower().replace(" ", ""),
            *tags,
            *name.lower().split(" "),
        )

        # Remove duplicates
        data["search"] = list(dict.fromkeys(search_text))

        return Plugin(**data)
