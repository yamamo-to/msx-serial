"""
Tests for configuration factory and validation
"""

import pytest

from msx_serial.connection.config_factory import (ConfigFactory,
                                                  ConnectionConfigValidator)
from msx_serial.connection.dummy import DummyConfig
from msx_serial.connection.serial import SerialConfig
from msx_serial.connection.telnet import TelnetConfig
from msx_serial.connection.uri_parser import ParsedUri


class TestConfigFactory:
    """Test configuration factory"""

    def setup_method(self):
        """Setup test"""
        self.factory = ConfigFactory()

    def test_create_telnet_config_basic(self):
        """Test basic telnet config creation"""
        parsed_uri = ParsedUri(scheme="telnet", host="localhost", port=8080)
        config = self.factory.create_telnet_config(parsed_uri)

        assert isinstance(config, TelnetConfig)
        assert config.host == "localhost"
        assert config.port == 8080

    def test_create_telnet_config_default_port(self):
        """Test telnet config with default port"""
        parsed_uri = ParsedUri(scheme="telnet", host="example.com")
        config = self.factory.create_telnet_config(parsed_uri)

        assert isinstance(config, TelnetConfig)
        assert config.host == "example.com"
        assert config.port == 23

    def test_create_telnet_config_missing_host(self):
        """Test telnet config without host"""
        parsed_uri = ParsedUri(scheme="telnet", port=8080)
        with pytest.raises(ValueError, match="Host is required"):
            self.factory.create_telnet_config(parsed_uri)

    def test_create_serial_config_basic(self):
        """Test basic serial config creation"""
        parsed_uri = ParsedUri(scheme="serial", path="/dev/ttyUSB0")
        config = self.factory.create_serial_config(parsed_uri)

        assert isinstance(config, SerialConfig)
        assert config.port == "/dev/ttyUSB0"
        assert config.baudrate == 115200  # default
        assert config.bytesize == 8  # default
        assert config.parity == "N"  # default
        assert config.stopbits == 1  # default
        assert config.timeout is None  # default
        assert config.xonxoff is False  # default
        assert config.rtscts is False  # default
        assert config.dsrdtr is False  # default

    def test_create_serial_config_with_params(self):
        """Test serial config with query parameters"""
        params = {
            "baudrate": ["9600"],
            "bytesize": ["7"],
            "parity": ["E"],
            "stopbits": ["2"],
            "timeout": ["5"],
            "xonxoff": ["true"],
            "rtscts": ["1"],
            "dsrdtr": ["yes"],
        }
        parsed_uri = ParsedUri(scheme="serial", path="COM1", query_params=params)
        config = self.factory.create_serial_config(parsed_uri)

        assert config.port == "COM1"
        assert config.baudrate == 9600
        assert config.bytesize == 7
        assert config.parity == "E"
        assert config.stopbits == 2
        assert config.timeout == 5
        assert config.xonxoff is True
        assert config.rtscts is True
        assert config.dsrdtr is True

    def test_create_serial_config_invalid_params(self):
        """Test serial config with invalid parameters"""
        params = {
            "baudrate": ["invalid"],
            "bytesize": ["invalid"],
            "stopbits": ["invalid"],
            "timeout": ["invalid"],
        }
        parsed_uri = ParsedUri(scheme="serial", path="COM1", query_params=params)
        config = self.factory.create_serial_config(parsed_uri)

        # Should use defaults for invalid values
        assert config.baudrate == 115200
        assert config.bytesize == 8
        assert config.stopbits == 1
        assert config.timeout is None

    def test_create_serial_config_boolean_variations(self):
        """Test various boolean parameter formats"""
        test_cases = [
            (["true"], True),
            (["True"], True),
            (["1"], True),
            (["yes"], True),
            (["on"], True),
            (["false"], False),
            (["False"], False),
            (["0"], False),
            (["no"], False),
            (["off"], False),
            (["invalid"], False),
        ]

        for value, expected in test_cases:
            params = {"xonxoff": value}
            parsed_uri = ParsedUri(scheme="serial", path="COM1", query_params=params)
            config = self.factory.create_serial_config(parsed_uri)
            assert config.xonxoff is expected

    def test_create_serial_config_missing_path(self):
        """Test serial config without path"""
        parsed_uri = ParsedUri(scheme="serial")
        with pytest.raises(ValueError, match="Path or host is required"):
            self.factory.create_serial_config(parsed_uri)

    def test_create_dummy_config(self):
        """Test dummy config creation"""
        parsed_uri = ParsedUri(scheme="dummy")
        config = self.factory.create_dummy_config(parsed_uri)

        assert isinstance(config, DummyConfig)

    def test_create_config_telnet(self):
        """Test create_config for telnet"""
        parsed_uri = ParsedUri(scheme="telnet", host="localhost", port=23)
        config = self.factory.create_config(parsed_uri)

        assert isinstance(config, TelnetConfig)
        assert config.host == "localhost"
        assert config.port == 23

    def test_create_config_serial(self):
        """Test create_config for serial"""
        parsed_uri = ParsedUri(scheme="serial", path="COM1")
        config = self.factory.create_config(parsed_uri)

        assert isinstance(config, SerialConfig)
        assert config.port == "COM1"

    def test_create_config_dummy(self):
        """Test create_config for dummy"""
        parsed_uri = ParsedUri(scheme="dummy")
        config = self.factory.create_config(parsed_uri)

        assert isinstance(config, DummyConfig)

    def test_create_config_unsupported_scheme(self):
        """Test create_config with unsupported scheme"""
        parsed_uri = ParsedUri(scheme="unsupported")
        with pytest.raises(ValueError, match="Unsupported scheme: unsupported"):
            self.factory.create_config(parsed_uri)

    def test_create_config_case_insensitive(self):
        """Test create_config is case insensitive"""
        parsed_uri = ParsedUri(scheme="TELNET", host="localhost")
        config = self.factory.create_config(parsed_uri)

        assert isinstance(config, TelnetConfig)


class TestConnectionConfigValidator:
    """Test connection configuration validator"""

    def setup_method(self):
        """Setup test"""
        self.validator = ConnectionConfigValidator()

    def test_validate_telnet_config_valid(self):
        """Test valid telnet config validation"""
        config = TelnetConfig(host="localhost", port=23)
        # Should not raise exception
        self.validator.validate_telnet_config(config)

    def test_validate_telnet_config_empty_host(self):
        """Test telnet config with empty host"""
        config = TelnetConfig(host="", port=23)
        with pytest.raises(ValueError, match="Host cannot be empty"):
            self.validator.validate_telnet_config(config)

    def test_validate_telnet_config_none_host(self):
        """Test telnet config with None host"""
        config = TelnetConfig(host=None, port=23)
        with pytest.raises(ValueError, match="Host cannot be empty"):
            self.validator.validate_telnet_config(config)

    def test_validate_telnet_config_invalid_port(self):
        """Test telnet config with invalid port"""
        test_cases = [0, -1, "invalid", None]
        for port in test_cases:
            config = TelnetConfig(host="localhost", port=port)
            with pytest.raises(ValueError, match="Port must be a positive integer"):
                self.validator.validate_telnet_config(config)

    def test_validate_serial_config_valid(self):
        """Test valid serial config validation"""
        config = SerialConfig(
            port="COM1",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
        )
        # Should not raise exception
        self.validator.validate_serial_config(config)

    def test_validate_serial_config_empty_port(self):
        """Test serial config with empty port"""
        config = SerialConfig(port="")
        with pytest.raises(ValueError, match="Port cannot be empty"):
            self.validator.validate_serial_config(config)

    def test_validate_serial_config_none_port(self):
        """Test serial config with None port"""
        config = SerialConfig(port=None)
        with pytest.raises(ValueError, match="Port cannot be empty"):
            self.validator.validate_serial_config(config)

    def test_validate_serial_config_invalid_bytesize(self):
        """Test serial config with invalid bytesize"""
        for bytesize in [4, 9, 10]:
            config = SerialConfig(port="COM1", bytesize=bytesize)
            with pytest.raises(ValueError, match="Bytesize must be one of"):
                self.validator.validate_serial_config(config)

    def test_validate_serial_config_invalid_parity(self):
        """Test serial config with invalid parity"""
        for parity in ["X", "Y", "Z"]:
            config = SerialConfig(port="COM1", parity=parity)
            with pytest.raises(ValueError, match="Parity must be one of"):
                self.validator.validate_serial_config(config)

    def test_validate_serial_config_invalid_stopbits(self):
        """Test serial config with invalid stopbits"""
        for stopbits in [0, 3, 0.5]:
            config = SerialConfig(port="COM1", stopbits=stopbits)
            with pytest.raises(ValueError, match="Stopbits must be one of"):
                self.validator.validate_serial_config(config)

    def test_validate_serial_config_invalid_baudrate(self):
        """Test serial config with invalid baudrate"""
        for baudrate in [0, -1]:
            config = SerialConfig(port="COM1", baudrate=baudrate)
            with pytest.raises(ValueError, match="Baudrate must be positive"):
                self.validator.validate_serial_config(config)

    def test_validate_config_telnet(self):
        """Test validate_config for telnet"""
        config = TelnetConfig(host="localhost", port=23)
        # Should not raise exception
        self.validator.validate_config(config)

    def test_validate_config_serial(self):
        """Test validate_config for serial"""
        config = SerialConfig(port="COM1")
        # Should not raise exception
        self.validator.validate_config(config)

    def test_validate_config_dummy(self):
        """Test validate_config for dummy"""
        config = DummyConfig()
        # Should not raise exception
        self.validator.validate_config(config)

    def test_validate_config_invalid_telnet(self):
        """Test validate_config with invalid telnet config"""
        config = TelnetConfig(host="", port=23)
        with pytest.raises(ValueError, match="Host cannot be empty"):
            self.validator.validate_config(config)

    def test_validate_config_invalid_serial(self):
        """Test validate_config with invalid serial config"""
        config = SerialConfig(port="", baudrate=-1)
        with pytest.raises(ValueError, match="Port cannot be empty"):
            self.validator.validate_config(config)
