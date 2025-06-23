"""
MSX Terminal - Compatibility wrapper for refactored architecture
"""

# Backward compatibility import
from .core.terminal_session import MSXTerminalSession

# Alias for backward compatibility
MSXTerminal = MSXTerminalSession

__all__ = ["MSXTerminal", "MSXTerminalSession"]
