"""
MSX Serial Terminal
"""

from .core.optimized_session import OptimizedMSXTerminalSession
from .__main__ import main

# Use optimized session as main terminal
MSXTerminal = OptimizedMSXTerminalSession

# Version is automatically managed by setuptools_scm
try:
    from ._version import version as __version__
except ImportError:
    # Fallback for development
    __version__ = "0.0.0.dev"

__all__ = ["MSXTerminal", "OptimizedMSXTerminalSession", "main"]
