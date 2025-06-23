"""
URI parsing utilities for connection configuration
"""

import re
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass


@dataclass
class ParsedUri:
    """Parsed URI components"""

    scheme: str
    host: Optional[str] = None
    port: Optional[int] = None
    path: Optional[str] = None
    query_params: Optional[Dict[str, List[str]]] = None


class LegacyFormatParser:
    """Parse legacy (non-URI) connection formats"""

    @staticmethod
    def is_legacy_format(uri: str) -> bool:
        """Check if URI is in legacy format

        Args:
            uri: URI string to check

        Returns:
            True if legacy format
        """
        return "://" not in uri

    @staticmethod
    def parse_host_port(uri: str) -> Optional[ParsedUri]:
        """Parse host:port format

        Args:
            uri: URI in host:port format

        Returns:
            ParsedUri if successful, None otherwise
        """
        if ":" not in uri:
            return None

        try:
            # Handle IPv6 addresses that contain multiple colons
            if uri.count(":") > 1:
                # Try to find port at the end (IPv6:port format)
                parts = uri.rsplit(":", 1)
                if len(parts) == 2:
                    host, port_str = parts
                    port = int(port_str)
                    return ParsedUri(scheme="telnet", host=host, port=port)
            else:
                host, port_str = uri.split(":", 1)
                port = int(port_str)
                return ParsedUri(scheme="telnet", host=host, port=port)
        except ValueError:
            return None

    @staticmethod
    def parse_serial_port(uri: str) -> Optional[ParsedUri]:
        """Parse serial port format

        Args:
            uri: URI in serial port format

        Returns:
            ParsedUri if successful, None otherwise
        """
        # Check for COM ports or /dev/tty devices
        if re.match(r"^(COM\d+|/dev/tty\w*)$", uri):
            return ParsedUri(scheme="serial", path=uri)

        return None

    @classmethod
    def parse(cls, uri: str) -> ParsedUri:
        """Parse legacy format URI

        Args:
            uri: Legacy format URI

        Returns:
            ParsedUri object

        Raises:
            ValueError: If URI format is invalid
        """
        # Try host:port format
        result = cls.parse_host_port(uri)
        if result:
            return result

        # Try serial port format
        result = cls.parse_serial_port(uri)
        if result:
            return result

        # Default to serial with the URI as port
        return ParsedUri(scheme="serial", path=uri)


class StandardUriParser:
    """Parse standard URI format connections"""

    @staticmethod
    def parse(uri: str) -> ParsedUri:
        """Parse standard URI format

        Args:
            uri: Standard URI format string

        Returns:
            ParsedUri object

        Raises:
            ValueError: If URI format is invalid
        """
        try:
            parsed = urlparse(uri)
            scheme = parsed.scheme.lower()

            if not scheme:
                raise ValueError("Missing scheme")

            query_params = parse_qs(parsed.query) if parsed.query else {}

            # Parse netloc for host and port
            host = None
            port = None
            if parsed.netloc:
                if ":" in parsed.netloc:
                    host, port_str = parsed.netloc.split(":", 1)
                    port = int(port_str)
                else:
                    host = parsed.netloc

            return ParsedUri(
                scheme=scheme,
                host=host,
                port=port,
                path=parsed.path,
                query_params=query_params,
            )

        except Exception as e:
            raise ValueError(f"Invalid URI format: {uri} ({str(e)})")


class UriParser:
    """Main URI parser that handles both legacy and standard formats"""

    @staticmethod
    def parse(uri: str) -> ParsedUri:
        """Parse URI string

        Args:
            uri: URI string to parse

        Returns:
            ParsedUri object

        Raises:
            ValueError: If URI format is invalid
        """
        if not uri or not isinstance(uri, str):
            raise ValueError("URI must be a non-empty string")

        if LegacyFormatParser.is_legacy_format(uri):
            return LegacyFormatParser.parse(uri)
        else:
            return StandardUriParser.parse(uri)
