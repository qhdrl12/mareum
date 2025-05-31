"""
Configuration-related exception classes.

This module contains all exception classes related to configuration parsing,
validation, and loading. Centralized exception management improves maintainability
and provides consistent error handling across the application.
"""

from typing import Any, Dict, List, Optional


class ConfigError(Exception):
    """Base exception for configuration loading errors."""
    
    def __init__(self, message: str, config_path: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.config_path = config_path
        self.cause = cause
    
    def __str__(self) -> str:
        """Return a detailed error message."""
        base_msg = super().__str__()
        
        details = []
        if self.config_path:
            details.append(f"Config path: {self.config_path}")
        if self.cause:
            details.append(f"Caused by: {type(self.cause).__name__}: {self.cause}")
        
        if details:
            return f"{base_msg}\n  " + "\n  ".join(details)
        return base_msg


class ConfigParseError(Exception):
    """Exception raised when configuration parsing fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    
    def __init__(self, message: str, errors: List[str]):
        super().__init__(message)
        self.errors = errors 