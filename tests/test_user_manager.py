"""
Tests for user management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess

from addy.user_manager import UserManager


class TestUserManager:
    """Test UserManager functionality."""

    def test_user_exists_true(self, mock_pwd):
        """Test checking if user exists when user exists."""
        mock_getpwnam, _ = mock_pwd
        user_manager = UserManager()

        assert user_manager.user_exists("testuser") is True
        mock_getpwnam.assert_called_with("testuser")

    def test_user_exists_false(self, mock_pwd):
        """Test checking if user exists when user doesn't exist."""
        mock_getpwnam, _ = mock_pwd
        mock_getpwnam.side_effect = KeyError("User not found")
        user_manager = UserManager()

        assert user_manager.user_exists("nonexistent") is False

    @patch("subprocess.run")
    @patch("pwd.getpwnam")
    def test_create_user_success(
        self, mock_getpwnam, mock_subprocess, mock_os_operations
    ):
        """Test successful user creation."""
        # First call (user_exists) raises KeyError, second call succeeds
        mock_user = Mock()
        mock_user.pw_dir = "/home/newuser"  # Use real string path
        mock_user.pw_uid = 1000
        mock_user.pw_gid = 1000
        mock_getpwnam.side_effect = [KeyError("User not found"), mock_user]
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = ""

        with patch("pathlib.Path.mkdir") as mock_mkdir, patch("os.chown") as mock_chown:

            user_manager = UserManager()
            user_manager.create_user("newuser")

        mock_subprocess.assert_called()
        args = mock_subprocess.call_args[0][0]
        assert "useradd" in args
        assert "-m" in args
        assert "newuser" in args

    @patch("pwd.getpwnam")
    def test_create_user_already_exists(self, mock_getpwnam):
        """Test creating user that already exists."""
        mock_user = Mock()
        mock_getpwnam.return_value = mock_user

        user_manager = UserManager()
        user_manager.create_user("existinguser")  # Should not raise exception

    @patch("subprocess.run")
    @patch("pwd.getpwnam")
    def test_create_user_command_fails(self, mock_getpwnam, mock_subprocess):
        """Test user creation when useradd command fails."""
        mock_getpwnam.side_effect = KeyError("User not found")
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "useradd", stderr="Permission denied"
        )

        user_manager = UserManager()

        with pytest.raises(RuntimeError, match="Failed to create user"):
            user_manager.create_user("newuser")

    @patch("builtins.open", create=True)
    @patch("os.chmod")
    @patch("os.chown")
    @patch("pwd.getpwnam")
    def test_install_ssh_key_success(
        self, mock_getpwnam, mock_chown, mock_chmod, mock_open
    ):
        """Test successful SSH key installation."""
        # Mock user info
        mock_user = Mock()
        mock_user.pw_uid = 1000
        mock_user.pw_gid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_getpwnam.return_value = mock_user

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with patch("pathlib.Path.exists", return_value=False), patch(
            "pathlib.Path.mkdir"
        ):

            user_manager = UserManager()
            user_manager.install_ssh_key(
                "testuser", "ssh-rsa AAAAB3... test@example.com"
            )

            mock_file.write.assert_called_once()
            mock_chmod.assert_called()
            mock_chown.assert_called()

    @patch("builtins.open", create=True)
    @patch("pwd.getpwnam")
    def test_install_ssh_key_already_exists(self, mock_getpwnam, mock_open):
        """Test installing SSH key that already exists."""
        # Mock user info
        mock_user = Mock()
        mock_user.pw_uid = 1000
        mock_user.pw_gid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_getpwnam.return_value = mock_user

        # Mock file with existing key
        test_key = "ssh-rsa AAAAB3... test@example.com"
        mock_file = MagicMock()
        mock_file.read.return_value = test_key
        mock_open.return_value.__enter__.return_value = mock_file

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.mkdir"
        ), patch("os.chown"), patch("os.chmod"):

            user_manager = UserManager()
            user_manager.install_ssh_key("testuser", test_key)

            # Should not write again
            mock_file.write.assert_not_called()

    @patch("pwd.getpwnam")
    def test_install_ssh_key_user_not_found(self, mock_getpwnam):
        """Test installing SSH key for non-existent user."""
        mock_getpwnam.side_effect = KeyError("User not found")

        user_manager = UserManager()

        with pytest.raises(RuntimeError, match="User testuser does not exist"):
            user_manager.install_ssh_key(
                "testuser", "ssh-rsa AAAAB3... test@example.com"
            )

    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.exists")
    @patch("pwd.getpwnam")
    def test_remove_ssh_access_success(self, mock_getpwnam, mock_exists, mock_unlink):
        """Test successful SSH access removal."""
        # Mock user info
        mock_user = Mock()
        mock_user.pw_dir = "/home/testuser"
        mock_getpwnam.return_value = mock_user
        mock_exists.return_value = True

        user_manager = UserManager()
        user_manager.remove_ssh_access("testuser")

        mock_unlink.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("pwd.getpwnam")
    def test_remove_ssh_access_no_keys(self, mock_getpwnam, mock_exists):
        """Test removing SSH access when no keys exist."""
        # Mock user info
        mock_user = Mock()
        mock_user.pw_dir = "/home/testuser"
        mock_getpwnam.return_value = mock_user
        mock_exists.return_value = False

        user_manager = UserManager()
        user_manager.remove_ssh_access("testuser")  # Should not raise exception

    @patch("pwd.getpwnam")
    def test_remove_ssh_access_user_not_found(self, mock_getpwnam):
        """Test removing SSH access for non-existent user."""
        mock_getpwnam.side_effect = KeyError("User not found")

        user_manager = UserManager()
        user_manager.remove_ssh_access("nonexistent")  # Should not raise exception

    @patch("builtins.open", create=True)
    @patch("pathlib.Path.exists")
    @patch("pwd.getpwnam")
    def test_get_user_info_success(self, mock_getpwnam, mock_exists, mock_open):
        """Test getting user information successfully."""
        # Mock user info
        mock_user = Mock()
        mock_user.pw_uid = 1000
        mock_user.pw_gid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_user.pw_shell = "/bin/bash"
        mock_getpwnam.return_value = mock_user
        mock_exists.return_value = True

        # Mock authorized_keys file with 2 keys
        mock_file = MagicMock()
        mock_file.__iter__.return_value = [
            "ssh-rsa AAAAB3... key1",
            "ssh-rsa AAAAB3... key2",
            "# comment line",
            "",
        ]
        mock_open.return_value.__enter__.return_value = mock_file

        user_manager = UserManager()
        info = user_manager.get_user_info("testuser")

        assert info is not None
        assert info["username"] == "testuser"
        assert info["uid"] == 1000
        assert info["gid"] == 1000
        assert info["home_dir"] == "/home/testuser"
        assert info["shell"] == "/bin/bash"
        assert info["ssh_key_count"] == 2
        assert info["has_ssh_access"] is True

    @patch("pwd.getpwnam")
    def test_get_user_info_user_not_found(self, mock_getpwnam):
        """Test getting user info for non-existent user."""
        mock_getpwnam.side_effect = KeyError("User not found")

        user_manager = UserManager()
        info = user_manager.get_user_info("nonexistent")

        assert info is None

    @patch("pwd.getpwall")
    def test_list_users_with_ssh(self, mock_getpwall):
        """Test listing users with SSH access."""
        # Mock multiple users
        mock_users = []
        for i, name in enumerate(["user1", "user2", "systemuser"]):
            mock_user = Mock()
            mock_user.pw_name = name
            mock_user.pw_uid = 1000 + i
            mock_user.pw_dir = f"/home/{name}"
            mock_users.append(mock_user)

        mock_getpwall.return_value = mock_users

        def mock_path_exists(self):
            path_str = str(self)
            return "user1" in path_str or "user2" in path_str

        with patch("pathlib.Path.exists", mock_path_exists):
            user_manager = UserManager()
            users = user_manager.list_users_with_ssh()

            assert sorted(users) == ["user1", "user2"]

    def test_validate_username_valid(self):
        """Test validation of valid usernames."""
        user_manager = UserManager()

        assert user_manager.validate_username("alice") is True
        assert user_manager.validate_username("user123") is True
        assert user_manager.validate_username("test-user") is True
        assert user_manager.validate_username("test_user") is True
        assert user_manager.validate_username("user.name") is True

    def test_validate_username_invalid(self):
        """Test validation of invalid usernames."""
        user_manager = UserManager()

        assert user_manager.validate_username("") is False
        assert user_manager.validate_username("-invalid") is False
        assert user_manager.validate_username("_invalid") is False
        assert user_manager.validate_username(".invalid") is False
        assert user_manager.validate_username("user@invalid") is False
        assert user_manager.validate_username("user space") is False
        assert user_manager.validate_username("a" * 33) is False  # Too long

    @patch("subprocess.run")
    @patch("pwd.getpwnam")
    def test_delete_user_success(self, mock_getpwnam, mock_subprocess):
        """Test successful user deletion."""
        # Mock user exists
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_getpwnam.return_value = mock_user
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = ""

        user_manager = UserManager()
        user_manager.delete_user("testuser")

        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert "userdel" in args
        assert "-r" in args
        assert "testuser" in args

    @patch("pwd.getpwnam")
    def test_delete_user_not_exists(self, mock_getpwnam):
        """Test deleting user that doesn't exist."""
        mock_getpwnam.side_effect = KeyError("User not found")

        user_manager = UserManager()
        # Should not raise exception
        user_manager.delete_user("nonexistent")

    @patch("subprocess.run")
    @patch("pwd.getpwnam")
    def test_delete_user_failure_with_ssh_fallback(
        self, mock_getpwnam, mock_subprocess
    ):
        """Test user deletion failure with SSH removal fallback."""
        # Mock user exists
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_dir = "/home/testuser"
        mock_getpwnam.return_value = mock_user

        # Mock userdel failure
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "userdel", stderr="User busy"
        )

        with patch.object(UserManager, "remove_ssh_access") as mock_remove_ssh:
            user_manager = UserManager()

            with pytest.raises(RuntimeError, match="Failed to delete user"):
                user_manager.delete_user("testuser")

            # Should attempt SSH removal as fallback
            mock_remove_ssh.assert_called_once_with("testuser")
