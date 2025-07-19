#!/usr/bin/env python3
"""
Integration test to demonstrate the new sudo removal options.
"""

from unittest.mock import Mock, patch
from addy.sudo_manager import SudoManager
from addy.user_manager import UserManager


def test_remove_sudo_only():
    """Test basic sudo removal (original behavior)."""
    user_manager = UserManager()
    sudo_manager = SudoManager(user_manager)

    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.unlink"
    ) as mock_unlink, patch.object(
        user_manager, "remove_ssh_access"
    ) as mock_remove_ssh, patch.object(
        user_manager, "delete_user"
    ) as mock_delete:

        # Remove sudo only (default behavior)
        sudo_manager.revoke_sudo("alice")

        # Verify only sudo was removed
        mock_unlink.assert_called_once()
        mock_remove_ssh.assert_not_called()
        mock_delete.assert_not_called()

        print("✓ Remove sudo only: Works")


def test_remove_sudo_and_ssh():
    """Test sudo removal with SSH access removal."""
    user_manager = UserManager()
    sudo_manager = SudoManager(user_manager)

    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.unlink"
    ) as mock_unlink, patch.object(
        user_manager, "remove_ssh_access"
    ) as mock_remove_ssh, patch.object(
        user_manager, "delete_user"
    ) as mock_delete:

        # Remove sudo + SSH
        sudo_manager.revoke_sudo("alice", remove_ssh=True)

        # Verify sudo and SSH were removed
        mock_unlink.assert_called_once()
        mock_remove_ssh.assert_called_once_with("alice")
        mock_delete.assert_not_called()

        print("✓ Remove sudo + SSH: Works")


def test_remove_sudo_and_delete_user():
    """Test sudo removal with complete user deletion."""
    user_manager = UserManager()
    sudo_manager = SudoManager(user_manager)

    with patch("pathlib.Path.exists", return_value=True), patch(
        "pathlib.Path.unlink"
    ) as mock_unlink, patch.object(
        user_manager, "remove_ssh_access"
    ) as mock_remove_ssh, patch.object(
        user_manager, "delete_user"
    ) as mock_delete:

        # Remove sudo + SSH + delete user
        sudo_manager.revoke_sudo("alice", delete_user=True)

        # Verify everything was removed
        mock_unlink.assert_called_once()
        mock_remove_ssh.assert_called_once_with("alice")
        mock_delete.assert_called_once_with("alice")

        print("✓ Remove sudo + SSH + delete user: Works")


def test_remove_user_only():
    """Test basic user removal (SSH access only)."""
    user_manager = UserManager()

    with patch.object(
        user_manager, "remove_ssh_access"
    ) as mock_remove_ssh, patch.object(user_manager, "delete_user") as mock_delete:

        # Remove SSH only (default behavior for user packages)
        user_manager.remove_ssh_access("alice")

        # Verify only SSH was removed
        mock_remove_ssh.assert_called_once_with("alice")
        mock_delete.assert_not_called()

        print("✓ Remove user (SSH only): Works")


def test_remove_user_with_delete():
    """Test user removal with complete account deletion."""
    user_manager = UserManager()

    with patch.object(
        user_manager, "remove_ssh_access"
    ) as mock_remove_ssh, patch.object(user_manager, "delete_user") as mock_delete:

        # Remove SSH + delete user
        user_manager.remove_ssh_access("alice")
        user_manager.delete_user("alice")

        # Verify both operations
        mock_remove_ssh.assert_called_once_with("alice")
        mock_delete.assert_called_once_with("alice")

        print("✓ Remove user + delete account: Works")


if __name__ == "__main__":
    print("Testing sudo removal options:")
    test_remove_sudo_only()
    test_remove_sudo_and_ssh()
    test_remove_sudo_and_delete_user()

    print("\nTesting user removal options:")
    test_remove_user_only()
    test_remove_user_with_delete()

    print("\n🎉 All removal options work correctly!")
