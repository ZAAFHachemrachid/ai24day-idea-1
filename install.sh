#!/bin/bash

# Exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Found Python version: $PYTHON_VERSION"
}

# Set up virtual environment
setup_venv() {
    log_info "Creating virtual environment..."
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    log_info "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    log_success "Virtual environment created and activated"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    pip install -r requirements.txt
    pip install -e .
    log_success "Dependencies installed successfully"
}

# Initialize database and required directories
initialize_project() {
    log_info "Initializing project..."
    
    # Create required directories if they don't exist
    directories=("data" "face_data" "faces" "logs")
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
    
    # Initialize database
    if [ -f "src/database/init_database.py" ]; then
        log_info "Initializing database..."
        python3 -m src.database.init_database
    fi
    
    log_success "Project initialized successfully"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check if main script exists
    if [ ! -f "src/main.py" ]; then
        log_error "Main script not found: src/main.py"
        exit 1
    fi
    
    # Try to run the application in test mode (if supported)
    # python3 src/main.py --test
    
    log_success "Installation verified successfully"
}

# Main installation process
main() {
    log_info "Starting setup..."
    
    check_python
    setup_venv
    install_dependencies
    initialize_project
    verify_installation
    
    log_success "Setup completed successfully!"
    log_info "To run the application:"
    echo -e "${BLUE}1. Activate the virtual environment:${NC} source venv/bin/activate"
    echo -e "${BLUE}2. Run the application:${NC} python3 src/main.py"
}

# Handle errors
trap 'log_error "An error occurred during installation. Please check the error message above."' ERR

# Run main installation
main