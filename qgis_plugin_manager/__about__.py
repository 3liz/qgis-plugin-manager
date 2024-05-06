"""
Metadata about the package to easily retrieve information about it.
See: https://packaging.python.org/guides/single-sourcing-package-version/
"""

from datetime import date

__all__ = [
    "__author__",
    "__copyright__",
    "__email__",
    "__license__",
    "__summary__",
    "__title__",
    "__title_clean__",
    "__uri__",
    "__version__",
    "__version_info__",
]

__author__ = "Étienne Trimaille"
__copyright__ = f"2021 - {date.today().year}, {__author__}"
__email__ = "etrimaille@3liz.com"
__license__ = "GNU General Public License v3.0"
__summary__ = "Tool for downloading/managing QGIS plugins from CLI."
__title__ = "QGIS Plugin Manager"
__title_clean__ = "".join(e for e in __title__ if e.isalnum())
__uri__ = "https://github.com/3liz/qgis-plugin-manager"

# This string might be updated on CI on runtime with a proper semantic version name with X.Y.Z
__version__ = "__VERSION__"

if "." not in __version__:
    # If __version__ is still not a proper semantic versioning with X.Y.Z
    # let's hardcode 0.0.0
    __version__ = "0.0.0"

__version_info__ = tuple(
    [
        int(num) if num.isdigit() else num
        for num in __version__.replace("-", ".", 1).split(".")
    ],
)
