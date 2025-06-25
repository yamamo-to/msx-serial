import socket
import select
from dataclasses import dataclass
from .base import Connection, ConnectionConfig
from ..common.color_output import print_exception
import logging


@dataclass
class TelnetConfig(ConnectionConfig):
    """Telnet connection configuration"""

    port: int = 23
    host: str = "localhost"


class TelnetConnection(Connection):
    """High-performance socket-based telnet connection for MSX communication"""

    def __init__(self, config: TelnetConfig):
        self.host = config.host
        self.port = config.port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Set socket options for low latency
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # Connect to host
        self.socket.connect((self.host, self.port))
        self.socket.setblocking(False)  # Non-blocking for instant reads

        self._buffer = bytearray()
        self._connected = True

    def write(self, data: bytes) -> None:
        try:
            self.socket.sendall(data)
        except Exception as e:
            print_exception("Telnet write error", e)
            self._connected = False

    def flush(self) -> None:
        pass  # Not required for socket

    def read(self, size: int) -> bytes:
        try:
            # Fill buffer with available data if needed
            self._fill_buffer_if_needed(size)

            # Return requested size data from buffer
            data = self._buffer[:size]
            self._buffer = self._buffer[size:]
            return bytes(data)
        except Exception as e:
            print_exception("Telnet read error", e)
            return b""

    def _fill_buffer_if_needed(self, required_size: int) -> None:
        """Fill buffer with available data if we don't have enough"""
        if len(self._buffer) >= required_size:
            return

        try:
            # Use select to check for available data without blocking
            ready, _, _ = select.select([self.socket], [], [], 0)
            if ready:
                # Read up to 4096 bytes of available data
                data = self.socket.recv(4096)
                if data:
                    self._buffer.extend(data)
                else:
                    # Connection closed
                    self._connected = False
        except socket.error:
            # No data available or connection error
            pass

    def in_waiting(self) -> int:
        try:
            # Check for immediately available data without blocking
            ready, _, _ = select.select([self.socket], [], [], 0)
            if ready:
                data = self.socket.recv(4096)
                if data:
                    self._buffer.extend(data)
                else:
                    self._connected = False
            return len(self._buffer)
        except Exception:
            return len(self._buffer)

    def close(self) -> None:
        """Close the telnet connection"""
        try:
            self.socket.close()
        except Exception as e:
            # ソケット終了時のエラーをログに記録（通常は無害）
            logging.debug(f"Socket close warning: {e}")
        self._connected = False

    def is_open(self) -> bool:
        return self._connected
