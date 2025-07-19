# Changelog

All notable changes to addy will be documented in this file.

## [1.0.2] - 2025-07-19

### Changed
- **BREAKING IMPROVEMENT**: `sudo/username` packages now automatically create users if they don't exist
- SudoManager now accepts optional UserManager instance for user creation functionality
- CLI `install sudo/username` command no longer requires pre-existing users

### Added
- New `create_user` parameter in `SudoManager.grant_sudo()` method
- Comprehensive test coverage for sudo user creation scenarios
- Integration tests for end-to-end sudo installation workflows

### Fixed
- Eliminated requirement to install `user/username` before `sudo/username` packages
- Improved user experience by removing manual two-step process for sudo access

### Technical Details
- Enhanced SudoManager constructor to accept UserManager dependency injection
- Backward compatibility maintained - existing SudoManager usage continues to work
- Added proper error handling for user creation failures during sudo installation

## [1.0.1] - 2025-07-19

### Changed
- Updated install script to use PyPI package instead of source installation
- Simplified installation process for end users
- Removed unnecessary complexity from install.sh

### Fixed
- Install script now properly installs from published PyPI package

## [1.0.0] - 2025-07-19

### Added
- Initial release of addy
- Core user management with `install user/username` and `remove user/username`
- Sudo management with `install sudo/username` and `remove sudo/username`
- Git repository integration for SSH key storage
- Configuration management with YAML storage
- Comprehensive test suite with pytest
- CLI interface built with Click
- SSH key validation for multiple key types (RSA, Ed25519, ECDSA)
- Support for private Git repositories with SSH keys
- Idempotent operations (safe to run multiple times)

### Technical Details
- Python 3.8+ support
- Uses GitPython for Git operations
- File permissions handling (600/700 for security)
- Sudoers validation with visudo
- Virtual environment support for development

### Documentation
- Complete README with installation and usage examples
- Contributing guidelines
- MIT license
- Development setup instructions

---

*Future releases will follow [Semantic Versioning](https://semver.org/).*