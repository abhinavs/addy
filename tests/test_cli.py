"""
Tests for CLI interface.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from addy.cli import cli, _parse_package, check_root


class TestCLI:
    """Test CLI functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_version_command(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "addy 1.0.2" in result.output

    def test_help_command(self):
        """Test help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Git-Driven SSH Access Control" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.ConfigManager")
    def test_config_set_command(self, mock_config_class, mock_geteuid):
        """Test config set command."""
        mock_geteuid.return_value = 0  # Root user
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(
            cli, ["config", "set", "git-repo", "git@github.com:test/repo.git"]
        )

        assert result.exit_code == 0
        mock_config.set.assert_called_once_with(
            "git-repo", "git@github.com:test/repo.git"
        )
        assert "Set git-repo=git@github.com:test/repo.git" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.ConfigManager")
    def test_config_get_command(self, mock_config_class, mock_geteuid):
        """Test config get command."""
        mock_geteuid.return_value = 0  # Root user
        mock_config = Mock()
        mock_config.get.return_value = "git@github.com:test/repo.git"
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "get", "git-repo"])

        assert result.exit_code == 0
        mock_config.get.assert_called_once_with("git-repo")
        assert "git@github.com:test/repo.git" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.ConfigManager")
    def test_config_get_not_found(self, mock_config_class, mock_geteuid):
        """Test config get command for non-existent key."""
        mock_geteuid.return_value = 0  # Root user
        mock_config = Mock()
        mock_config.get.return_value = None
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "get", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.ConfigManager")
    def test_config_list_command(self, mock_config_class, mock_geteuid):
        """Test config list command."""
        mock_geteuid.return_value = 0  # Root user
        mock_config = Mock()
        mock_config.list_all.return_value = {
            "git-repo": "git@github.com:test/repo.git",
            "git-branch": "main",
        }
        mock_config_class.return_value = mock_config

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "list"])

        assert result.exit_code == 0
        assert "git-repo=git@github.com:test/repo.git" in result.output
        assert "git-branch=main" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.UserManager")
    @patch("addy.cli.GitRepository")
    @patch("addy.cli.ConfigManager")
    def test_install_user_package(
        self, mock_config_class, mock_git_class, mock_user_class, mock_geteuid
    ):
        """Test installing user package."""
        mock_geteuid.return_value = 0  # Root user

        # Mock dependencies
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        mock_git = Mock()
        mock_git.get_public_key.return_value = "ssh-rsa AAAAB3... test@example.com"
        mock_git_class.return_value = mock_git

        mock_user = Mock()
        mock_user_class.return_value = mock_user

        runner = CliRunner()
        result = runner.invoke(cli, ["install", "user/alice"])

        assert result.exit_code == 0
        mock_git.sync.assert_called_once()
        mock_git.get_public_key.assert_called_once_with("alice")
        mock_user.create_user.assert_called_once_with("alice")
        mock_user.install_ssh_key.assert_called_once()
        assert "installed successfully" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.SudoManager")
    @patch("addy.cli.UserManager")
    @patch("addy.cli.GitRepository")
    @patch("addy.cli.ConfigManager")
    def test_install_sudo_package(
        self,
        mock_config_class,
        mock_git_class,
        mock_user_class,
        mock_sudo_class,
        mock_geteuid,
    ):
        """Test installing sudo package."""
        mock_geteuid.return_value = 0  # Root user

        # Mock dependencies
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        mock_git = Mock()
        mock_git_class.return_value = mock_git

        mock_user = Mock()
        mock_user.user_exists.return_value = True
        mock_user_class.return_value = mock_user

        mock_sudo = Mock()
        mock_sudo_class.return_value = mock_sudo

        runner = CliRunner()
        result = runner.invoke(cli, ["install", "sudo/alice"])

        assert result.exit_code == 0
        mock_git.sync.assert_called_once()
        mock_sudo.grant_sudo.assert_called_once_with("alice", create_user=True)
        assert "installed successfully" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.SudoManager")
    @patch("addy.cli.UserManager")
    @patch("addy.cli.GitRepository")
    @patch("addy.cli.ConfigManager")
    def test_install_sudo_creates_user_if_not_exists(
        self,
        mock_config_class,
        mock_git_class,
        mock_user_class,
        mock_sudo_class,
        mock_geteuid,
    ):
        """Test installing sudo package creates user if they don't exist."""
        mock_geteuid.return_value = 0  # Root user

        # Mock dependencies
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        mock_git = Mock()
        mock_git_class.return_value = mock_git

        mock_user = Mock()
        mock_user_class.return_value = mock_user

        mock_sudo = Mock()
        mock_sudo_class.return_value = mock_sudo

        runner = CliRunner()
        result = runner.invoke(cli, ["install", "sudo/alice"])

        assert result.exit_code == 0
        mock_git.sync.assert_called_once()
        mock_sudo.grant_sudo.assert_called_once_with("alice", create_user=True)
        assert "installed successfully" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.UserManager")
    def test_remove_user_package(self, mock_user_class, mock_geteuid):
        """Test removing user package."""
        mock_geteuid.return_value = 0  # Root user

        mock_user = Mock()
        mock_user_class.return_value = mock_user

        runner = CliRunner()
        result = runner.invoke(cli, ["remove", "user/alice"])

        assert result.exit_code == 0
        mock_user.remove_ssh_access.assert_called_once_with("alice")
        assert "removed successfully" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.SudoManager")
    @patch("addy.cli.UserManager")
    def test_remove_sudo_package(self, mock_user_class, mock_sudo_class, mock_geteuid):
        """Test removing sudo package."""
        mock_geteuid.return_value = 0  # Root user

        mock_user = Mock()
        mock_user_class.return_value = mock_user

        mock_sudo = Mock()
        mock_sudo_class.return_value = mock_sudo

        runner = CliRunner()
        result = runner.invoke(cli, ["remove", "sudo/alice"])

        assert result.exit_code == 0
        mock_sudo.revoke_sudo.assert_called_once_with("alice")
        assert "removed successfully" in result.output

    @patch("os.geteuid")
    @patch("addy.cli.GitRepository")
    @patch("addy.cli.ConfigManager")
    def test_sync_command(self, mock_config_class, mock_git_class, mock_geteuid):
        """Test sync command."""
        mock_geteuid.return_value = 0  # Root user

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        mock_git = Mock()
        mock_git_class.return_value = mock_git

        runner = CliRunner()
        result = runner.invoke(cli, ["sync"])

        assert result.exit_code == 0
        mock_git.sync.assert_called_once()
        assert "synced successfully" in result.output

    def test_non_root_user(self):
        """Test that non-root users are rejected for privileged commands."""
        with patch("os.geteuid", return_value=1000):  # Non-root user
            runner = CliRunner()
            result = runner.invoke(cli, ["config", "set", "key", "value"])

            assert result.exit_code == 1
            assert "must be run as root" in result.output

    def test_parse_package_valid(self):
        """Test parsing valid package strings."""
        assert _parse_package("user/alice") == ("user", "alice")
        assert _parse_package("sudo/bob") == ("sudo", "bob")
        assert _parse_package("user/test-user") == ("user", "test-user")
        assert _parse_package("user/test_user") == ("user", "test_user")
        assert _parse_package("user/test.user") == ("user", "test.user")

    def test_parse_package_invalid(self):
        """Test parsing invalid package strings."""
        with pytest.raises(ValueError, match="Invalid package format"):
            _parse_package("invalid")

        with pytest.raises(ValueError, match="Invalid username"):
            _parse_package("user/alice/extra")

        with pytest.raises(ValueError, match="Package type must be"):
            _parse_package("invalid/alice")

        with pytest.raises(ValueError, match="Invalid username"):
            _parse_package("user/")

        with pytest.raises(ValueError, match="Invalid username"):
            _parse_package("user/alice@invalid")

    def test_check_root_function(self):
        """Test check_root function directly."""
        with patch("os.geteuid", return_value=0):
            check_root()  # Should not raise

        with patch("os.geteuid", return_value=1000):
            with pytest.raises(SystemExit):
                check_root()
