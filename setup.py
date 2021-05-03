import os
import sys

from setuptools import setup

python_min_version = (3, 7)

if os.getenv('CI') == 'true':
    VERSION = "__VERSION__"
else:
    VERSION = "0.0.0"

if sys.version_info < python_min_version:
    sys.exit(
        "qgis-plugin-manager requires at least Python version {vmaj}.{vmin}.\n"
        "You are currently running this installation with\n\n{curver}".format(
            vmaj=python_min_version[0], vmin=python_min_version[1], curver=sys.version
        )
    )

setup(
    name="qgis-plugin-manager",
    packages=["qgis_plugin_manager"],
    entry_points={"console_scripts": ["qgis-plugin-manager = qgis_plugin_manager.cli:main"]},
    version=VERSION,
    description="Manage QGIS plugin when you are on a server.",
    author="Etienne Trimaille",
    author_email="etrimaille@3liz.com",
    # url="https://github.com/opengisch/qgis-plugin-ci",
    # download_url="https://github.com/opengisch/qgis-plugin-ci/archive/{}.tar.gz".format(VERSION),
    keywords=["QGIS"],
    classifiers=[
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
    ],
    install_requires=[],
    python_requires=">={vmaj}.{vmin}".format(
        vmaj=python_min_version[0], vmin=python_min_version[1]
    ),
)
