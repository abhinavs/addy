"""
Configuration management for addy.

Originally used a simple key-value store, but switched to YAML for better
human readability and structure. The /etc/addy location follows Unix conventions.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages addy configuration."""

    DEFAULT_CONFIG_DIR = "/etc/addy"
    DEFAULT_CONFIG_FILE = "config.yaml"

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Directory to store configuration. Defaults to /etc/addy
        """
        self.config_dir = Path(config_dir or self.DEFAULT_CONFIG_DIR)
        self.config_file = self.config_dir / self.DEFAULT_CONFIG_FILE
        self._config_cache: Optional[Dict[str, Any]] = None

        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists with proper permissions."""
        try:
            self.config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            logger.debug(f"Configuration directory: {self.config_dir}")
        except PermissionError:
            raise RuntimeError(
                f"Permission denied creating config directory: {self.config_dir}"
            )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self._config_cache is not None:
            return self._config_cache

        if not self.config_file.exists():
            self._config_cache = {}
            return self._config_cache

        try:
            with open(self.config_file, "r") as f:
                self._config_cache = yaml.safe_load(f) or {}
            logger.debug(f"Loaded configuration from {self.config_file}")
        except (yaml.YAMLError, PermissionError) as e:
            raise RuntimeError(f"Failed to load configuration: {e}")

        return self._config_cache

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False)

            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)
            self._config_cache = config
            logger.debug(f"Saved configuration to {self.config_file}")

        except (yaml.YAMLError, PermissionError) as e:
            raise RuntimeError(f"Failed to save configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        config = self._load_config()
        return config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Configuration key must be a non-empty string")

        config = self._load_config()
        config[key] = value
        self._save_config(config)
        logger.info(f"Set configuration: {key}")

    def delete(self, key: str) -> bool:
        """Delete a configuration value.

        Args:
            key: Configuration key to delete

        Returns:
            True if key was deleted, False if key didn't exist
        """
        config = self._load_config()
        if key in config:
            del config[key]
            self._save_config(config)
            logger.info(f"Deleted configuration: {key}")
            return True
        return False

    def list_all(self) -> Dict[str, Any]:
        """Get all configuration values.

        Returns:
            Dictionary of all configuration key-value pairs
        """
        return self._load_config().copy()

    def get_git_repo(self) -> str:
        """Get Git repository URL.

        Returns:
            Git repository URL

        Raises:
            RuntimeError: If git-repo is not configured
        """
        repo = self.get("git-repo")
        if not repo:
            raise RuntimeError(
                "Git repository not configured. Run: addy config set git-repo <repo-url>"
            )
        return repo

    def get_git_branch(self) -> str:
        """Get Git branch.

        Returns:
            Git branch name (defaults to 'main')
        """
        return self.get("git-branch", "main")

    def get_ssh_key_path(self) -> Optional[str]:
        """Get SSH private key path for Git access.

        Returns:
            SSH private key path or None
        """
        return self.get("ssh-key-path")

    def validate_config(self) -> Dict[str, str]:
        """Validate current configuration.

        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}

        # Check git-repo
        git_repo = self.get("git-repo")
        if not git_repo:
            errors["git-repo"] = "Git repository URL is required"
        elif not isinstance(git_repo, str):
            errors["git-repo"] = "Git repository URL must be a string"

        # Check SSH key path if specified
        ssh_key_path = self.get_ssh_key_path()
        if ssh_key_path:
            if not isinstance(ssh_key_path, str):
                errors["ssh-key-path"] = "SSH key path must be a string"
            elif not Path(ssh_key_path).exists():
                errors["ssh-key-path"] = f"SSH key file does not exist: {ssh_key_path}"

        # Check git-branch
        git_branch = self.get("git-branch")
        if git_branch and not isinstance(git_branch, str):
            errors["git-branch"] = "Git branch must be a string"

        return errors
