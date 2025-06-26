"""
Connection configuration detection and creation
"""

from typing import Union

from .config_factory import ConfigFactory, ConnectionConfigValidator
from .dummy import DummyConfig
from .serial import SerialConfig
from .telnet import TelnetConfig
from .uri_parser import UriParser


class ConnectionDetector:
    """Detect and create connection configurations from URI strings"""

    def __init__(self) -> None:
        """Initialize connection detector"""
        self.parser = UriParser()
        self.factory = ConfigFactory()
        self.validator = ConnectionConfigValidator()

    def detect_connection_type(
        self, uri: str
    ) -> Union[TelnetConfig, SerialConfig, DummyConfig]:
        """Detect connection type from URI

        Args:
            uri: URI string in various formats

        Returns:
            Connection configuration object

        Raises:
            ValueError: If URI format is invalid or unsupported
        """
        # Parse the URI
        parsed_uri = self.parser.parse(uri)

        # Create configuration
        config = self.factory.create_config(parsed_uri)

        # Validate configuration
        self.validator.validate_config(config)

        return config


# Backward compatibility: maintain the original function interface
def detect_connection_type(uri: str) -> Union[TelnetConfig, SerialConfig, DummyConfig]:
    """URI形式の接続先から接続タイプを判定する

    Args:
        uri: URI string

    Returns:
        Connection configuration object

    Raises:
        ValueError: If URI format is invalid
    """
    detector = ConnectionDetector()
    return detector.detect_connection_type(uri)
