#!/usr/bin/env python3
"""
Simple integration test to verify sudo user creation functionality.
"""

from unittest.mock import Mock, patch
from addy.sudo_manager import SudoManager
from addy.user_manager import UserManager


def test_sudo_with_user_creation():
    """Test that we can install sudo for a non-existent user."""

    # Create real instances
    user_manager = UserManager()
    sudo_manager = SudoManager(user_manager)

    # Mock the user_manager methods
    with patch.object(user_manager, "user_exists", return_value=False), patch.object(
        user_manager, "create_user"
    ) as mock_create, patch("subprocess.run") as mock_subprocess, patch(
        "pathlib.Path.exists", return_value=False
    ), patch(
        "pathlib.Path.rename"
    ), patch(
        "builtins.open"
    ), patch(
        "os.chmod"
    ):

        # Mock visudo validation to pass
        mock_subprocess.return_value.returncode = 0

        # This should work without error - user should be created first
        sudo_manager.grant_sudo("newuser", create_user=True)

        # Verify user creation was called
        mock_create.assert_called_once_with("newuser")

        print("✓ Test passed: sudo installation with user creation works")


def test_sudo_without_user_creation():
    """Test that we get an error when trying to install sudo for non-existent user without create_user=True."""

    # Create real instances
    user_manager = UserManager()
    sudo_manager = SudoManager(user_manager)

    # Mock the user_manager methods
    with patch.object(user_manager, "user_exists", return_value=False), patch.object(
        user_manager, "create_user"
    ) as mock_create:

        # This should raise an error
        try:
            sudo_manager.grant_sudo("newuser", create_user=False)
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "does not exist" in str(e)

        # Verify user creation was NOT called
        mock_create.assert_not_called()

        print("✓ Test passed: sudo installation without user creation fails correctly")


if __name__ == "__main__":
    test_sudo_with_user_creation()
    test_sudo_without_user_creation()
    print("✓ All integration tests passed!")
