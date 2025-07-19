#!/usr/bin/env python3
"""
Smoke test to verify basic functionality works on the current platform.
This simulates what CI would do.
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and check its result."""
    print(f"Running: {description}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ FAILED: {description}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    else:
        print(f"✅ PASSED: {description}")
        return True


def main():
    """Run smoke tests."""
    print("🧪 Running Addy Smoke Tests")
    print("=" * 50)

    # Test import
    try:
        import addy

        print(f"✅ Import successful - version {addy.__version__}")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        sys.exit(1)

    # Test CLI import
    try:
        from addy.cli import cli

        print("✅ CLI import successful")
    except ImportError as e:
        print(f"❌ CLI import failed: {e}")
        sys.exit(1)

    # Test basic CLI command
    if run_command("python -m addy.cli --help", "CLI help command"):
        print("✅ CLI help works")
    else:
        print("❌ CLI help failed")
        sys.exit(1)

    # Test version command
    if run_command("python -m addy.cli version", "Version command"):
        print("✅ Version command works")
    else:
        print("❌ Version command failed")
        sys.exit(1)

    print("\n🎉 All smoke tests passed!")
    print("Ready for CI/CD deployment!")


if __name__ == "__main__":
    main()
