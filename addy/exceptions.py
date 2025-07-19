"""
Custom exceptions for addy.

Started with simple RuntimeErrors everywhere, but as the project grew
it became clear we needed more specific exception types for better
error handling and user experience.
"""


class AddyError(Exception):
    """Base exception for all addy-related errors."""
    pass


class ConfigurationError(AddyError):
    """Raised when there's an issue with configuration."""
    pass


class GitRepositoryError(AddyError):
    """Raised when Git operations fail."""
    pass


class UserManagementError(AddyError):
    """Raised when user operations fail."""
    pass


class SudoManagementError(AddyError):
    """Raised when sudo operations fail."""
    pass


class SSHKeyError(AddyError):
    """Raised when SSH key validation or operations fail."""
    pass