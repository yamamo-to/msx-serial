"""
Tests for URI parsing utilities
"""

import pytest

from msx_serial.connection.uri_parser import (LegacyFormatParser, ParsedUri,
                                              StandardUriParser, UriParser)


class TestParsedUri:
    """Test ParsedUri data class"""

    def test_default_values(self):
        """Test ParsedUri with default values"""
        uri = ParsedUri(scheme="test")
        assert uri.scheme == "test"
        assert uri.host is None
        assert uri.port is None
        assert uri.path is None
        assert uri.query_params is None

    def test_all_values(self):
        """Test ParsedUri with all values set"""
        params = {"key": ["value"]}
        uri = ParsedUri(
            scheme="http",
            host="example.com",
            port=8080,
            path="/test",
            query_params=params,
        )
        assert uri.scheme == "http"
        assert uri.host == "example.com"
        assert uri.port == 8080
        assert uri.path == "/test"
        assert uri.query_params == params


class TestLegacyFormatParser:
    """Test legacy format parser"""

    def test_is_legacy_format_true(self):
        """Test legacy format detection - positive cases"""
        assert LegacyFormatParser.is_legacy_format("localhost:8080")
        assert LegacyFormatParser.is_legacy_format("COM1")
        assert LegacyFormatParser.is_legacy_format("/dev/ttyUSB0")
        assert LegacyFormatParser.is_legacy_format("192.168.1.1:23")

    def test_is_legacy_format_false(self):
        """Test legacy format detection - negative cases"""
        assert not LegacyFormatParser.is_legacy_format("telnet://host:23")
        assert not LegacyFormatParser.is_legacy_format("serial:///dev/ttyUSB0")
        assert not LegacyFormatParser.is_legacy_format("http://example.com")

    def test_parse_host_port_valid(self):
        """Test valid host:port parsing"""
        result = LegacyFormatParser.parse_host_port("localhost:8080")
        assert result is not None
        assert result.scheme == "telnet"
        assert result.host == "localhost"
        assert result.port == 8080

    def test_parse_host_port_ipv4(self):
        """Test IPv4 host:port parsing"""
        result = LegacyFormatParser.parse_host_port("192.168.1.100:23")
        assert result is not None
        assert result.scheme == "telnet"
        assert result.host == "192.168.1.100"
        assert result.port == 23

    def test_parse_host_port_no_colon(self):
        """Test host without port"""
        result = LegacyFormatParser.parse_host_port("localhost")
        assert result is None

    def test_parse_host_port_invalid_port(self):
        """Test invalid port number"""
        result = LegacyFormatParser.parse_host_port("localhost:invalid")
        assert result is None

    def test_parse_serial_port_com(self):
        """Test COM port parsing"""
        result = LegacyFormatParser.parse_serial_port("COM1")
        assert result is not None
        assert result.scheme == "serial"
        assert result.path == "COM1"

        result = LegacyFormatParser.parse_serial_port("COM10")
        assert result is not None
        assert result.scheme == "serial"
        assert result.path == "COM10"

    def test_parse_serial_port_tty(self):
        """Test /dev/tty device parsing"""
        result = LegacyFormatParser.parse_serial_port("/dev/ttyUSB0")
        assert result is not None
        assert result.scheme == "serial"
        assert result.path == "/dev/ttyUSB0"

        result = LegacyFormatParser.parse_serial_port("/dev/ttyACM0")
        assert result is not None
        assert result.scheme == "serial"
        assert result.path == "/dev/ttyACM0"

    def test_parse_serial_port_invalid(self):
        """Test invalid serial port format"""
        assert LegacyFormatParser.parse_serial_port("localhost") is None
        assert LegacyFormatParser.parse_serial_port("COM") is None
        assert LegacyFormatParser.parse_serial_port("/dev/") is None

    def test_parse_priority(self):
        """Test parsing priority (host:port over serial)"""
        # Should be detected as telnet, not serial
        result = LegacyFormatParser.parse("192.168.1.1:23")
        assert result.scheme == "telnet"
        assert result.host == "192.168.1.1"
        assert result.port == 23

    def test_parse_serial_default(self):
        """Test default serial parsing"""
        result = LegacyFormatParser.parse("/some/unknown/device")
        assert result.scheme == "serial"
        assert result.path == "/some/unknown/device"

    def test_parse_com_port(self):
        """Test COM port parsing"""
        result = LegacyFormatParser.parse("COM1")
        assert result.scheme == "serial"
        assert result.path == "COM1"


class TestStandardUriParser:
    """Test standard URI parser"""

    def test_parse_telnet_with_port(self):
        """Test telnet URI with port"""
        result = StandardUriParser.parse("telnet://localhost:8080")
        assert result.scheme == "telnet"
        assert result.host == "localhost"
        assert result.port == 8080

    def test_parse_telnet_without_port(self):
        """Test telnet URI without port"""
        result = StandardUriParser.parse("telnet://localhost")
        assert result.scheme == "telnet"
        assert result.host == "localhost"
        assert result.port is None

    def test_parse_serial_with_query(self):
        """Test serial URI with query parameters"""
        uri = "serial:///dev/ttyUSB0?baudrate=9600&parity=E&timeout=5"
        result = StandardUriParser.parse(uri)
        assert result.scheme == "serial"
        assert result.path == "/dev/ttyUSB0"
        assert result.query_params["baudrate"] == ["9600"]
        assert result.query_params["parity"] == ["E"]
        assert result.query_params["timeout"] == ["5"]

    def test_parse_dummy(self):
        """Test dummy URI"""
        result = StandardUriParser.parse("dummy://")
        assert result.scheme == "dummy"

    def test_parse_missing_scheme(self):
        """Test URI without scheme"""
        with pytest.raises(ValueError, match="Missing scheme"):
            StandardUriParser.parse("://localhost")

    def test_parse_invalid_port(self):
        """Test URI with invalid port"""
        with pytest.raises(ValueError, match="Invalid URI format"):
            StandardUriParser.parse("telnet://localhost:invalid")

    def test_parse_with_path_and_query(self):
        """Test URI with both path and query"""
        uri = "serial:///dev/ttyUSB0?baudrate=115200"
        result = StandardUriParser.parse(uri)
        assert result.scheme == "serial"
        assert result.path == "/dev/ttyUSB0"
        assert result.query_params["baudrate"] == ["115200"]


class TestUriParser:
    """Test main URI parser"""

    def test_parse_legacy_host_port(self):
        """Test legacy host:port format"""
        result = UriParser.parse("localhost:8080")
        assert result.scheme == "telnet"
        assert result.host == "localhost"
        assert result.port == 8080

    def test_parse_legacy_serial(self):
        """Test legacy serial format"""
        result = UriParser.parse("COM1")
        assert result.scheme == "serial"
        assert result.path == "COM1"

    def test_parse_standard_telnet(self):
        """Test standard telnet URI"""
        result = UriParser.parse("telnet://localhost:23")
        assert result.scheme == "telnet"
        assert result.host == "localhost"
        assert result.port == 23

    def test_parse_standard_serial(self):
        """Test standard serial URI"""
        result = UriParser.parse("serial:///dev/ttyUSB0?baudrate=9600")
        assert result.scheme == "serial"
        assert result.path == "/dev/ttyUSB0"
        assert result.query_params["baudrate"] == ["9600"]

    def test_parse_empty_uri(self):
        """Test empty URI"""
        with pytest.raises(ValueError, match="URI must be a non-empty string"):
            UriParser.parse("")

    def test_parse_none_uri(self):
        """Test None URI"""
        with pytest.raises(ValueError, match="URI must be a non-empty string"):
            UriParser.parse(None)

    def test_parse_non_string_uri(self):
        """Test non-string URI"""
        with pytest.raises(ValueError, match="URI must be a non-empty string"):
            UriParser.parse(123)
