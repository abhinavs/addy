# Contributing to Addy

Thank you for your interest in contributing to Addy! We welcome contributions from everyone.

## 🚀 Quick Start

### Development Setup

```bash
# Clone the repository
git clone https://github.com/abhinavs/addy.git
cd addy

# Install development dependencies
pip3 install -r requirements-dev.txt

# Install in development mode
pip3 install -e .

# Verify installation
addy version
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=addy --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run specific test file
pytest tests/test_config.py -v
```

### Code Quality

We maintain high code quality standards:

```bash
# Format code (required before committing)
black addy/ tests/

# Check linting
flake8 addy/ tests/

# Type checking
mypy addy/

# Run all quality checks
black addy/ tests/ && flake8 addy/ tests/ && mypy addy/
```

## 📋 How to Contribute

### 1. Find an Issue

- Check our [Issues](https://github.com/abhinavs/addy/issues) page
- Look for issues labeled `good first issue` or `help wanted`
- Or propose a new feature by opening an issue first

### 2. Fork and Branch

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/your-username/addy.git
cd addy

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 3. Make Changes

- **Follow existing code style** - we use Black for formatting
- **Write tests** - all new code should have corresponding tests
- **Update documentation** - update README.md, docstrings, etc. as needed
- **Keep commits focused** - one logical change per commit

### 4. Test Your Changes

```bash
# Run the full test suite
pytest

# Test specific functionality
pytest tests/test_your_module.py

# Check code coverage
pytest --cov=addy --cov-report=term-missing

# Test CLI manually
sudo addy --help
sudo addy config list
```

### 5. Submit a Pull Request

```bash
# Push your changes
git push origin feature/your-feature-name

# Create a pull request on GitHub
```

## 🧪 Testing Guidelines

### Test Structure

- **Unit tests**: Test individual functions/methods in isolation
- **Integration tests**: Test component interactions
- **CLI tests**: Test command-line interface behavior

### Writing Tests

```python
def test_function_behavior(self):
    """Test that function does what it should."""
    # Arrange
    input_data = "test"
    expected = "expected_result"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected
```

### Mocking Guidelines

- Mock external dependencies (file system, network, subprocess)
- Use `pytest-mock` for mocking
- Test both success and failure scenarios

```python
@patch('subprocess.run')
def test_user_creation(mock_subprocess):
    mock_subprocess.return_value.returncode = 0
    # Test user creation logic
```

## 📝 Code Style Guide

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use type hints where appropriate
- Write descriptive docstrings

### Naming Conventions

- **Functions/methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Configuration keys**: `kebab-case` (e.g., `git-repo`, `ssh-key-path`)

### Error Handling

```python
def risky_operation():
    try:
        # operation that might fail
        pass
    except SpecificException as e:
        logger.error(f"Operation failed: {e}")
        raise RuntimeError(f"Failed to perform operation: {e}")
```

## 🔒 Security Guidelines

When contributing to Addy:

- **Never log sensitive data** (SSH keys, passwords, tokens)
- **Validate all inputs** before processing
- **Use secure file permissions** (600 for files, 700 for directories)
- **Sanitize user input** to prevent injection attacks
- **Test security scenarios** (invalid keys, malicious input)

## 📚 Documentation

### Code Documentation

- Write clear docstrings for all public functions/classes
- Include type hints
- Document parameters and return values

```python
def install_ssh_key(self, username: str, public_key: str) -> None:
    """Install SSH public key for a user.
    
    Args:
        username: Username to install key for
        public_key: SSH public key content
        
    Raises:
        RuntimeError: If key installation fails
    """
```

### User Documentation

- Update README.md for new features
- Add examples for new CLI commands
- Update configuration documentation

## 🐛 Reporting Issues

### Bug Reports

Include:
- Addy version (`addy version`)
- Operating system and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Impact on existing functionality

## 📋 Development Workflow

### Commit Message Format

```
type(scope): description

- feat: add new feature
- fix: bug fix
- docs: documentation changes
- test: add or update tests
- refactor: code refactoring
- style: formatting changes
```

Examples:
```
feat(cli): add user listing command
fix(config): handle missing configuration file
docs(readme): update installation instructions
test(user): add tests for user creation
```

### Pull Request Guidelines

- **Clear title**: Describe what the PR does
- **Detailed description**: Explain the problem and solution
- **Link to issues**: Reference related GitHub issues
- **Test coverage**: Ensure new code is tested
- **Documentation**: Update docs if needed

### Review Process

1. **Automated checks**: Tests and linting must pass
2. **Code review**: At least one maintainer review required
3. **Manual testing**: Test new features manually
4. **Documentation**: Verify docs are updated

## 🤝 Code of Conduct

### Our Standards

- **Be respectful** and inclusive
- **Be constructive** in feedback
- **Be patient** with new contributors
- **Be collaborative** and helpful

### Reporting Issues

If you experience inappropriate behavior, please contact the maintainers.

## ❓ Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check README.md and code comments

## 🎯 Areas for Contribution

### Easy Contributions

- Documentation improvements
- Test coverage improvements
- Bug fixes
- Code formatting and linting fixes

### Medium Contributions

- New CLI commands
- Configuration enhancements
- Error handling improvements
- Performance optimizations

### Advanced Contributions

- Security enhancements
- New authentication methods
- Integration with other tools
- Architecture improvements

## 📝 License

By contributing to Addy, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Addy! 🎉