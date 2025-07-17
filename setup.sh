#!/bin/bash

# FleetFuel360 Quick Start Script
# This script automates the setup process for the FleetFuel360 application

set -e  # Exit on any error

echo "🚀 FleetFuel360 Quick Start Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    print_status "Python version: $python_version"
}

# Check if pip is installed
check_pip() {
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip."
        exit 1
    fi
    
    print_status "pip3 is available"
}

# Check if MySQL is installed and running
check_mysql() {
    if ! command -v mysql &> /dev/null; then
        print_warning "MySQL client not found. Please install MySQL 8.0 or higher."
        echo "Installation instructions:"
        echo "  Ubuntu/Debian: sudo apt-get install mysql-server mysql-client"
        echo "  CentOS/RHEL: sudo yum install mysql-server mysql"
        echo "  macOS: brew install mysql"
        echo ""
        read -p "Continue without MySQL check? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_status "MySQL client is available"
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Skipping creation."
    else
        python3 -m venv venv
        print_status "Virtual environment created successfully"
    fi
}

# Activate virtual environment and install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_status "Dependencies installed successfully"
}

# Configure database credentials
configure_database() {
    print_status "Configuring database credentials..."
    
    # Check if .env file exists
    if [ -f ".env" ]; then
        print_warning ".env file already exists. Skipping database configuration."
        return
    fi
    
    # Copy example file
    cp .env.example .env
    
    echo ""
    echo "Please configure your MySQL database settings:"
    echo "The default configuration uses:"
    echo "  Host: localhost"
    echo "  User: root"
    echo "  Database: fleetfuel360"
    echo ""
    
    read -p "MySQL root password: " -s mysql_password
    echo ""
    
    # Update .env file with user input
    sed -i.bak "s/your_mysql_password_here/$mysql_password/g" .env
    rm .env.bak
    
    print_status "Database configuration saved to .env file"
}

# Update app.py with database credentials
update_app_config() {
    print_status "Updating application configuration..."
    
    if [ -f ".env" ]; then
        # Read password from .env file
        mysql_password=$(grep "DB_PASSWORD=" .env | cut -d'=' -f2)
        
        # Update app.py with the password
        sed -i.bak "s/'password': 'password'/'password': '$mysql_password'/g" app.py
        sed -i.bak "s/'password': 'password'/'password': '$mysql_password'/g" init_db.py
        rm -f app.py.bak init_db.py.bak
        
        print_status "Application configuration updated"
    else
        print_warning "No .env file found. Please update DB_CONFIG in app.py and init_db.py manually."
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run database initialization
    python init_db.py
    
    if [ $? -eq 0 ]; then
        print_status "Database initialized successfully"
    else
        print_error "Database initialization failed. Please check your MySQL configuration."
        exit 1
    fi
}

# Test the application
test_app() {
    print_status "Testing application..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run unit tests
    python test_unit.py
    
    if [ $? -eq 0 ]; then
        print_status "Application tests passed"
    else
        print_warning "Some tests failed. The application may still work, but please check the output."
    fi
}

# Main setup process
main() {
    print_status "Starting FleetFuel360 setup..."
    
    # Check prerequisites
    check_python
    check_pip
    check_mysql
    
    # Setup process
    create_venv
    install_dependencies
    configure_database
    update_app_config
    init_database
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo "================================"
    echo ""
    echo "To start the application:"
    echo "  1. Activate the virtual environment: source venv/bin/activate"
    echo "  2. Start the server: python app.py"
    echo "  3. Test the API: python test_api.py"
    echo ""
    echo "The API will be available at: http://localhost:5000"
    echo "API documentation is in README.md"
    echo ""
    echo "Optional: Run unit tests with: python test_unit.py"
    echo "Optional: Try examples with: python examples.py"
    echo ""
    
    # Ask if user wants to start the application
    read -p "Start the application now? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Starting FleetFuel360 application..."
        source venv/bin/activate
        python app.py
    fi
}

# Run main function
main "$@"
