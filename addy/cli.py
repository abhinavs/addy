#!/usr/bin/env python3
"""
Main CLI interface for addy.

This started as a simple Click app but grew into something more substantial.
The CLI design tries to mimic package managers - hence install/remove commands.
"""

import sys
import os
import logging
from typing import Optional

import click

from .config import ConfigManager
from .git_ops import GitRepository
from .user_manager import UserManager
from .sudo_manager import SudoManager
from . import __version__


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def check_root() -> None:
    """Check if running as root."""
    if os.geteuid() != 0:
        click.echo("Error: This command must be run as root (use sudo)", err=True)
        sys.exit(1)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, verbose):
    """Addy - Git-Driven SSH Access Control"""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.group()
@click.pass_context
def config(ctx):
    """Manage addy configuration"""
    check_root()
    ctx.obj["config"] = ConfigManager()


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx, key: str, value: str):
    """Set a configuration value"""
    config_manager = ctx.obj["config"]
    config_manager.set(key, value)
    click.echo(f"Set {key}={value}")


@config.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx, key: str):
    """Get a configuration value"""
    config_manager = ctx.obj["config"]
    value = config_manager.get(key)
    if value is not None:
        click.echo(value)
    else:
        click.echo(f"Configuration key '{key}' not found", err=True)
        sys.exit(1)


@config.command("list")
@click.pass_context
def config_list(ctx):
    """List all configuration values"""
    config_manager = ctx.obj["config"]
    config_data = config_manager.list_all()
    if config_data:
        for key, value in config_data.items():
            click.echo(f"{key}={value}")
    else:
        click.echo("No configuration found")


@cli.command()
@click.argument("package")
@click.pass_context
def install(ctx, package: str):
    """Install a user or sudo package"""
    check_root()

    try:
        package_type, username = _parse_package(package)

        config_manager = ConfigManager()
        git_repo = GitRepository(config_manager)
        user_manager = UserManager()
        sudo_manager = SudoManager(user_manager)

        click.echo(f"Installing package: {package}")

        # Sync repository
        git_repo.sync()

        if package_type == "user":
            # Get public key
            public_key = git_repo.get_public_key(username)

            # Create user and install SSH key
            user_manager.create_user(username)
            user_manager.install_ssh_key(username, public_key)

        elif package_type == "sudo":
            # Grant sudo access (create user if needed)
            sudo_manager.grant_sudo(username, create_user=True)

        click.echo(f"Package {package} installed successfully")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("package")
@click.option(
    "--remove-user",
    is_flag=True,
    help="Also remove SSH access (for sudo packages only)",
)
@click.option(
    "--delete-account", is_flag=True, help="Also delete the user account completely"
)
@click.pass_context
def remove(ctx, package: str, remove_user: bool, delete_account: bool):
    """Remove a user or sudo package

    Examples:
      sudo addy remove user/alice                    # Remove SSH access only
      sudo addy remove user/alice --delete-account  # Remove SSH access + delete account
      sudo addy remove sudo/alice                    # Remove sudo only
      sudo addy remove sudo/alice --remove-user     # Remove sudo + SSH access
      sudo addy remove sudo/alice --delete-account  # Remove sudo + SSH + account
    """
    check_root()

    try:
        package_type, username = _parse_package(package)

        user_manager = UserManager()
        sudo_manager = SudoManager(user_manager)

        # Validate flags - remove_user only works with sudo packages
        if remove_user and package_type != "sudo":
            click.echo(
                "Error: --remove-user can only be used with sudo packages",
                err=True,
            )
            sys.exit(1)

        click.echo(f"Removing package: {package}")

        if package_type == "user":
            user_manager.remove_ssh_access(username)
            if delete_account:
                user_manager.delete_user(username)
        elif package_type == "sudo":
            sudo_manager.revoke_sudo(
                username,
                remove_ssh=remove_user or delete_account,
                delete_user=delete_account,
            )

        click.echo(f"Package {package} removed successfully")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def sync(ctx):
    """Sync with Git repository"""
    check_root()

    try:
        config_manager = ConfigManager()
        git_repo = GitRepository(config_manager)
        git_repo.sync()
        click.echo("Repository synced successfully")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """Show version information"""
    click.echo(f"addy {__version__}")


def _parse_package(package: str) -> tuple[str, str]:
    """Parse package string into type and username."""
    if "/" not in package:
        raise ValueError("Invalid package format. Use: user/username or sudo/username")

    parts = package.split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid package format. Use: user/username or sudo/username")

    package_type, username = parts

    if package_type not in ["user", "sudo"]:
        raise ValueError("Package type must be 'user' or 'sudo'")

    if (
        not username
        or not username.replace("-", "").replace("_", "").replace(".", "").isalnum()
    ):
        raise ValueError(f"Invalid username: {username}")

    return package_type, username


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
