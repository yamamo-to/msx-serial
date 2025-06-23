"""
Data sender for terminal communication
"""

from ..connection.base import Connection


class DataSender:
    """Handle data transmission to MSX"""

    def __init__(self, connection: Connection, encoding: str = "msx-jp"):
        self.connection = connection
        self.encoding = encoding

    def send(self, user_input: str) -> None:
        """Send user input to MSX

        Args:
            user_input: User input to send
        """
        lines = user_input.splitlines()

        for line in lines:
            if line.strip() == "^C":
                self.connection.write(b"\x03")
            elif line.strip() == "^[":
                self.connection.write(b"\x1b")
            else:
                self.connection.write((line + "\r\n").encode(self.encoding))

        if len(lines) == 0:
            self.connection.write(("\r\n").encode(self.encoding))

        self.connection.flush()
