"""
Tests for Git operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import git

from addy.git_ops import GitRepository
from addy.config import ConfigManager


class TestGitRepository:
    """Test GitRepository functionality."""
    
    def test_init_creates_repo_dir(self, config_manager, temp_dir):
        """Test that GitRepository creates repo directory."""
        repo_dir = temp_dir / "test_repo"
        git_repo = GitRepository(config_manager, str(repo_dir))
        
        assert repo_dir.exists()
        assert repo_dir.stat().st_mode & 0o777 == 0o700
    
    @patch('git.Repo.clone_from')
    def test_sync_clone_new_repo(self, mock_clone, config_manager, git_repo):
        """Test syncing by cloning new repository."""
        config_manager.set("git-repo", "git@github.com:test/repo.git")
        config_manager.set("git-branch", "main")
        
        mock_repo = Mock()
        mock_clone.return_value = mock_repo
        
        git_repo.sync()
        
        mock_clone.assert_called_once()
        args, kwargs = mock_clone.call_args
        assert args[0] == "git@github.com:test/repo.git"
        assert args[1] == git_repo.repo_dir
        assert kwargs["branch"] == "main"
    
    @patch('git.Repo')
    def test_sync_update_existing_repo(self, mock_repo_class, config_manager, git_repo):
        """Test syncing by updating existing repository."""
        config_manager.set("git-repo", "git@github.com:test/repo.git")
        config_manager.set("git-branch", "main")
        
        # Create .git directory to simulate existing repo
        (git_repo.repo_dir / '.git').mkdir(parents=True)
        
        # Mock Git repository
        mock_repo = Mock()
        mock_branch = Mock()
        mock_branch.name = "main"
        mock_repo.active_branch = mock_branch
        mock_remote = Mock()
        mock_repo.remote.return_value = mock_remote
        mock_repo_class.return_value = mock_repo
        
        git_repo.sync()
        
        mock_repo.remote.assert_called_with('origin')
        mock_remote.fetch.assert_called_once()
        mock_repo.git.reset.assert_called_with('--hard', 'origin/main')
    
    def test_get_public_key_valid(self, config_manager, git_repo, sample_ssh_key):
        """Test getting valid public key."""
        # Create users directory and key file
        users_dir = git_repo.repo_dir / "users"
        users_dir.mkdir(parents=True)
        key_file = users_dir / "alice.pub"
        key_file.write_text(sample_ssh_key)
        
        result = git_repo.get_public_key("alice")
        assert result == sample_ssh_key
    
    def test_get_public_key_not_found(self, config_manager, git_repo):
        """Test getting public key when file doesn't exist."""
        with pytest.raises(RuntimeError, match="Public key not found"):
            git_repo.get_public_key("nonexistent")
    
    def test_get_public_key_empty_file(self, config_manager, git_repo):
        """Test getting public key from empty file."""
        users_dir = git_repo.repo_dir / "users"
        users_dir.mkdir(parents=True)
        key_file = users_dir / "alice.pub"
        key_file.write_text("")
        
        with pytest.raises(RuntimeError, match="Empty public key file"):
            git_repo.get_public_key("alice")
    
    def test_get_public_key_invalid_key(self, config_manager, git_repo):
        """Test getting invalid public key."""
        users_dir = git_repo.repo_dir / "users"
        users_dir.mkdir(parents=True)
        key_file = users_dir / "alice.pub"
        key_file.write_text("invalid key content")
        
        with pytest.raises(RuntimeError, match="Invalid SSH public key"):
            git_repo.get_public_key("alice")
    
    def test_validate_ssh_public_key_valid(self, git_repo, sample_ssh_key):
        """Test validation of valid SSH public key."""
        assert git_repo._validate_ssh_public_key(sample_ssh_key) is True
    
    def test_validate_ssh_public_key_invalid_format(self, git_repo):
        """Test validation of invalid SSH public key format."""
        assert git_repo._validate_ssh_public_key("invalid key") is False
        assert git_repo._validate_ssh_public_key("ssh-rsa") is False
        assert git_repo._validate_ssh_public_key("") is False
    
    def test_validate_ssh_public_key_unsupported_type(self, git_repo):
        """Test validation of unsupported key type."""
        invalid_key = "ssh-unknown AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqaj test@example.com"
        assert git_repo._validate_ssh_public_key(invalid_key) is False
    
    def test_validate_ssh_public_key_invalid_base64(self, git_repo):
        """Test validation of key with invalid base64."""
        invalid_key = "ssh-rsa invalid_base64! test@example.com"
        assert git_repo._validate_ssh_public_key(invalid_key) is False
    
    def test_list_users_empty(self, config_manager, git_repo):
        """Test listing users when no users exist."""
        assert git_repo.list_users() == []
    
    def test_list_users_with_keys(self, config_manager, git_repo, sample_ssh_key):
        """Test listing users with public keys."""
        users_dir = git_repo.repo_dir / "users"
        users_dir.mkdir(parents=True)
        
        (users_dir / "alice.pub").write_text(sample_ssh_key)
        (users_dir / "bob.pub").write_text(sample_ssh_key)
        (users_dir / "charlie.pub").write_text(sample_ssh_key)
        
        users = git_repo.list_users()
        assert sorted(users) == ["alice", "bob", "charlie"]
    
    def test_get_git_env_no_ssh_key(self, config_manager, git_repo):
        """Test getting Git environment without SSH key."""
        env = git_repo._get_git_env()
        assert 'GIT_SSH_COMMAND' not in env
    
    def test_get_git_env_with_ssh_key(self, config_manager, git_repo, temp_dir):
        """Test getting Git environment with SSH key."""
        ssh_key = temp_dir / "ssh_key"
        ssh_key.write_text("fake key")
        config_manager.set("ssh-key-path", str(ssh_key))
        
        env = git_repo._get_git_env()
        assert 'GIT_SSH_COMMAND' in env
        assert str(ssh_key) in env['GIT_SSH_COMMAND']
        assert 'StrictHostKeyChecking=no' in env['GIT_SSH_COMMAND']
    
    @patch('git.Repo')
    def test_get_repo_info(self, mock_repo_class, config_manager, git_repo):
        """Test getting repository information."""
        config_manager.set("git-repo", "git@github.com:test/repo.git")
        config_manager.set("git-branch", "main")
        
        # Mock Git repository
        mock_repo = Mock()
        mock_commit = Mock()
        mock_commit.hexsha = "abcdef1234567890"
        mock_commit.committed_datetime.isoformat.return_value = "2023-01-01T12:00:00"
        mock_commit.message = "Test commit message\n"
        mock_repo.head.commit = mock_commit
        
        git_repo._repo = mock_repo
        
        info = git_repo.get_repo_info()
        
        assert info["url"] == "git@github.com:test/repo.git"
        assert info["branch"] == "main"
        assert info["last_commit"] == "abcdef12"
        assert info["last_commit_date"] == "2023-01-01T12:00:00"
        assert info["last_commit_message"] == "Test commit message"
    
    def test_get_repo_info_no_repo(self, config_manager, git_repo):
        """Test getting repository information when no repo loaded."""
        info = git_repo.get_repo_info()
        assert info == {}
    
    def test_sync_git_command_error(self, config_manager, git_repo):
        """Test sync with Git command error."""
        config_manager.set("git-repo", "invalid-repo-url")
        
        with pytest.raises(RuntimeError, match="Failed to sync Git repository"):
            git_repo.sync()