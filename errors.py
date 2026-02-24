#!/usr/bin/env python3
"""
OpenClaw Memory Template - Error Handling Utilities
Proper error messages and recovery strategies
"""

import sys
import traceback
from typing import Optional, Callable, Any
from functools import wraps


# Error codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_CONFIG = 3
EXIT_NETWORK = 4
EXIT_PERMISSION = 5
EXIT_NOT_FOUND = 6


class OpenClawError(Exception):
    """Base exception for OpenClaw errors"""

    def __init__(self, message: str, exit_code: int = EXIT_ERROR):
        """Initialize error

        Args:
            message: Error message
            exit_code: Exit code for this error
        """
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


class ConfigError(OpenClawError):
    """Configuration error"""
    def __init__(self, message: str):
        super().__init__(message, EXIT_CONFIG)


class NetworkError(OpenClawError):
    """Network/connection error"""
    def __init__(self, message: str):
        super().__init__(message, EXIT_NETWORK)


class PermissionError(OpenClawError):
    """Permission error"""
    def __init__(self, message: str):
        super().__init__(message, EXIT_PERMISSION)


class NotFoundError(OpenClawError):
    """File/directory not found error"""
    def __init__(self, path: str):
        super().__init__(f"Not found: {path}", EXIT_NOT_FOUND)


def log_error(error: Exception, context: Optional[str] = None) -> str:
    """Format error for logging

    Args:
        error: Exception object
        context: Optional context string

    Returns:
        Formatted error message
    """
    parts = []

    # Error type
    error_type = type(error).__name__
    parts.append(f"Error: {error_type}")

    # Context
    if context:
        parts.append(f"Context: {context}")

    # Error message
    parts.append(f"Message: {str(error)}")

    # Traceback for unexpected errors
    if not isinstance(error, OpenClawError):
        parts.append(f"Traceback:\n{traceback.format_exc()}")

    return "\n  ".join(parts)


def handle_error(error: Exception, context: Optional[str] = None) -> int:
    """Handle error and return exit code

    Args:
        error: Exception object
        context: Optional context string

    Returns:
        Exit code
    """
    # Import logging here to avoid circular imports
    from logging import get_logger
    logger = get_logger("openclaw.error_handler")

    # Format and log error
    error_msg = log_error(error, context)
    logger.error("error_occurred", message=error_msg, error=error)

    # Print to stderr
    print(f"❌ {error_msg}", file=sys.stderr)

    # Return exit code
    if isinstance(error, OpenClawError):
        return error.exit_code
    return EXIT_ERROR


def safe_execute(
    func: Callable,
    default: Any = None,
    error_callback: Optional[Callable] = None
) -> Any:
    """Execute function safely with error handling

    Args:
        func: Function to execute
        default: Default value to return on error
        error_callback: Optional callback to call on error

    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        if error_callback:
            error_callback(e)
        return default


def retry(
    func: Callable,
    max_attempts: int = 3,
    backoff: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """Retry function with exponential backoff

    Args:
        func: Function to execute
        max_attempts: Maximum retry attempts
        backoff: Initial backoff in seconds
        exceptions: Tuple of exceptions to retry

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    import time
    from logging import get_logger

    logger = get_logger("openclaw.retry")

    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e

            if attempt < max_attempts - 1:
                wait_time = backoff * (2 ** attempt)
                logger.warn(
                    "retry_attempt",
                    function=func.__name__,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                    wait_seconds=wait_time,
                    error=str(e)
                )
                time.sleep(wait_time)
            else:
                logger.error(
                    "retry_failed",
                    function=func.__name__,
                    max_attempts=max_attempts,
                    final_error=str(e)
                )

    raise last_exception


def error_handler_decorator(func: Callable) -> Callable:
    """Decorator for automatic error handling

    Args:
        func: Function to decorate

    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            sys.exit(handle_error(e, context=func.__name__))
    return wrapper


def require_file(path: str) -> None:
    """Require that a file exists

    Args:
        path: File path

    Raises:
        NotFoundError: If file doesn't exist
    """
    from pathlib import Path
    if not Path(path).exists():
        raise NotFoundError(path)


def require_dir(path: str) -> None:
    """Require that a directory exists

    Args:
        path: Directory path

    Raises:
        NotFoundError: If directory doesn't exist
    """
    from pathlib import Path
    p = Path(path)
    if not p.exists() or not p.is_dir():
        raise NotFoundError(path)


def validate_exit_code(code: int) -> None:
    """Validate exit code

    Args:
        code: Exit code to validate

    Raises:
        ValueError: If code is invalid
    """
    if not isinstance(code, int):
        raise ValueError(f"Exit code must be an integer: {code}")
    if code < 0 or code > 255:
        raise ValueError(f"Exit code must be 0-255: {code}")


# Example usage
if __name__ == "__main__":
    from logging import get_logger
    logger = get_logger("openclaw.test")

    # Example 1: Basic error handling
    try:
        require_file("/nonexistent/file.txt")
    except NotFoundError as e:
        print(f"❌ {log_error(e)}")

    # Example 2: Safe execute
    result = safe_execute(
        lambda: 1 / 0,
        default=None,
        error_callback=lambda e: logger.warn("division_skipped", error=str(e))
    )
    print(f"Result: {result}")

    # Example 3: Retry
    try:
        def flaky_function():
            import random
            if random.random() < 0.7:
                raise NetworkError("Connection failed")
            return "success"

        result = retry(flaky_function, max_attempts=5)
        print(f"Retry result: {result}")
    except Exception as e:
        print(f"Retry failed: {log_error(e)}")

    # Example 4: Decorator
    @error_handler_decorator
    def main():
        raise ConfigError("Invalid configuration")

    # main()  # This will exit with error code
