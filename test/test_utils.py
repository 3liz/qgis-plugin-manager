import unittest

from qgis_plugin_manager.utils import parse_ldd, parse_version


class TestUtils(unittest.TestCase):

    def test_qgis_server_version(self):
        """ Trying the LDD command to know QGIS Server version. """
        output = (
            "	libqgis_server.so.3.10.4 => /lib/libqgis_server.so.3.10.4 (0x00007f6c76269000)\n"
            "	libqgis_core.so.3.10.4 => /lib/libqgis_core.so.3.10.4 (0x00007f6c74fd4000)"
        )
        self.assertEqual('3.10.4', parse_ldd(output))

        output = (
            "	libqgis_server.so.3.4.4 => /lib/libqgis_server.so.3.4.4 (0x00007f6c76269000)\n"
            "	libqgis_core.so.3.4.4 => /lib/libqgis_core.so.3.4.4 (0x00007f6c74fd4000)"
        )
        self.assertEqual('3.4.4', parse_ldd(output))

        output = (
            "libqgis_server.so.3.16.6 => /home/etienne/dev/app/qgis-stable/lib/libqgis_server.so.3.16.6 (0x00007f6b2dd30000)\n"
            "libqgis_core.so.3.16.6 => /home/etienne/dev/app/qgis-stable/lib/libqgis_core.so.3.16.6 (0x00007f6b2b879000)"
        )
        self.assertEqual('3.16.6', parse_ldd(output))

    def test_version(self):
        self.assertListEqual([3, 10, 0], parse_version("3.10"))
        self.assertListEqual([3, 10, 0], parse_version("3.10.0"))
        self.assertIsNone(parse_version(""))
