"""Test package initialization"""

import unittest


class TestInit(unittest.TestCase):
    """Test package initialization functionality"""

    def test_package_import(self) -> None:
        """Test basic package import"""
        import msx_serial

        self.assertIsNotNone(msx_serial)

    def test_package_has_version(self) -> None:
        """Test package has version attribute"""
        import msx_serial

        self.assertTrue(hasattr(msx_serial, "__version__"))

    def test_version_format(self) -> None:
        """Test version format is correct"""
        import msx_serial

        version = msx_serial.__version__
        self.assertIsInstance(version, str)
        self.assertGreater(len(version), 0)

    def test_package_main_module(self) -> None:
        """Test package main module can be imported"""
        import msx_serial.__main__

        self.assertIsNotNone(msx_serial.__main__)

    def test_core_components(self) -> None:
        """Test core components can be imported"""
        from msx_serial.core import data_processor, msx_session

        self.assertIsNotNone(msx_session)
        self.assertIsNotNone(data_processor)

    def test_connection_components(self) -> None:
        """Test connection components can be imported"""
        from msx_serial.connection import config_factory, connection

        self.assertIsNotNone(config_factory)
        self.assertIsNotNone(connection)


if __name__ == "__main__":
    unittest.main()
