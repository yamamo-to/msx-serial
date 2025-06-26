"""
MSX Serial Terminal
"""

from .__main__ import main
from .core.msx_session import MSXSession

# Use optimized session as main terminal
MSXTerminal = MSXSession

# Version is automatically managed by setuptools_scm
try:
    from ._version import version as __version__
except ImportError:
    # Fallback for development
    __version__ = "0.0.0.dev"

__all__ = ["MSXSession", "MSXTerminal", "main"]
