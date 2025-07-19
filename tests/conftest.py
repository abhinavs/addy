"""
Pytest configuration and fixtures for addy tests.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import git

from addy.config import ConfigManager
from addy.git_ops import GitRepository
from addy.user_manager import UserManager
from addy.sudo_manager import SudoManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def config_manager(temp_dir):
    """Create a ConfigManager instance with temporary directory."""
    config_dir = temp_dir / "config"
    return ConfigManager(str(config_dir))


@pytest.fixture
def git_repo(config_manager, temp_dir):
    """Create a GitRepository instance with temporary directory."""
    repo_dir = temp_dir / "repo"
    return GitRepository(config_manager, str(repo_dir))


@pytest.fixture
def mock_user_manager():
    """Create a mock UserManager for testing."""
    return Mock(spec=UserManager)


@pytest.fixture
def mock_sudo_manager():
    """Create a mock SudoManager for testing."""
    return Mock(spec=SudoManager)


@pytest.fixture
def sample_ssh_key():
    """Sample SSH public key for testing."""
    return "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhZh7Z8QJ5L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L8F5K6H6L test@example.com"


@pytest.fixture
def mock_git_repo(temp_dir):
    """Create a mock Git repository for testing."""
    repo_dir = temp_dir / "test_repo"
    repo_dir.mkdir()

    # Initialize Git repo
    repo = git.Repo.init(repo_dir)

    # Create users directory and sample key
    users_dir = repo_dir / "users"
    users_dir.mkdir()

    # Add sample user key
    sample_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7vbqajDhZh7Z8QJ5L8F5K6H6L8F5K6H6L test@example.com"
    (users_dir / "alice.pub").write_text(sample_key)
    (users_dir / "bob.pub").write_text(sample_key)

    # Add and commit
    repo.index.add([str(users_dir / "alice.pub"), str(users_dir / "bob.pub")])
    repo.index.commit("Initial commit with test users")

    return repo_dir


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing system commands."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_pwd():
    """Mock pwd module for testing user operations."""
    with patch("pwd.getpwnam") as mock_getpwnam, patch("pwd.getpwall") as mock_getpwall:

        # Mock user info
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_gid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_user.pw_shell = "/bin/bash"

        mock_getpwnam.return_value = mock_user
        mock_getpwall.return_value = [mock_user]

        yield mock_getpwnam, mock_getpwall


@pytest.fixture
def mock_os_operations():
    """Mock OS operations for testing."""
    with patch("os.chown") as mock_chown, patch("os.chmod") as mock_chmod, patch(
        "os.geteuid"
    ) as mock_geteuid:

        mock_geteuid.return_value = 0  # Simulate root user
        yield mock_chown, mock_chmod, mock_geteuid
