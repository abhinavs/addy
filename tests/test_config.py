"""
Tests for configuration management.
"""

import pytest
from pathlib import Path

from addy.config import ConfigManager


class TestConfigManager:
    """Test ConfigManager functionality."""
    
    def test_init_creates_config_dir(self, temp_dir):
        """Test that ConfigManager creates config directory."""
        config_dir = temp_dir / "test_config"
        config_manager = ConfigManager(str(config_dir))
        
        assert config_dir.exists()
        assert config_dir.stat().st_mode & 0o777 == 0o700
    
    def test_set_and_get_config(self, config_manager):
        """Test setting and getting configuration values."""
        config_manager.set("test_key", "test_value")
        assert config_manager.get("test_key") == "test_value"
    
    def test_get_default_value(self, config_manager):
        """Test getting default value for non-existent key."""
        assert config_manager.get("nonexistent", "default") == "default"
        assert config_manager.get("nonexistent") is None
    
    def test_list_all_config(self, config_manager):
        """Test listing all configuration values."""
        config_manager.set("key1", "value1")
        config_manager.set("key2", "value2")
        
        config = config_manager.list_all()
        assert config == {"key1": "value1", "key2": "value2"}
    
    def test_delete_config(self, config_manager):
        """Test deleting configuration values."""
        config_manager.set("test_key", "test_value")
        assert config_manager.delete("test_key") is True
        assert config_manager.get("test_key") is None
        assert config_manager.delete("nonexistent") is False
    
    def test_get_git_repo_configured(self, config_manager):
        """Test getting Git repository URL when configured."""
        config_manager.set("git-repo", "git@github.com:test/repo.git")
        assert config_manager.get_git_repo() == "git@github.com:test/repo.git"
    
    def test_get_git_repo_not_configured(self, config_manager):
        """Test getting Git repository URL when not configured."""
        with pytest.raises(RuntimeError, match="Git repository not configured"):
            config_manager.get_git_repo()
    
    def test_get_git_branch_default(self, config_manager):
        """Test getting Git branch with default value."""
        assert config_manager.get_git_branch() == "main"
    
    def test_get_git_branch_configured(self, config_manager):
        """Test getting Git branch when configured."""
        config_manager.set("git-branch", "develop")
        assert config_manager.get_git_branch() == "develop"
    
    def test_get_ssh_key_path(self, config_manager):
        """Test getting SSH key path."""
        assert config_manager.get_ssh_key_path() is None
        
        config_manager.set("ssh-key-path", "/path/to/key")
        assert config_manager.get_ssh_key_path() == "/path/to/key"
    
    def test_validate_config_valid(self, config_manager, temp_dir):
        """Test configuration validation with valid config."""
        # Create a temporary SSH key file
        ssh_key = temp_dir / "ssh_key"
        ssh_key.write_text("fake key content")
        
        config_manager.set("git-repo", "git@github.com:test/repo.git")
        config_manager.set("git-branch", "main")
        config_manager.set("ssh-key-path", str(ssh_key))
        
        errors = config_manager.validate_config()
        assert errors == {}
    
    def test_validate_config_missing_repo(self, config_manager):
        """Test configuration validation with missing repo."""
        errors = config_manager.validate_config()
        assert "git-repo" in errors
        assert "required" in errors["git-repo"]
    
    def test_validate_config_invalid_ssh_key(self, config_manager):
        """Test configuration validation with invalid SSH key path."""
        config_manager.set("git-repo", "git@github.com:test/repo.git")
        config_manager.set("ssh-key-path", "/nonexistent/key")
        
        errors = config_manager.validate_config()
        assert "ssh-key-path" in errors
        assert "does not exist" in errors["ssh-key-path"]
    
    def test_config_file_permissions(self, config_manager):
        """Test that config file has correct permissions."""
        config_manager.set("test", "value")
        
        config_file = config_manager.config_file
        assert config_file.exists()
        assert config_file.stat().st_mode & 0o777 == 0o600
    
    def test_invalid_key_validation(self, config_manager):
        """Test validation of configuration keys."""
        with pytest.raises(ValueError, match="non-empty string"):
            config_manager.set("", "value")
        
        with pytest.raises(ValueError, match="non-empty string"):
            config_manager.set("   ", "value")