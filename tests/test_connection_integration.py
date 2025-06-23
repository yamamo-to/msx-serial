"""
Integration tests for connection configuration
"""

import pytest
from msx_serial.connection.connection import (
    ConnectionDetector,
    detect_connection_type,
)
from msx_serial.connection.serial import SerialConfig
from msx_serial.connection.telnet import TelnetConfig
from msx_serial.connection.dummy import DummyConfig


class TestConnectionDetector:
    """Test connection detector"""

    def setup_method(self):
        """Setup test"""
        self.detector = ConnectionDetector()

    def test_detect_legacy_host_port(self):
        """Test legacy host:port detection"""
        config = self.detector.detect_connection_type("localhost:8080")
        assert isinstance(config, TelnetConfig)
        assert config.host == "localhost"
        assert config.port == 8080

    def test_detect_legacy_ipv4(self):
        """Test legacy IPv4:port detection"""
        config = self.detector.detect_connection_type("192.168.1.100:23")
        assert isinstance(config, TelnetConfig)
        assert config.host == "192.168.1.100"
        assert config.port == 23

    def test_detect_legacy_com_port(self):
        """Test legacy COM port detection"""
        config = self.detector.detect_connection_type("COM1")
        assert isinstance(config, SerialConfig)
        assert config.port == "COM1"
        assert config.baudrate == 115200

    def test_detect_legacy_tty_device(self):
        """Test legacy TTY device detection"""
        config = self.detector.detect_connection_type("/dev/ttyUSB0")
        assert isinstance(config, SerialConfig)
        assert config.port == "/dev/ttyUSB0"
        assert config.baudrate == 115200

    def test_detect_legacy_unknown_device(self):
        """Test legacy unknown device detection"""
        config = self.detector.detect_connection_type("/some/unknown/device")
        assert isinstance(config, SerialConfig)
        assert config.port == "/some/unknown/device"

    def test_detect_standard_telnet_uri(self):
        """Test standard telnet URI detection"""
        config = self.detector.detect_connection_type("telnet://localhost:8080")
        assert isinstance(config, TelnetConfig)
        assert config.host == "localhost"
        assert config.port == 8080

    def test_detect_standard_telnet_default_port(self):
        """Test standard telnet URI with default port"""
        config = self.detector.detect_connection_type("telnet://example.com")
        assert isinstance(config, TelnetConfig)
        assert config.host == "example.com"
        assert config.port == 23

    def test_detect_standard_serial_uri(self):
        """Test standard serial URI detection"""
        uri = "serial:///dev/ttyUSB0?baudrate=9600&parity=E&timeout=5"
        config = self.detector.detect_connection_type(uri)
        assert isinstance(config, SerialConfig)
        assert config.port == "/dev/ttyUSB0"
        assert config.baudrate == 9600
        assert config.parity == "E"
        assert config.timeout == 5

    def test_detect_standard_serial_com_uri(self):
        """Test standard serial COM URI detection"""
        uri = "serial:///COM1?baudrate=115200&bytesize=8"
        config = self.detector.detect_connection_type(uri)
        assert isinstance(config, SerialConfig)
        assert config.port == "/COM1"
        assert config.baudrate == 115200
        assert config.bytesize == 8

    def test_detect_dummy_uri(self):
        """Test dummy URI detection"""
        config = self.detector.detect_connection_type("dummy://")
        assert isinstance(config, DummyConfig)

    def test_detect_invalid_uri(self):
        """Test invalid URI detection"""
        with pytest.raises(ValueError, match="URI must be a non-empty string"):
            self.detector.detect_connection_type("")

    def test_detect_unsupported_scheme(self):
        """Test unsupported scheme detection"""
        with pytest.raises(ValueError, match="Unsupported scheme"):
            self.detector.detect_connection_type("http://example.com")

    def test_detect_invalid_telnet_config(self):
        """Test invalid telnet configuration validation"""
        with pytest.raises(ValueError, match="Port must be a positive integer"):
            self.detector.detect_connection_type("telnet://localhost:0")

    def test_detect_invalid_serial_config(self):
        """Test invalid serial configuration validation"""
        uri = "serial:///dev/ttyUSB0?baudrate=-1"
        with pytest.raises(ValueError, match="Baudrate must be positive"):
            self.detector.detect_connection_type(uri)


class TestDetectConnectionTypeFunction:
    """Test backward compatibility function"""

    def test_function_legacy_host_port(self):
        """Test function with legacy host:port"""
        config = detect_connection_type("localhost:8080")
        assert isinstance(config, TelnetConfig)
        assert config.host == "localhost"
        assert config.port == 8080

    def test_function_legacy_serial(self):
        """Test function with legacy serial"""
        config = detect_connection_type("COM1")
        assert isinstance(config, SerialConfig)
        assert config.port == "COM1"

    def test_function_standard_uri(self):
        """Test function with standard URI"""
        config = detect_connection_type("telnet://localhost:23")
        assert isinstance(config, TelnetConfig)
        assert config.host == "localhost"
        assert config.port == 23

    def test_function_dummy(self):
        """Test function with dummy URI"""
        config = detect_connection_type("dummy://")
        assert isinstance(config, DummyConfig)


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    def setup_method(self):
        """Setup test"""
        self.detector = ConnectionDetector()

    def test_complex_serial_parameters(self):
        """Test complex serial parameter combinations"""
        uri = (
            "serial:///dev/ttyUSB0?"
            "baudrate=57600&"
            "bytesize=7&"
            "parity=O&"
            "stopbits=2&"
            "timeout=10&"
            "xonxoff=true&"
            "rtscts=false&"
            "dsrdtr=on"
        )
        config = self.detector.detect_connection_type(uri)
        assert isinstance(config, SerialConfig)
        assert config.port == "/dev/ttyUSB0"
        assert config.baudrate == 57600
        assert config.bytesize == 7
        assert config.parity == "O"
        assert config.stopbits == 2
        assert config.timeout == 10
        assert config.xonxoff is True
        assert config.rtscts is False
        assert config.dsrdtr is True

    def test_malformed_host_port(self):
        """Test malformed host:port combinations"""
        # Multiple colons should still work (IPv6-like, but treated as legacy)
        config = self.detector.detect_connection_type("::1:8080")
        assert isinstance(config, TelnetConfig)
        assert config.host == "::1"
        assert config.port == 8080

    def test_case_sensitivity(self):
        """Test case sensitivity handling"""
        # Scheme should be case insensitive
        config = self.detector.detect_connection_type("TELNET://localhost:23")
        assert isinstance(config, TelnetConfig)
        assert config.host == "localhost"
        assert config.port == 23

    def test_unicode_handling(self):
        """Test Unicode character handling"""
        # Should handle Unicode characters in paths
        config = self.detector.detect_connection_type("テスト")
        assert isinstance(config, SerialConfig)
        assert config.port == "テスト"

    def test_very_long_uri(self):
        """Test very long URI handling"""
        long_host = "a" * 1000
        config = self.detector.detect_connection_type(f"{long_host}:8080")
        assert isinstance(config, TelnetConfig)
        assert config.host == long_host
        assert config.port == 8080

    def test_empty_query_parameters(self):
        """Test empty query parameters"""
        uri = "serial:///dev/ttyUSB0?baudrate=&parity=&timeout="
        config = self.detector.detect_connection_type(uri)
        assert isinstance(config, SerialConfig)
        # Should use defaults for empty values
        assert config.baudrate == 115200
        assert config.parity == "N"
        assert config.timeout is None
