"""
Configuration factory for connection types
"""

from typing import Dict, List, Optional, Union

from .dummy import DummyConfig
from .serial import SerialConfig
from .telnet import TelnetConfig
from .uri_parser import ParsedUri


class ParameterExtractor:
    """Helper class for extracting and converting URI parameters"""

    def __init__(self, params: Optional[Dict[str, List[str]]]):
        self.params = params or {}

    def get_int(self, name: str, default: int) -> int:
        """Get integer parameter"""
        if name in self.params and self.params[name]:
            try:
                return int(self.params[name][0])
            except (ValueError, IndexError):
                return default
        return default

    def get_str(self, name: str, default: str) -> str:
        """Get string parameter"""
        if name in self.params and self.params[name]:
            return self.params[name][0]
        return default

    def get_bool(self, name: str, default: bool = False) -> bool:
        """Get boolean parameter"""
        if name in self.params and self.params[name]:
            value = self.params[name][0].lower()
            return value in ("true", "1", "yes", "on")
        return default

    def get_timeout(self) -> Optional[int]:
        """Get timeout parameter with special handling"""
        if "timeout" in self.params and self.params["timeout"]:
            try:
                return int(self.params["timeout"][0])
            except (ValueError, IndexError):
                pass
        return None


class ConfigFactory:
    """Factory for creating connection configurations from parsed URIs"""

    @staticmethod
    def create_telnet_config(parsed_uri: ParsedUri) -> TelnetConfig:
        """Create TelnetConfig from parsed URI

        Args:
            parsed_uri: Parsed URI components

        Returns:
            TelnetConfig object

        Raises:
            ValueError: If required parameters are missing
        """
        if not parsed_uri.host:
            raise ValueError("Host is required for telnet connection")

        # Validate port first, then use default if None
        if parsed_uri.port is not None and parsed_uri.port <= 0:
            raise ValueError("Port must be a positive integer")
        port = parsed_uri.port if parsed_uri.port is not None else 23
        return TelnetConfig(host=parsed_uri.host, port=port)

    @staticmethod
    def create_serial_config(parsed_uri: ParsedUri) -> SerialConfig:
        """Create SerialConfig from parsed URI

        Args:
            parsed_uri: Parsed URI components

        Returns:
            SerialConfig object

        Raises:
            ValueError: If required parameters are missing
        """
        # For serial connections, path or host can be used
        port = parsed_uri.path or parsed_uri.host
        if not port:
            raise ValueError("Path or host is required for serial connection")

        # Extract parameters using helper
        extractor = ParameterExtractor(parsed_uri.query_params)

        return SerialConfig(
            port=port,
            baudrate=extractor.get_int("baudrate", 115200),
            bytesize=extractor.get_int("bytesize", 8),
            parity=extractor.get_str("parity", "N"),
            stopbits=extractor.get_int("stopbits", 1),
            timeout=extractor.get_timeout(),
            xonxoff=extractor.get_bool("xonxoff"),
            rtscts=extractor.get_bool("rtscts"),
            dsrdtr=extractor.get_bool("dsrdtr"),
        )

    @staticmethod
    def create_dummy_config(parsed_uri: ParsedUri) -> DummyConfig:
        """Create DummyConfig from parsed URI

        Args:
            parsed_uri: Parsed URI components

        Returns:
            DummyConfig object
        """
        return DummyConfig()

    @classmethod
    def create_config(
        cls, parsed_uri: ParsedUri
    ) -> Union[TelnetConfig, SerialConfig, DummyConfig]:
        """Create appropriate config based on scheme

        Args:
            parsed_uri: Parsed URI components

        Returns:
            Connection configuration object

        Raises:
            ValueError: If scheme is not supported
        """
        scheme = parsed_uri.scheme.lower()

        config_creators = {
            "telnet": cls.create_telnet_config,
            "serial": cls.create_serial_config,
            "dummy": cls.create_dummy_config,
        }

        if scheme not in config_creators:
            raise ValueError(f"Unsupported scheme: {scheme}")

        return config_creators[scheme](parsed_uri)  # type: ignore


class ConnectionConfigValidator:
    """Validate connection configurations"""

    @staticmethod
    def validate_telnet_config(config: TelnetConfig) -> None:
        """Validate telnet configuration

        Args:
            config: TelnetConfig to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if not config.host:
            raise ValueError("Host cannot be empty")
        if not isinstance(config.port, int) or config.port <= 0:
            raise ValueError("Port must be a positive integer")

    @staticmethod
    def validate_serial_config(config: SerialConfig) -> None:
        """Validate serial configuration

        Args:
            config: SerialConfig to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if not config.port:
            raise ValueError("Port cannot be empty")

        valid_bytesize = [5, 6, 7, 8]
        if config.bytesize not in valid_bytesize:
            raise ValueError(f"Bytesize must be one of {valid_bytesize}")

        valid_parity = ["N", "O", "E", "M", "S"]
        if config.parity not in valid_parity:
            raise ValueError(f"Parity must be one of {valid_parity}")

        valid_stopbits = [1, 1.5, 2]
        if config.stopbits not in valid_stopbits:
            raise ValueError(f"Stopbits must be one of {valid_stopbits}")

        if config.baudrate <= 0:
            raise ValueError("Baudrate must be positive")

    @classmethod
    def validate_config(
        cls, config: Union[TelnetConfig, SerialConfig, DummyConfig]
    ) -> None:
        """Validate any connection configuration

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if isinstance(config, TelnetConfig):
            cls.validate_telnet_config(config)
        elif isinstance(config, SerialConfig):
            cls.validate_serial_config(config)
        # DummyConfig needs no validation


def create_connection_config(
    dummy: bool = False,
    device: Optional[str] = None,
    baudrate: int = 19200,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> Union[TelnetConfig, SerialConfig, DummyConfig]:
    """Create connection configuration from individual parameters

    Args:
        dummy: Use dummy connection for testing
        device: Serial device path
        baudrate: Serial baud rate
        host: Telnet host
        port: Telnet port

    Returns:
        Connection configuration object

    Raises:
        ValueError: If required parameters are missing
    """
    if dummy:
        return DummyConfig()

    if host is not None:
        # Telnet connection
        telnet_port = port if port is not None else 23
        return TelnetConfig(host=host, port=telnet_port)

    if device is not None:
        # Serial connection
        return SerialConfig(port=device, baudrate=baudrate)

    raise ValueError("Either dummy=True, device path, or host must be provided")
