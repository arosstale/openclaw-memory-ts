#!/usr/bin/env python3
"""
OpenClaw Memory Template - Structured Logging
JSON-formatted logs with fields for observability
"""

import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredLogger:
    """Structured JSON logger for OpenClaw"""

    def __init__(self, name: str, level: str = "INFO"):
        """Initialize structured logger

        Args:
            name: Logger name (e.g., "openclaw.memory")
            level: Log level (DEBUG, INFO, WARN, ERROR)
        """
        self.name = name
        self.level = self._parse_level(level)
        self.log_file = os.environ.get("OPENCLAW_LOG_FILE")

        # Create logs directory if specified
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

    def _parse_level(self, level: str) -> int:
        """Parse log level string to int"""
        levels = {
            "DEBUG": 10,
            "INFO": 20,
            "WARN": 30,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50
        }
        return levels.get(level.upper(), 20)

    def _should_log(self, level: int) -> bool:
        """Check if message should be logged"""
        return level >= self.level

    def _format_timestamp(self) -> str:
        """Format timestamp in ISO 8601"""
        return datetime.utcnow().isoformat() + "Z"

    def _format_message(
        self,
        event: str,
        level: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """Format log message as JSON

        Args:
            event: Event name (e.g., "memory_sync")
            level: Log level (DEBUG, INFO, WARN, ERROR)
            data: Additional fields
            error: Exception object if logging an error

        Returns:
            Dict with all log fields
        """
        message = {
            "timestamp": self._format_timestamp(),
            "level": level,
            "logger": self.name,
            "event": event
        }

        # Add data fields
        if data:
            message.update(data)

        # Add error info if present
        if error:
            message["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }

        return message

    def _write_log(self, message: Dict[str, Any]):
        """Write log message to stdout and optionally to file

        Args:
            message: Log message dict
        """
        # Write to stdout (JSON)
        print(json.dumps(message))

        # Write to file if configured
        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(message) + "\n")
            except Exception as e:
                print(json.dumps({
                    "timestamp": self._format_timestamp(),
                    "level": "ERROR",
                    "logger": "openclaw.logging",
                    "event": "log_write_failed",
                    "error": str(e)
                }))

    def debug(self, event: str, **kwargs):
        """Log debug message

        Args:
            event: Event name
            **kwargs: Additional fields
        """
        if self._should_log(10):
            message = self._format_message(event, "DEBUG", kwargs)
            self._write_log(message)

    def info(self, event: str, **kwargs):
        """Log info message

        Args:
            event: Event name
            **kwargs: Additional fields
        """
        if self._should_log(20):
            message = self._format_message(event, "INFO", kwargs)
            self._write_log(message)

    def warn(self, event: str, **kwargs):
        """Log warning message

        Args:
            event: Event name
            **kwargs: Additional fields
        """
        if self._should_log(30):
            message = self._format_message(event, "WARN", kwargs)
            self._write_log(message)

    def warning(self, event: str, **kwargs):
        """Alias for warn"""
        self.warn(event, **kwargs)

    def error(self, event: str, error: Optional[Exception] = None, **kwargs):
        """Log error message

        Args:
            event: Event name
            error: Exception object
            **kwargs: Additional fields
        """
        if self._should_log(40):
            message = self._format_message(event, "ERROR", kwargs, error)
            self._write_log(message)

    def critical(self, event: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message

        Args:
            event: Event name
            error: Exception object
            **kwargs: Additional fields
        """
        if self._should_log(50):
            message = self._format_message(event, "CRITICAL", kwargs, error)
            self._write_log(message)


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, level: Optional[str] = None) -> StructuredLogger:
    """Get or create a logger instance

    Args:
        name: Logger name
        level: Log level (uses env var if not specified)

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        log_level = level or os.environ.get("OPENCLAW_LOG_LEVEL", "INFO")
        _loggers[name] = StructuredLogger(name, log_level)
    return _loggers[name]


# Convenience functions
def debug(event: str, **kwargs):
    """Log debug message"""
    get_logger("default").debug(event, **kwargs)


def info(event: str, **kwargs):
    """Log info message"""
    get_logger("default").info(event, **kwargs)


def warn(event: str, **kwargs):
    """Log warning message"""
    get_logger("default").warn(event, **kwargs)


def error(event: str, error: Optional[Exception] = None, **kwargs):
    """Log error message"""
    get_logger("default").error(event, error=error, **kwargs)


def critical(event: str, error: Optional[Exception] = None, **kwargs):
    """Log critical message"""
    get_logger("default").critical(event, error=error, **kwargs)


# Example usage
if __name__ == "__main__":
    # Basic usage
    logger = get_logger("openclaw.test")
    logger.info("test_message", user="alice", action="login", duration_ms=123)

    # Convenience functions
    info("memory_sync", atoms=75, duration_ms=523, status="success")

    # Error logging
    try:
        1 / 0
    except Exception as e:
        logger.error("division_failed", error=e, numerator=1, denominator=0)
