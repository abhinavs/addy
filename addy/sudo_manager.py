"""
Sudo access management for addy.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, List


logger = logging.getLogger(__name__)


class SudoManager:
    """Manages sudo access for users."""

    SUDOERS_DIR = Path("/etc/sudoers.d")

    def __init__(self):
        """Initialize sudo manager."""
        pass

    def grant_sudo(self, username: str) -> None:
        """Grant passwordless sudo access to a user.

        Args:
            username: Username to grant sudo access

        Raises:
            RuntimeError: If sudo grant fails
        """
        sudoers_file = self.SUDOERS_DIR / username

        if sudoers_file.exists():
            logger.info(f"Sudo access already configured for user {username}")
            return

        logger.info(f"Granting sudo access to user: {username}")

        try:
            # Create sudoers rule
            sudo_rule = f"{username} ALL=(ALL) NOPASSWD:ALL\n"

            # Write to temporary file first
            temp_file = sudoers_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                f.write(sudo_rule)

            # Set proper permissions
            os.chmod(temp_file, 0o440)

            # Validate the sudoers file
            if not self._validate_sudoers_file(temp_file):
                temp_file.unlink()
                raise RuntimeError(f"Invalid sudoers configuration for {username}")

            # Move to final location
            temp_file.rename(sudoers_file)

            logger.info(f"Sudo access granted to user {username}")

        except (OSError, PermissionError) as e:
            # Clean up temporary file if it exists
            temp_file = self.SUDOERS_DIR / f"{username}.tmp"
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            raise RuntimeError(f"Failed to grant sudo access to {username}: {e}")

    def revoke_sudo(self, username: str) -> None:
        """Revoke sudo access from a user.

        Args:
            username: Username to revoke sudo access from
        """
        sudoers_file = self.SUDOERS_DIR / username

        if not sudoers_file.exists():
            logger.info(f"No sudo access configured for user {username}")
            return

        logger.info(f"Removing sudo access for user: {username}")

        try:
            sudoers_file.unlink()
            logger.info(f"Sudo access removed for user {username}")

        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to remove sudo access for {username}: {e}")

    def has_sudo_access(self, username: str) -> bool:
        """Check if a user has sudo access.

        Args:
            username: Username to check

        Returns:
            True if user has sudo access, False otherwise
        """
        sudoers_file = self.SUDOERS_DIR / username
        return sudoers_file.exists()

    def list_sudo_users(self) -> List[str]:
        """List all users with sudo access managed by addy.

        Returns:
            List of usernames with sudo access
        """
        if not self.SUDOERS_DIR.exists():
            return []

        sudo_users = []
        for sudoers_file in self.SUDOERS_DIR.iterdir():
            if sudoers_file.is_file() and not sudoers_file.name.startswith("."):
                # Basic check to see if this looks like an addy-managed file
                if self._is_addy_sudoers_file(sudoers_file):
                    sudo_users.append(sudoers_file.name)

        return sorted(sudo_users)

    def _validate_sudoers_file(self, file_path: Path) -> bool:
        """Validate a sudoers file using visudo.

        This is critical - invalid sudoers files can lock you out of sudo.
        Learned this the hard way during early testing!

        Args:
            file_path: Path to sudoers file to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            result = subprocess.run(
                ["visudo", "-c", "-f", str(file_path)], capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.debug(f"Sudoers file validation passed: {file_path}")
                return True
            else:
                logger.error(f"Sudoers file validation failed: {result.stderr}")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to validate sudoers file: {e}")
            return False
        except FileNotFoundError:
            logger.warning("visudo command not found, skipping validation")
            return True  # Assume valid if visudo not available

    def _is_addy_sudoers_file(self, file_path: Path) -> bool:
        """Check if a sudoers file was created by addy.

        Args:
            file_path: Path to sudoers file

        Returns:
            True if this looks like an addy-managed file
        """
        try:
            with open(file_path, "r") as f:
                content = f.read().strip()

            # Check if it matches our expected format
            username = file_path.name
            expected_rule = f"{username} ALL=(ALL) NOPASSWD:ALL"

            return content == expected_rule

        except (OSError, PermissionError):
            return False

    def get_sudo_info(self, username: str) -> Optional[dict]:
        """Get sudo information for a user.

        Args:
            username: Username to get sudo info for

        Returns:
            Dictionary with sudo information or None
        """
        sudoers_file = self.SUDOERS_DIR / username

        if not sudoers_file.exists():
            return None

        try:
            stat_info = sudoers_file.stat()

            with open(sudoers_file, "r") as f:
                content = f.read().strip()

            return {
                "username": username,
                "sudoers_file": str(sudoers_file),
                "permissions": oct(stat_info.st_mode)[-3:],
                "content": content,
                "is_addy_managed": self._is_addy_sudoers_file(sudoers_file),
            }

        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to get sudo info for {username}: {e}")
            return None

    def verify_sudoers_integrity(self) -> dict:
        """Verify integrity of all addy-managed sudoers files.

        Returns:
            Dictionary with validation results
        """
        results = {"valid_files": [], "invalid_files": [], "errors": []}

        try:
            if not self.SUDOERS_DIR.exists():
                results["errors"].append("Sudoers directory does not exist")
                return results

            for sudoers_file in self.SUDOERS_DIR.iterdir():
                if sudoers_file.is_file() and self._is_addy_sudoers_file(sudoers_file):
                    if self._validate_sudoers_file(sudoers_file):
                        results["valid_files"].append(sudoers_file.name)
                    else:
                        results["invalid_files"].append(sudoers_file.name)

        except Exception as e:
            results["errors"].append(f"Failed to verify sudoers integrity: {e}")

        return results
