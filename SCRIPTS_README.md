# Tweet Screenshot Generator - Setup Scripts

This directory contains script files that make it easy to run the Tweet Screenshot Generator application.

## Scripts Overview

### 1. run.sh - Docker Setup Script

This script provides the easiest way to run the application using Docker:

```bash
./run.sh
```

**What it does:**
- Checks if Docker and Docker Compose are installed
- Builds and starts the application in a Docker container
- Shows you how to access the web interface (http://localhost:5001)
- Provides commands for stopping the application and viewing logs

**Requirements:**
- Docker and Docker Compose must be installed
- No other requirements (the Docker container has everything needed)

### 2. run_native.sh - Native Setup Script

This script runs the application directly on your system without Docker:

```bash
./run_native.sh
```

**What it does:**
- Checks if Python 3 and Google Chrome are installed
- Sets up a Python virtual environment
- Installs required dependencies
- Checks for ChromeDriver
- Automatically finds an available port if the default port is in use
- Starts the application
- Creates a stop.sh script for stopping the application
- Automatically launches the application in your default browser

**Requirements:**
- Python 3
- Google Chrome
- ChromeDriver matching your Chrome version (placed in the drivers directory)

## Troubleshooting

### Docker Setup Issues

- **Missing Docker**: Install Docker from https://docs.docker.com/get-docker/
- **Port conflict**: If port 5001 is already in use, modify the port mapping in docker-compose.yml
- **Permission denied**: You may need to run Docker with sudo on some systems

### Native Setup Issues

- **ChromeDriver errors**: Make sure the ChromeDriver version matches your Chrome browser version
- **Missing dependencies**: Check that all dependencies in requirements.txt installed correctly
- **Port conflict**: The script will automatically try to find an available port if the default port (5000) is in use
- **Browser doesn't open**: If the browser doesn't open automatically, manually navigate to the URL shown in the terminal
