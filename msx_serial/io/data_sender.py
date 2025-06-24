"""
Data sender for terminal communication
"""

from ..connection.base import Connection


class DataSender:
    """Handle data transmission to MSX"""

    def __init__(self, connection: Connection, encoding: str = "msx-jp"):
        self.connection = connection
        self.encoding = encoding
        self.data_processor = None  # Reference to data processor for echo detection

    def set_data_processor(self, processor) -> None:
        """Set reference to data processor for echo detection

        Args:
            processor: DataProcessor instance
        """
        self.data_processor = processor

    def send(self, user_input: str) -> None:
        """Send user input to MSX

        Args:
            user_input: User input to send
        """
        # Notify data processor of the command for echo detection
        if self.data_processor and hasattr(self.data_processor, "set_last_command"):
            self.data_processor.set_last_command(user_input.strip())

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
