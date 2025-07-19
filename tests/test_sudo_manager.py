"""
Tests for sudo management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import subprocess

from addy.sudo_manager import SudoManager


class TestSudoManager:
    """Test SudoManager functionality."""

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.chmod")
    def test_grant_sudo_success(self, mock_chmod, mock_file, mock_subprocess):
        """Test successful sudo grant."""
        mock_subprocess.return_value.returncode = 0  # visudo validation passes

        with patch("pathlib.Path.exists", return_value=False), patch(
            "pathlib.Path.rename"
        ) as mock_rename:

            sudo_manager = SudoManager()
            sudo_manager.grant_sudo("testuser")

            mock_file.assert_called()
            mock_chmod.assert_called_with(
                mock_file.return_value.__enter__.return_value.name, 0o440
            )
            mock_rename.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_grant_sudo_already_exists(self, mock_exists):
        """Test granting sudo when already configured."""
        mock_exists.return_value = True

        sudo_manager = SudoManager()
        sudo_manager.grant_sudo("testuser")  # Should not raise exception

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.chmod")
    @patch("pathlib.Path.unlink")
    def test_grant_sudo_validation_fails(
        self, mock_unlink, mock_chmod, mock_file, mock_subprocess
    ):
        """Test sudo grant when visudo validation fails."""
        mock_subprocess.return_value.returncode = 1  # visudo validation fails

        with patch("pathlib.Path.exists", return_value=False):

            sudo_manager = SudoManager()

            with pytest.raises(RuntimeError, match="Invalid sudoers configuration"):
                sudo_manager.grant_sudo("testuser")

            mock_unlink.assert_called_once()  # Temp file should be cleaned up

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.exists")
    def test_revoke_sudo_success(self, mock_exists, mock_unlink):
        """Test successful sudo revocation."""
        mock_exists.return_value = True

        sudo_manager = SudoManager()
        sudo_manager.revoke_sudo("testuser")

        mock_unlink.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_revoke_sudo_not_configured(self, mock_exists):
        """Test revoking sudo when not configured."""
        mock_exists.return_value = False

        sudo_manager = SudoManager()
        sudo_manager.revoke_sudo("testuser")  # Should not raise exception

    @patch("pathlib.Path.exists")
    def test_has_sudo_access_true(self, mock_exists):
        """Test checking sudo access when user has access."""
        mock_exists.return_value = True

        sudo_manager = SudoManager()
        assert sudo_manager.has_sudo_access("testuser") is True

    @patch("pathlib.Path.exists")
    def test_has_sudo_access_false(self, mock_exists):
        """Test checking sudo access when user doesn't have access."""
        mock_exists.return_value = False

        sudo_manager = SudoManager()
        assert sudo_manager.has_sudo_access("testuser") is False

    def test_list_sudo_users_empty(self):
        """Test listing sudo users when sudoers.d doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            sudo_manager = SudoManager()
            users = sudo_manager.list_sudo_users()
            assert users == []

    @patch("builtins.open", new_callable=mock_open)
    def test_list_sudo_users_with_users(self, mock_file):
        """Test listing sudo users with addy-managed files."""
        # Mock directory contents
        mock_files = [
            Mock(name="alice", is_file=lambda: True),
            Mock(name="bob", is_file=lambda: True),
            Mock(name=".hidden", is_file=lambda: True),
            Mock(name="charlie", is_file=lambda: True),
        ]

        # Mock file contents - only alice and charlie are addy-managed
        def mock_read_side_effect(*args, **kwargs):
            filename = args[0].name
            if filename == "alice":
                return "alice ALL=(ALL) NOPASSWD:ALL"
            elif filename == "bob":
                return "bob ALL=(ALL) ALL"  # Not addy format
            elif filename == "charlie":
                return "charlie ALL=(ALL) NOPASSWD:ALL"
            return ""

        mock_file.return_value.read.side_effect = mock_read_side_effect

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.iterdir", return_value=mock_files
        ):

            sudo_manager = SudoManager()
            users = sudo_manager.list_sudo_users()

            assert sorted(users) == ["alice", "charlie"]

    @patch("subprocess.run")
    def test_validate_sudoers_file_valid(self, mock_subprocess):
        """Test validating a valid sudoers file."""
        mock_subprocess.return_value.returncode = 0

        sudo_manager = SudoManager()
        assert sudo_manager._validate_sudoers_file(Path("/tmp/test")) is True

    @patch("subprocess.run")
    def test_validate_sudoers_file_invalid(self, mock_subprocess):
        """Test validating an invalid sudoers file."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "syntax error"

        sudo_manager = SudoManager()
        assert sudo_manager._validate_sudoers_file(Path("/tmp/test")) is False

    @patch("subprocess.run")
    def test_validate_sudoers_file_visudo_not_found(self, mock_subprocess):
        """Test validating when visudo command is not found."""
        mock_subprocess.side_effect = FileNotFoundError("visudo not found")

        sudo_manager = SudoManager()
        assert (
            sudo_manager._validate_sudoers_file(Path("/tmp/test")) is True
        )  # Assume valid

    @patch("builtins.open", new_callable=mock_open)
    def test_is_addy_sudoers_file_true(self, mock_file):
        """Test identifying addy-managed sudoers file."""
        mock_file.return_value.read.return_value = "testuser ALL=(ALL) NOPASSWD:ALL"

        sudo_manager = SudoManager()
        test_file = Path("/etc/sudoers.d/testuser")

        assert sudo_manager._is_addy_sudoers_file(test_file) is True

    @patch("builtins.open", new_callable=mock_open)
    def test_is_addy_sudoers_file_false(self, mock_file):
        """Test identifying non-addy sudoers file."""
        mock_file.return_value.read.return_value = (
            "testuser ALL=(ALL) ALL"  # Missing NOPASSWD
        )

        sudo_manager = SudoManager()
        test_file = Path("/etc/sudoers.d/testuser")

        assert sudo_manager._is_addy_sudoers_file(test_file) is False

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists")
    def test_get_sudo_info_success(self, mock_exists, mock_stat, mock_file):
        """Test getting sudo information successfully."""
        mock_exists.return_value = True

        # Mock file stats
        mock_stat_result = Mock()
        mock_stat_result.st_mode = 0o100440  # Regular file with 440 permissions
        mock_stat.return_value = mock_stat_result

        # Mock file content
        mock_file.return_value.read.return_value = "testuser ALL=(ALL) NOPASSWD:ALL"

        sudo_manager = SudoManager()
        info = sudo_manager.get_sudo_info("testuser")

        assert info is not None
        assert info["username"] == "testuser"
        assert info["permissions"] == "440"
        assert info["content"] == "testuser ALL=(ALL) NOPASSWD:ALL"
        assert info["is_addy_managed"] is True

    @patch("pathlib.Path.exists")
    def test_get_sudo_info_not_found(self, mock_exists):
        """Test getting sudo info when file doesn't exist."""
        mock_exists.return_value = False

        sudo_manager = SudoManager()
        info = sudo_manager.get_sudo_info("nonexistent")

        assert info is None

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    def test_verify_sudoers_integrity(self, mock_file, mock_subprocess):
        """Test verifying sudoers integrity."""
        mock_subprocess.return_value.returncode = 0  # All files valid

        # Mock directory and files
        mock_files = [
            Mock(name="alice", is_file=lambda: True),
            Mock(name="bob", is_file=lambda: True),
        ]

        # Mock file contents - both addy-managed
        def mock_read_side_effect(*args, **kwargs):
            filename = args[0].name
            return f"{filename} ALL=(ALL) NOPASSWD:ALL"

        mock_file.return_value.read.side_effect = mock_read_side_effect

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.iterdir", return_value=mock_files
        ):

            sudo_manager = SudoManager()
            results = sudo_manager.verify_sudoers_integrity()

            assert sorted(results["valid_files"]) == ["alice", "bob"]
            assert results["invalid_files"] == []
            assert results["errors"] == []

    def test_verify_sudoers_integrity_no_directory(self):
        """Test verifying integrity when sudoers.d doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            sudo_manager = SudoManager()
            results = sudo_manager.verify_sudoers_integrity()

            assert "Sudoers directory does not exist" in results["errors"]
