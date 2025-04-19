# Installation Instructions

## Prerequisites
- Python 3
- Git
- Internet connection

## Installation Steps

1. Make the installation script executable:
```bash
chmod +x install.sh
```

2. Run the installation script:
```bash
./install.sh
```

The script will:
- Clone the repository
- Set up a Python virtual environment
- Install all required dependencies
- Initialize the database and required directories
- Verify the installation

## After Installation

To run the application:

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

2. Run the application:
```bash
python3 src/main.py
```

## Troubleshooting

If you encounter any issues during installation:

1. Make sure you have Python 3 and Git installed
2. Check your internet connection
3. Ensure you have write permissions in the installation directory
4. If the script fails, check the error message for specific details

For more detailed information about the installation process, see the [Installation Plan](documentation/en/installation_plan.md).