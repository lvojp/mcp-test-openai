"""
Filesystem Server Exceptions
"""

class FilesystemError(Exception):
    """Base exception for filesystem errors"""
    pass

class PathNotFoundError(FilesystemError):
    """Raised when a path is not found"""
    pass

class AccessError(FilesystemError):
    """Raised when access to a path is denied"""
    pass

class InvalidPathError(FilesystemError):
    """Raised when a path is invalid or contains invalid characters"""
    pass