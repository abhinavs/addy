#!/bin/bash
set -euo pipefail

ADDY_VERSION="1.0.0"
INSTALL_DIR="/usr/local/bin"
PYTHON_MIN_VERSION="3.8"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

error() {
    log "ERROR: $*"
    exit 1
}

info() {
    log "INFO: $*"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This installation script must be run as root (use sudo)"
    fi
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local required_version=$(echo "$PYTHON_MIN_VERSION" | cut -d'.' -f1-2)
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= tuple(map(int, '$PYTHON_MIN_VERSION'.split('.'))) else 1)"; then
        error "Python $PYTHON_MIN_VERSION or higher is required (found $python_version)"
    fi
    
    info "Python version check passed: $python_version"
}

check_git() {
    if ! command -v git &> /dev/null; then
        error "Git is required but not installed"
    fi
    
    info "Git found: $(git --version)"
}

install_addy() {
    info "Installing addy from PyPI..."
    
    # Check if pip is available
    if ! python3 -m pip --version &> /dev/null; then
        error "pip is required but not available"
    fi
    
    # Install from PyPI
    info "Installing addy package..."
    if ! python3 -m pip install addy; then
        error "Failed to install addy from PyPI"
    fi
    
    # Verify installation
    if ! command -v addy &> /dev/null; then
        error "Installation failed - addy command not found in PATH"
    fi
    
    info "Installation successful!"
    addy version
}

show_post_install() {
    cat << 'EOF'

🎉 Addy is ready! Here's how to get started:

1. First, set up your Git repository with SSH keys:
   sudo addy config set git-repo git@github.com:your-org/ssh-keys.git

2. For private repos, add a deploy key:
   sudo addy config set ssh-key-path /etc/addy/deploy_key

3. Install your first user:
   sudo addy install user/alice

4. Grant sudo if needed:
   sudo addy install sudo/alice

That's it! Run `addy --help` for more commands.
Need help? Check https://github.com/abhinavs/addy
EOF
}

main() {
    info "Starting addy installation..."
    
    check_root
    check_python
    check_git
    install_addy
    show_post_install
    
    info "Installation complete!"
}

main "$@"