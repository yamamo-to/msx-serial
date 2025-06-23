"""
User Input Handler - Compatibility wrapper for refactored architecture
"""

# Backward compatibility import
from ..io.user_interface import UserInterface

# Alias for backward compatibility
UserInputHandler = UserInterface

__all__ = ["UserInputHandler", "UserInterface"]
