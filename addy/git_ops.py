"""
Git repository operations for addy.

GitPython made this much cleaner than subprocess calls to git.
SSH key validation was tricky - had to handle multiple key formats
and edge cases I discovered during testing.
"""

import os
import logging
from pathlib import Path
from typing import Optional

import git
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519, ec

from .config import ConfigManager


logger = logging.getLogger(__name__)


class GitRepository:
    """Manages Git repository operations for user keys."""
    
    DEFAULT_REPO_DIR = "/var/lib/addy/repo"
    
    def __init__(self, config_manager: ConfigManager, repo_dir: Optional[str] = None):
        """Initialize Git repository manager.
        
        Args:
            config_manager: Configuration manager instance
            repo_dir: Directory to store Git repository
        """
        self.config = config_manager
        self.repo_dir = Path(repo_dir or self.DEFAULT_REPO_DIR)
        self._repo: Optional[git.Repo] = None
        
        self._ensure_repo_dir()
    
    def _ensure_repo_dir(self) -> None:
        """Ensure repository directory exists with proper permissions."""
        try:
            self.repo_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            logger.debug(f"Repository directory: {self.repo_dir}")
        except PermissionError:
            raise RuntimeError(f"Permission denied creating repo directory: {self.repo_dir}")
    
    def _get_git_env(self) -> dict[str, str]:
        """Get environment variables for Git operations."""
        env = os.environ.copy()
        
        ssh_key_path = self.config.get_ssh_key_path()
        if ssh_key_path:
            # Use custom SSH key for Git operations
            ssh_cmd = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"
            env['GIT_SSH_COMMAND'] = ssh_cmd
            logger.debug(f"Using SSH key: {ssh_key_path}")
        
        return env
    
    def sync(self) -> None:
        """Sync repository with remote."""
        git_repo_url = self.config.get_git_repo()
        git_branch = self.config.get_git_branch()
        
        logger.info(f"Syncing repository: {git_repo_url} (branch: {git_branch})")
        
        env = self._get_git_env()
        
        try:
            if (self.repo_dir / '.git').exists():
                # Repository exists, pull latest changes
                self._repo = git.Repo(self.repo_dir)
                
                # Ensure we're on the correct branch
                if self._repo.active_branch.name != git_branch:
                    try:
                        self._repo.git.checkout(git_branch, env=env)
                    except git.GitCommandError:
                        # Branch might not exist locally, create it
                        self._repo.git.checkout('-b', git_branch, f'origin/{git_branch}', env=env)
                
                # Pull latest changes
                origin = self._repo.remote('origin')
                origin.fetch(env=env)
                self._repo.git.reset('--hard', f'origin/{git_branch}', env=env)
                
                logger.info("Repository updated successfully")
            else:
                # Clone repository
                self._repo = git.Repo.clone_from(
                    git_repo_url,
                    self.repo_dir,
                    branch=git_branch,
                    env=env
                )
                logger.info("Repository cloned successfully")
                
        except git.GitCommandError as e:
            raise RuntimeError(f"Failed to sync Git repository: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error syncing repository: {e}")
    
    def get_public_key(self, username: str) -> str:
        """Get public key for a user from the repository.
        
        Args:
            username: Username to get public key for
            
        Returns:
            SSH public key content
            
        Raises:
            RuntimeError: If key file not found or invalid
        """
        key_file = self.repo_dir / 'users' / f'{username}.pub'
        
        if not key_file.exists():
            raise RuntimeError(f"Public key not found: users/{username}.pub")
        
        try:
            with open(key_file, 'r') as f:
                key_content = f.read().strip()
        except (IOError, PermissionError) as e:
            raise RuntimeError(f"Failed to read public key file: {e}")
        
        if not key_content:
            raise RuntimeError(f"Empty public key file: users/{username}.pub")
        
        # Validate SSH public key format
        if not self._validate_ssh_public_key(key_content):
            raise RuntimeError(f"Invalid SSH public key in users/{username}.pub")
        
        logger.info(f"Retrieved public key for user: {username}")
        return key_content
    
    def _validate_ssh_public_key(self, key_content: str) -> bool:
        """Validate SSH public key format.
        
        Args:
            key_content: SSH public key content
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic format check
            parts = key_content.strip().split()
            if len(parts) < 2:
                return False
            
            key_type = parts[0]
            key_data = parts[1]
            
            # Check key type
            valid_types = [
                'ssh-rsa',
                'ssh-ed25519',
                'ecdsa-sha2-nistp256',
                'ecdsa-sha2-nistp384',
                'ecdsa-sha2-nistp521',
                'ssh-dss'
            ]
            
            if key_type not in valid_types:
                logger.warning(f"Unsupported key type: {key_type}")
                return False
            
            # Try to decode base64 data
            import base64
            try:
                base64.b64decode(key_data)
            except Exception:
                logger.warning("Invalid base64 encoding in public key")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Public key validation failed: {e}")
            return False
    
    def list_users(self) -> list[str]:
        """List all users with public keys in the repository.
        
        Returns:
            List of usernames
        """
        users_dir = self.repo_dir / 'users'
        if not users_dir.exists():
            return []
        
        users = []
        for key_file in users_dir.glob('*.pub'):
            username = key_file.stem
            users.append(username)
        
        return sorted(users)
    
    def get_repo_info(self) -> dict[str, str]:
        """Get repository information.
        
        Returns:
            Dictionary with repository information
        """
        if not self._repo:
            return {}
        
        try:
            return {
                'url': self.config.get_git_repo(),
                'branch': self.config.get_git_branch(),
                'last_commit': self._repo.head.commit.hexsha[:8],
                'last_commit_date': self._repo.head.commit.committed_datetime.isoformat(),
                'last_commit_message': self._repo.head.commit.message.strip()
            }
        except Exception as e:
            logger.warning(f"Failed to get repo info: {e}")
            return {}