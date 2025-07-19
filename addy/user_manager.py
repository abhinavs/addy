"""
User management operations for addy.
"""

import os
import pwd
import grp
import subprocess
import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class UserManager:
    """Manages Linux user accounts and SSH keys."""

    def __init__(self):
        """Initialize user manager."""
        pass

    def user_exists(self, username: str) -> bool:
        """Check if a user exists.

        Args:
            username: Username to check

        Returns:
            True if user exists, False otherwise
        """
        try:
            pwd.getpwnam(username)
            return True
        except KeyError:
            return False

    def create_user(self, username: str, shell: str = "/bin/bash") -> None:
        """Create a new user account.

        Args:
            username: Username to create
            shell: Default shell for the user

        Raises:
            RuntimeError: If user creation fails
        """
        if self.user_exists(username):
            logger.info(f"User {username} already exists")
            return

        logger.info(f"Creating user: {username}")

        try:
            # Create user with home directory
            cmd = [
                "useradd",
                "-m",  # Create home directory
                "-s",
                shell,  # Set shell
                username,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"useradd output: {result.stdout}")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create user {username}: {e.stderr}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error creating user {username}: {e}")

        # Create .ssh directory with proper permissions
        try:
            self._setup_ssh_directory(username)
            logger.info(f"User {username} created successfully")
        except Exception as e:
            # Try to clean up the user if SSH setup fails
            try:
                subprocess.run(["userdel", "-r", username], capture_output=True)
            except:
                pass
            raise RuntimeError(f"Failed to setup SSH directory for {username}: {e}")

    def _setup_ssh_directory(self, username: str) -> None:
        """Setup .ssh directory for a user.

        Args:
            username: Username to setup SSH directory for
        """
        try:
            user_info = pwd.getpwnam(username)
            home_dir = Path(user_info.pw_dir)
            ssh_dir = home_dir / ".ssh"

            # Create .ssh directory
            ssh_dir.mkdir(mode=0o700, exist_ok=True)

            # Set ownership
            os.chown(ssh_dir, user_info.pw_uid, user_info.pw_gid)

            logger.debug(f"SSH directory setup for {username}: {ssh_dir}")

        except KeyError:
            raise RuntimeError(f"User {username} not found")
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to setup SSH directory: {e}")

    def install_ssh_key(self, username: str, public_key: str) -> None:
        """Install SSH public key for a user.

        This was more complex than expected - had to handle cases where
        users already have authorized_keys files with existing keys.

        Args:
            username: Username to install key for
            public_key: SSH public key content

        Raises:
            RuntimeError: If key installation fails
        """
        if not self.user_exists(username):
            raise RuntimeError(f"User {username} does not exist")

        try:
            user_info = pwd.getpwnam(username)
            home_dir = Path(user_info.pw_dir)
            ssh_dir = home_dir / ".ssh"
            authorized_keys = ssh_dir / "authorized_keys"

            # Ensure SSH directory exists
            self._setup_ssh_directory(username)

            # Check if key already exists
            if authorized_keys.exists():
                with open(authorized_keys, "r") as f:
                    existing_keys = f.read()
                if public_key.strip() in existing_keys:
                    logger.info(f"SSH key already installed for user {username}")
                    return

            # Add the public key
            logger.info(f"Installing SSH key for user: {username}")
            with open(authorized_keys, "a") as f:
                f.write(f"{public_key.strip()}\n")

            # Set proper permissions
            os.chmod(authorized_keys, 0o600)
            os.chown(authorized_keys, user_info.pw_uid, user_info.pw_gid)

            logger.info(f"SSH key installed successfully for user {username}")

        except KeyError:
            raise RuntimeError(f"User {username} not found")
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to install SSH key for {username}: {e}")

    def remove_ssh_access(self, username: str) -> None:
        """Remove SSH access for a user by deleting authorized_keys.

        Args:
            username: Username to remove SSH access for
        """
        if not self.user_exists(username):
            logger.warning(f"User {username} does not exist")
            return

        try:
            user_info = pwd.getpwnam(username)
            home_dir = Path(user_info.pw_dir)
            authorized_keys = home_dir / ".ssh" / "authorized_keys"

            if not authorized_keys.exists():
                logger.info(f"No SSH keys found for user {username}")
                return

            logger.info(f"Removing SSH access for user: {username}")
            authorized_keys.unlink()

            logger.info(f"SSH access removed for user {username}")

        except KeyError:
            logger.warning(f"User {username} not found")
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to remove SSH access for {username}: {e}")

    def get_user_info(self, username: str) -> Optional[dict]:
        """Get information about a user.

        Args:
            username: Username to get info for

        Returns:
            Dictionary with user information or None if user doesn't exist
        """
        try:
            user_info = pwd.getpwnam(username)
            home_dir = Path(user_info.pw_dir)
            authorized_keys = home_dir / ".ssh" / "authorized_keys"

            # Count SSH keys
            key_count = 0
            if authorized_keys.exists():
                with open(authorized_keys, "r") as f:
                    key_count = len(
                        [
                            line
                            for line in f
                            if line.strip() and not line.startswith("#")
                        ]
                    )

            return {
                "username": username,
                "uid": user_info.pw_uid,
                "gid": user_info.pw_gid,
                "home_dir": str(home_dir),
                "shell": user_info.pw_shell,
                "ssh_key_count": key_count,
                "has_ssh_access": authorized_keys.exists(),
            }

        except KeyError:
            return None
        except Exception as e:
            logger.warning(f"Failed to get user info for {username}: {e}")
            return None

    def list_users_with_ssh(self) -> list[str]:
        """List all users that have SSH access (authorized_keys file).

        Returns:
            List of usernames with SSH access
        """
        users_with_ssh = []

        try:
            # Get all users from /etc/passwd
            for user_info in pwd.getpwall():
                if user_info.pw_uid < 1000:  # Skip system users
                    continue

                home_dir = Path(user_info.pw_dir)
                authorized_keys = home_dir / ".ssh" / "authorized_keys"

                if authorized_keys.exists():
                    users_with_ssh.append(user_info.pw_name)

        except Exception as e:
            logger.warning(f"Failed to list users with SSH access: {e}")

        return sorted(users_with_ssh)

    def validate_username(self, username: str) -> bool:
        """Validate username format.

        Args:
            username: Username to validate

        Returns:
            True if valid, False otherwise
        """
        if not username:
            return False

        # Basic validation - alphanumeric, dots, dashes, underscores
        if not username.replace("-", "").replace("_", "").replace(".", "").isalnum():
            return False

        # Must start with letter or number
        if not username[0].isalnum():
            return False

        # Length check
        if len(username) > 32:
            return False

        return True
