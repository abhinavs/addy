# addy 🧑‍💻🔑 – Git-Driven SSH Access Control

**Simple user access management for Linux servers. Like `apt install` but for people.**

*Inspired by Yahoo's internal yinst package manager that made server user management effortless.*

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](#testing)

After years of manually copying SSH keys and editing sudoers files across servers, I built addy to treat user access like package management. Want to give Alice access? `addy install user/alice`. Need to grant sudo? `addy install sudo/alice`. Your Git repository becomes the single source of truth.

## ✨ Why I Built This

- **🎯 Package-like Simplicity**: Why should user management be harder than `apt install`?
- **🔒 Git-Powered Audit**: Every access change is version controlled and traceable
- **🚀 Zero Infrastructure**: No databases, no services - just Git and simple commands
- **📦 Familiar Workflow**: Your team already uses Git - now use it for access too
- **🔄 Production-Ready**: Idempotent by design, tested in real environments
- **🧪 Well-Tested**: 90%+ test coverage because security tools should be reliable

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install addy

# Or quick install script  
curl -fsSL https://raw.githubusercontent.com/abhinavs/addy/main/install.sh | bash

# Or install from source
git clone https://github.com/abhinavs/addy.git
cd addy
pip install -e .
```

### Setup Your Git Repository

Create a Git repository with your team's SSH keys:

```
your-addy-users-repo/
└── users/
    ├── alice.pub
    ├── bob.pub
    └── charlie.pub
```

Each `.pub` file contains a user's SSH public key.

### Configure Addy

```bash
# Set your Git repository (can be private)
sudo addy config set git-repo git@github.com:your-org/your-addy-users-repo.git

# For private repos, set up a deploy key
sudo addy config set ssh-key-path /etc/addy/deploy_key
```

### Grant Access

```bash
# Give SSH access
sudo addy install user/alice

# Grant sudo privileges
sudo addy install sudo/alice

# Remove access
sudo addy remove user/alice
sudo addy remove sudo/alice
```

## 🔧 How It Works

When you run `addy install user/alice`:

1. **Syncs** the latest Git repository
2. **Finds** `users/alice.pub` in the repo
3. **Creates** Linux user `alice` (if needed)
4. **Installs** SSH key to `~alice/.ssh/authorized_keys`
5. **Sets** proper permissions and ownership

When you run `addy install sudo/alice`:

1. **Checks** that user `alice` exists
2. **Creates** `/etc/sudoers.d/alice` with passwordless sudo
3. **Validates** the sudoers file for safety

## 📋 Features

### Core Functionality
- ✅ **User Management**: Create users and install SSH keys
- ✅ **Sudo Management**: Grant/revoke passwordless sudo access
- ✅ **Git Integration**: Pull keys from public or private repositories
- ✅ **SSH Key Validation**: Verify key format and security
- ✅ **Idempotent Operations**: Safe to run repeatedly

### Security Features
- 🔐 **SSH Key Authentication**: No password-based access
- 🛡️ **Sudoers Validation**: Uses `visudo` to prevent syntax errors
- 🔍 **Permission Management**: Proper file ownership and permissions
- 📝 **Audit Trail**: Git history shows who granted access when

### Developer Experience
- 🧪 **Comprehensive Testing**: Unit tests with mocking
- 📚 **Clear Documentation**: Examples and troubleshooting guides
- 🔧 **Easy Installation**: One-command setup
- 💻 **CLI Interface**: Intuitive command structure

## 📚 Usage Examples

### Basic Workflow

```bash
# Configure addy
sudo addy config set git-repo git@github.com:company/ssh-keys.git

# Grant SSH access to a new employee
sudo addy install user/john

# Give them sudo rights for deployments
sudo addy install sudo/john

# Remove access when they leave
sudo addy remove sudo/john
sudo addy remove user/john
```

### Advanced Configuration

```bash
# Use a specific branch
sudo addy config set git-branch production

# Set up private repository access
sudo addy config set ssh-key-path /etc/addy/readonly_deploy_key

# Manually sync repository
sudo addy sync

# View all configuration
sudo addy config list
```

### Automation & CI/CD

Addy integrates seamlessly with automation:

```bash
# In your deployment script
sudo addy install user/deployment-bot
sudo addy install sudo/deployment-bot

# In your offboarding script
sudo addy remove sudo/departing-employee
sudo addy remove user/departing-employee
```

## 🏗️ Git Repository Structure

Your Git repository should follow this structure:

```
your-addy-users-repo/
├── users/
│   ├── alice.pub      # Alice's SSH public key
│   ├── bob.pub        # Bob's SSH public key
│   └── charlie.pub    # Charlie's SSH public key
└── README.md          # Optional: document your access policies
```

### Supported Key Types
- `ssh-rsa` (RSA keys)
- `ssh-ed25519` (Ed25519 keys)
- `ecdsa-sha2-*` (ECDSA keys)

## ⚙️ Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `git-repo` | Git repository URL | *Required* |
| `git-branch` | Git branch to use | `main` |
| `ssh-key-path` | SSH private key for Git access | None |

## 🧪 Testing

Addy has a comprehensive test suite:

```bash
# Install development dependencies
pip3 install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=addy --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

## 🔒 Security Considerations

- **Private Repositories**: Use deploy keys with read-only access
- **SSH Key Management**: Rotate keys regularly, remove unused keys
- **Sudo Access**: Grant sparingly, audit regularly
- **Git History**: Provides complete audit trail of access changes
- **File Permissions**: Addy sets secure permissions automatically

## 🐛 Troubleshooting

### Common Issues

**Git clone/pull fails:**
```bash
# Check your repository URL
sudo addy config get git-repo

# Verify SSH key permissions (if using deploy key)
sudo ls -la /etc/addy/deploy_key
```

**User creation fails:**
```bash
# Check if user already exists
id username

# Verify sufficient permissions
sudo addy sync
```

**SSH key validation errors:**
```bash
# Test key format locally
ssh-keygen -l -f /path/to/key.pub

# Check repository structure
git clone your-addy-users-repo && ls -la users/
```

### Debug Mode

```bash
# Enable verbose logging
sudo addy --verbose sync
sudo addy --verbose install user/alice
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/abhinavs/addy.git
cd addy

# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
pip install -e .

# Run tests
pytest

# Code formatting
black addy/
flake8 addy/
```

**Note**: If you encounter "externally managed environment" errors, you must use a virtual environment as shown above. This is required on systems with Homebrew Python or similar package managers.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Documentation**: [GitHub Wiki](https://github.com/abhinavs/addy/wiki)
- **Issues**: [GitHub Issues](https://github.com/abhinavs/addy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/abhinavs/addy/discussions)

## 🗺️ Roadmap

- [ ] **Audit Logging**: Track all access grants/revocations
- [ ] **Web Dashboard**: View current access and audit logs
- [ ] **Key Expiration**: Automatic access revocation
- [ ] **SSH Certificates**: SSO-style authentication
- [ ] **Webhook Integration**: Automated access management

---

**Built with ❤️ by [@abhinavs](https://github.com/abhinavs) for system administrators who believe user management shouldn't be painful.**

*Inspired by the elegance of Yahoo's yinst package manager - because managing people should be as simple as managing packages.*