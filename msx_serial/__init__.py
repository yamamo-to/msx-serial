"""
MSX Serial Terminal
"""

from .core.optimized_session import OptimizedMSXTerminalSession

# Use optimized session as main terminal
MSXTerminal = OptimizedMSXTerminalSession

__version__ = "0.5.0"
__all__ = ["MSXTerminal", "OptimizedMSXTerminalSession"]
