"""Configuration handling for jot.

This package contains configuration management and settings.
The config package MUST use only stdlib - it MUST NOT import from any other jot/ module.
This is the lowest dependency layer in the architecture.
"""

from jot.config.paths import get_config_dir, get_data_dir, get_runtime_dir

__all__ = ["get_config_dir", "get_data_dir", "get_runtime_dir"]
