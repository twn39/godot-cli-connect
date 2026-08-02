"""
Custom exceptions for godot-cli-connect
"""

class GodotCliError(Exception):
    """Base exception class for godot-cli-connect errors."""
    pass

class GodotNotFoundError(GodotCliError):
    """Raised when Godot executable cannot be located."""
    pass

class GodotExecutionError(GodotCliError):
    """Raised when a Godot subprocess execution fails unexpectedly."""
    pass
