"""
Configuration factory for connection types
"""

from typing import Union
from .uri_parser import ParsedUri
from .serial import SerialConfig
from .telnet import TelnetConfig
from .dummy import DummyConfig


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

        # Extract parameters from query if available
        params = parsed_uri.query_params or {}

        def get_int_param(name: str, default: int) -> int:
            """Get integer parameter from query"""
            if name in params and params[name]:
                try:
                    return int(params[name][0])
                except (ValueError, IndexError):
                    return default
            return default

        def get_str_param(name: str, default: str) -> str:
            """Get string parameter from query"""
            if name in params and params[name]:
                return params[name][0]
            return default

        def get_bool_param(name: str, default: bool = False) -> bool:
            """Get boolean parameter from query"""
            if name in params and params[name]:
                value = params[name][0].lower()
                return value in ("true", "1", "yes", "on")
            return default

        def get_timeout_param() -> int:
            """Get timeout parameter with special handling"""
            if "timeout" in params and params["timeout"]:
                try:
                    return int(params["timeout"][0])
                except (ValueError, IndexError):
                    pass
            return None

        return SerialConfig(
            port=port,
            baudrate=get_int_param("baudrate", 115200),
            bytesize=get_int_param("bytesize", 8),
            parity=get_str_param("parity", "N"),
            stopbits=get_int_param("stopbits", 1),
            timeout=get_timeout_param(),
            xonxoff=get_bool_param("xonxoff"),
            rtscts=get_bool_param("rtscts"),
            dsrdtr=get_bool_param("dsrdtr"),
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

        if scheme == "telnet":
            return cls.create_telnet_config(parsed_uri)
        elif scheme == "serial":
            return cls.create_serial_config(parsed_uri)
        elif scheme == "dummy":
            return cls.create_dummy_config(parsed_uri)
        else:
            raise ValueError(f"Unsupported scheme: {scheme}")


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
