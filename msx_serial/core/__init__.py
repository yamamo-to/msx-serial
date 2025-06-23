"""Core MSX terminal components"""

from .optimized_session import OptimizedMSXTerminalSession

# Use optimized session as default
MSXTerminalSession = OptimizedMSXTerminalSession

__all__ = ["OptimizedMSXTerminalSession", "MSXTerminalSession"]
