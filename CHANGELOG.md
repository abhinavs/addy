# Changelog

All notable changes to addy will be documented in this file.

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