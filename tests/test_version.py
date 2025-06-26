"""
Version testing module
"""

import re
import unittest
from pathlib import Path


class TestVersion(unittest.TestCase):
    """Version testing class"""

    def test_version_format(self) -> None:
        """Test version string format"""
        import msx_serial

        version = msx_serial.__version__
        self.assertIsInstance(version, str)
        # Support both X.Y.Z and X.Y formats, with optional .devN suffix
        pattern = r"^\d+\.\d+(?:\.\d+)?(?:\.dev\d+)?$"
        self.assertRegex(version, pattern)

    def test_version_file_exists(self) -> None:
        """Test version file exists"""
        version_file = Path("msx_serial") / "_version.py"
        self.assertTrue(version_file.exists())

    def test_version_file_content(self) -> None:
        """Test version file content is valid"""
        version_file = Path("msx_serial") / "_version.py"
        content = version_file.read_text()
        self.assertIn("__version__", content)

    def test_package_version_matches_file(self) -> None:
        """Test package version matches version file"""
        import msx_serial

        version_file = Path("msx_serial") / "_version.py"
        content = version_file.read_text()

        # Extract version from file - setuptools_scmを使用している場合の対応
        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            file_version = version_match.group(1)
            package_version = msx_serial.__version__
            self.assertEqual(file_version, package_version)
        else:
            # setuptools_scmの場合、バージョンは動的に生成される
            self.assertIsNotNone(msx_serial.__version__)
            self.assertNotEqual(msx_serial.__version__, "0.0.0")

    def test_setup_tools_scm_version(self) -> None:
        """Test setuptools_scm version detection"""
        import msx_serial

        version = msx_serial.__version__
        # Version should be non-empty and contain at least one dot
        self.assertGreater(len(version), 0)
        self.assertIn(".", version)

    def test_version_not_placeholder(self) -> None:
        """Test version is not a placeholder value"""
        import msx_serial

        version = msx_serial.__version__
        # Check it's not a common placeholder
        placeholders = ["0.0.0", "unknown", "dev", ""]
        self.assertNotIn(version, placeholders)

    def test_development_version_pattern(self) -> None:
        """Test development version follows expected pattern"""
        import msx_serial

        version = msx_serial.__version__
        # If it's a dev version, it should end with .devN
        if ".dev" in version:
            # Support both X.Y.dev N and X.Y.Z.devN patterns
            pattern = r"^\d+\.\d+(?:\.\d+)?\.dev\d+$"
            self.assertRegex(version, pattern)


if __name__ == "__main__":
    unittest.main()
