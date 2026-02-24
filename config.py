#!/usr/bin/env python3
"""
OpenClaw Memory Template - Configuration Management
YAML configuration with validation and environment variable support
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ValidationError(Exception):
    """Configuration validation error"""
    pass


class Config:
    """OpenClaw configuration manager"""

    # Default configuration
    DEFAULTS = {
        "workspace": "$HOME/openclaw-agent",
        "memory_dir": "$WORKSPACE/memory",
        "git_remote": "origin/main",
        "msam_api": "http://localhost:3001",
        "msam_api_host": "127.0.0.1",
        "msam_api_port": "3001",
        "log_level": "INFO",
        "log_file": ".openclaw/logs/openclaw.log",
        "health_host": "0.0.0.0",
        "health_port": "8765"
    }

    # Required fields
    REQUIRED_FIELDS = ["workspace", "memory_dir", "git_remote"]

    # Valid log levels
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration

        Args:
            config_path: Path to config.yaml (default: .openclaw/config.yaml)
        """
        self.config_path = Path(config_path) if config_path else None
        self.config = self._load_config()

    def _expand_vars(self, value: str) -> str:
        """Expand environment variables in value

        Args:
            value: String with variables ($VAR, ${VAR})

        Returns:
            String with variables expanded
        """
        # Expand $VAR and ${VAR}
        result = value
        for key, val in os.environ.items():
            result = result.replace(f"${key}", val)
            result = result.replace(f"${{{key}}}", val)
        return result

    def _resolve_path(self, value: str) -> Path:
        """Resolve path with variable expansion

        Args:
            value: Path string

        Returns:
            Resolved Path object
        """
        expanded = self._expand_vars(value)
        return Path(expanded).expanduser()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with defaults

        Returns:
            Configuration dictionary
        """
        # Start with defaults
        config = self.DEFAULTS.copy()

        # Load from file if exists
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config.update(file_config)
            except Exception as e:
                print(f"⚠️  Warning: Failed to load config file: {e}", file=sys.stderr)

        # Override with environment variables
        env_overrides = {
            "OPENCLAW_WORKSPACE": "workspace",
            "OPENCLAW_MEMORY_DIR": "memory_dir",
            "OPENCLAW_GIT_REMOTE": "git_remote",
            "OPENCLAW_MSAM_API": "msam_api",
            "OPENCLAW_MSAM_API_HOST": "msam_api_host",
            "OPENCLAW_MSAM_API_PORT": "msam_api_port",
            "OPENCLAW_LOG_LEVEL": "log_level",
            "OPENCLAW_LOG_FILE": "log_file",
            "OPENCLAW_HEALTH_HOST": "health_host",
            "OPENCLAW_HEALTH_PORT": "health_port"
        }

        for env_var, config_key in env_overrides.items():
            if env_var in os.environ:
                config[config_key] = os.environ[env_var]

        return config

    def validate(self) -> None:
        """Validate configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not self.config.get(field):
                raise ValidationError(f"Missing required field: {field}")

        # Check log level
        log_level = self.config.get("log_level", "INFO")
        if log_level.upper() not in self.VALID_LOG_LEVELS:
            raise ValidationError(
                f"Invalid log level: {log_level}. "
                f"Valid levels: {', '.join(self.VALID_LOG_LEVELS)}"
            )

        # Check workspace directory exists or is creatable
        workspace = self.get("workspace")
        workspace_path = Path(workspace)
        if workspace_path.exists() and not workspace_path.is_dir():
            raise ValidationError(f"Workspace exists but is not a directory: {workspace}")

        # Check port numbers
        for port_field in ["msam_api_port", "health_port"]:
            port = self.config.get(port_field)
            try:
                port_int = int(port)
                if port_int < 1 or port_int > 65535:
                    raise ValidationError(f"Invalid port number for {port_field}: {port_int}")
            except ValueError:
                raise ValidationError(f"Port must be a number: {port_field}={port}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        value = self.config.get(key, default)

        # Expand variables for string values
        if isinstance(value, str):
            return self._expand_vars(value)

        return value

    def get_path(self, key: str, default: Optional[str] = None) -> Path:
        """Get configuration value as resolved Path

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Resolved Path object
        """
        value = self.get(key, default)
        return self._resolve_path(value)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value

        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value

    def save(self, path: Optional[str] = None) -> None:
        """Save configuration to file

        Args:
            path: Path to save (default: self.config_path)
        """
        save_path = Path(path) if path else self.config_path

        if not save_path:
            raise ValidationError("No config path specified")

        # Create parent directory
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as YAML
        with open(save_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def print(self) -> None:
        """Print current configuration"""
        print("📋 OpenClaw Configuration")
        print("=" * 40)
        for key, value in self.config.items():
            # Expand variables for display
            display_value = self._expand_vars(value) if isinstance(value, str) else value
            print(f"  {key}: {display_value}")


def load_config(config_path: Optional[str] = None, validate: bool = True) -> Config:
    """Load and validate configuration

    Args:
        config_path: Path to config.yaml (default: .openclaw/config.yaml)
        validate: Whether to validate configuration (default: True)

    Returns:
        Config object

    Raises:
        ValidationError: If configuration is invalid
    """
    config = Config(config_path)

    if validate:
        config.validate()

    return config


# Example usage
if __name__ == "__main__":
    # Load configuration
    config = load_config()

    # Print configuration
    config.print()

    # Get values
    workspace = config.get_path("workspace")
    git_remote = config.get("git_remote")
    log_level = config.get("log_level")

    print()
    print(f"Workspace: {workspace}")
    print(f"Git Remote: {git_remote}")
    print(f"Log Level: {log_level}")

    # Set and save
    print()
    config.set("log_level", "DEBUG")
    config.save()
    print("✅ Configuration saved")
