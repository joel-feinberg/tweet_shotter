#!/bin/bash
# Tweet Screenshot Generator - Native Setup Script
# This script helps you run the Tweet Screenshot Generator without Docker
#
# Features:
# - Automatically checks dependencies
# - Automatically finds an available port if default is in use
# - Automatically opens application in your browser
# - Creates stop.sh script for easy shutdown

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "==============================================="
    echo "  Tweet Screenshot Generator Native Setup"
    echo "==============================================="
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

print_info() {
    echo -e "$1"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3 first."
        print_info "Visit https://www.python.org/downloads/ for installation instructions."
        exit 1
    else
        print_success "✓ Python 3 is installed"
    fi
}

# Check if Chrome is installed
check_chrome() {
    if ! command -v google-chrome &> /dev/null && ! command -v google-chrome-stable &> /dev/null && ! [ -d "/Applications/Google Chrome.app" ]; then
        print_warning "⚠ Google Chrome might not be installed or not found in the standard location."
        print_info "The application requires Google Chrome to function properly."
        print_info "Visit https://www.google.com/chrome/ to download Chrome."
        
        print_info "\nDo you want to continue anyway? (y/n)"
        read -r ANSWER
        if [[ ! $ANSWER =~ ^[Yy] ]]; then
            exit 1
        fi
    else
        print_success "✓ Google Chrome appears to be installed"
    fi
}

# Set up Python virtual environment and install dependencies
setup_environment() {
    print_info "\nSetting up Python virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "✓ Created virtual environment"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_info "Installing dependencies..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "✓ Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Download ChromeDriver if needed
check_chromedriver() {
    print_info "\nChecking ChromeDriver..."
    
    if [ ! -d "drivers" ]; then
        mkdir -p drivers
    fi
    
    if [ ! -f "drivers/chromedriver" ] || [ ! -x "drivers/chromedriver" ]; then
        print_warning "⚠ ChromeDriver not found or not executable."
        print_info "You need to download the ChromeDriver version that matches your Chrome browser."
        print_info "Visit https://chromedriver.chromium.org/downloads"
        print_info "After downloading, extract it and place 'chromedriver' in the 'drivers' folder."
        print_info "\nDo you want to try to continue anyway? (y/n)"
        read -r ANSWER
        if [[ ! $ANSWER =~ ^[Yy] ]]; then
            exit 1
        fi
    else
        print_success "✓ ChromeDriver found"
    fi
}

# Check if a port is available
check_port_available() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i:"$port" >/dev/null 2>&1; then
            return 1  # Port is in use
        else
            return 0  # Port is available
        fi
    elif command -v nc >/dev/null 2>&1; then
        if nc -z localhost "$port" >/dev/null 2>&1; then
            return 1  # Port is in use
        else
            return 0  # Port is available
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -an | grep -q "[:.]$port "; then
            return 1  # Port is in use
        else
            return 0  # Port is available
        fi
    else
        # If we can't check, assume it's available
        print_warning "Could not verify if port $port is available. Assuming it is."
        return 0
    fi
}

# Find an available port starting from the given port
find_available_port() {
    local port=$1
    local max_attempts=10
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if check_port_available "$port"; then
            echo "$port"
            return 0
        fi
        print_warning "Port $port is in use. Trying next port."
        port=$((port + 1))
        attempt=$((attempt + 1))
    done
    
    # If we tried all ports and none were available, return the original
    echo "$1"
    return 1
}

# Open a URL in the default browser
open_browser() {
    local url=$1
    print_info "Opening $url in your default browser..."
    
    # Try to detect the platform and use the appropriate command
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "$url" &>/dev/null
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open "$url" &>/dev/null
        else
            print_warning "Could not automatically open browser. Please navigate to $url manually."
        fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows with Git Bash or similar
        start "$url" &>/dev/null || cmd.exe /c start "$url" &>/dev/null
    else
        print_warning "Could not automatically open browser. Please navigate to $url manually."
    fi
}

# Run the application
run_app() {
    print_info "\nStarting Tweet Screenshot Generator..."
    
    # Make sure output directory exists
    if [ ! -d "output_screenshots" ]; then
        mkdir -p output_screenshots
    fi
    
    # Get the default port from app.py
    # Look for FLASK_RUN_PORT in app.py
    if grep -q "FLASK_RUN_PORT\s*=\s*[0-9]+" app.py; then
        DEFAULT_PORT=$(grep "FLASK_RUN_PORT\s*=\s*[0-9]+" app.py | head -1 | sed -E 's/.*FLASK_RUN_PORT\s*=\s*([0-9]+).*/\1/')
        print_info "Detected port $DEFAULT_PORT from app.py"
    else
        DEFAULT_PORT=5000
        print_info "Could not detect port from app.py, using default port $DEFAULT_PORT"
    fi
    
    # Find an available port
    PORT=$(find_available_port $DEFAULT_PORT)
    
    if [ "$PORT" != "$DEFAULT_PORT" ]; then
        print_warning "Default port $DEFAULT_PORT is in use. Using port $PORT instead."
    fi
    
    # Export the port as an environment variable and run the app
    print_info "Starting app with port $PORT"
    export FLASK_RUN_PORT=$PORT
    
    # Run in debug mode to see more output
    python app.py &
    
    APP_PID=$!
    APP_PORT=$PORT
    
    # Save information for later use
    echo $APP_PID > .app.pid
    echo $APP_PORT > .app.port
    
    # Check if app started successfully
    print_info "Waiting for application to start..."
    local max_wait=10
    local wait_count=0
    local started=false
    
    # Give Flask a moment to start before checking the log
    sleep 2
    
    # First check for immediate startup errors in the log
    if [ -f "tweet_screenshotter.log" ]; then
        ERRORS=$(tail -20 tweet_screenshotter.log | grep -i "error")
        if [ ! -z "$ERRORS" ]; then
            print_warning "Potential errors detected in log file:"
            echo "$ERRORS" | head -3
        fi
    fi
    
    # Now try to connect
    while [ $wait_count -lt $max_wait ]; do
        sleep 1
        wait_count=$((wait_count + 1))
        
        if ! ps -p $APP_PID > /dev/null; then
            print_error "Process died unexpectedly"
            # Print the last few lines of stderr if available
            if [ -f "tweet_screenshotter.log" ]; then
                print_info "Last few lines of log:"
                tail -10 tweet_screenshotter.log
            fi
            break
        fi
        
        # Try to connect to the port
        if command -v curl >/dev/null 2>&1; then
            if curl -s http://localhost:$PORT/ >/dev/null 2>&1; then
                started=true
                break
            fi
        elif command -v wget >/dev/null 2>&1; then
            if wget -q --spider http://localhost:$PORT/ >/dev/null 2>&1; then
                started=true
                break
            fi
        else
            # If we can't check via HTTP, just give it a bit more time
            if [ $wait_count -ge 5 ]; then
                started=true
                break
            fi
        fi
    done
    
    if $started && ps -p $APP_PID > /dev/null; then
        print_success "✓ Application started successfully with PID $APP_PID on port $APP_PORT"
    else
        print_error "Failed to verify application is running properly"
        if ps -p $APP_PID > /dev/null; then
            print_warning "Process is running, but may not be responding to web requests"
            print_info "Check for errors in tweet_screenshotter.log"
            print_info "Continuing anyway..."
            started=true
        else
            print_error "Process has died. Check for errors in tweet_screenshotter.log"
            rm -f .app.pid .app.port
            exit 1
        fi
    fi
}

# Display access information
show_access_info() {
    # Get the port that was used
    local PORT=5000
    if [ -f .app.port ]; then
        PORT=$(cat .app.port)
    fi
    
    local APP_URL="http://localhost:$PORT"
    
    print_info "\n==============================================="
    print_info "  Tweet Screenshot Generator is ready!"
    print_info "==============================================="
    print_info ""
    print_info "Access the web interface at: ${GREEN}$APP_URL${NC}"
    print_info ""
    print_info "To stop the application, run:"
    print_info "  ${YELLOW}./stop.sh${NC}"
    print_info "or press Ctrl+C if running in foreground"
    print_info ""
    print_info "To view logs, check tweet_screenshotter.log file"
    print_info "==============================================="
    
    # Auto-launch the browser after a short delay
    sleep 2
    open_browser "$APP_URL"
}

# Create a stop script
create_stop_script() {
    cat > stop.sh << EOF
#!/bin/bash
# Color for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if [ -f .app.pid ]; then
    PID=\$(cat .app.pid)
    echo -e "Stopping Tweet Screenshot Generator (PID: \${YELLOW}\$PID\${NC})..."
    # Check if process is still running
    if ps -p \$PID > /dev/null; then
        kill \$PID
        # Give it a moment to shut down
        sleep 1
        if ps -p \$PID > /dev/null; then
            echo -e "\${YELLOW}Process still running, trying force kill...\${NC}"
            kill -9 \$PID
        fi
        echo -e "\${GREEN}Application stopped successfully\${NC}"
    else
        echo -e "\${YELLOW}Process \$PID no longer running\${NC}"
    fi
    # Clean up files
    rm -f .app.pid
    if [ -f .app.port ]; then
        rm -f .app.port
    fi
else
    echo -e "\${YELLOW}No running instance found\${NC}"
    # Check for any stray Flask processes
    FLASK_PIDS=\$(ps aux | grep -v grep | grep "python.*app.py" | awk '{print \$2}')
    if [ ! -z "\$FLASK_PIDS" ]; then
        echo -e "\${YELLOW}Found stray Flask processes: \$FLASK_PIDS\${NC}"
        echo -e "Run: \${GREEN}kill \$FLASK_PIDS\${NC} to stop them"
    fi
fi
EOF
    chmod +x stop.sh
    print_info "Created stop.sh script to easily stop the application"
}

# Main execution
print_header

# Check dependencies
check_python
check_chrome
check_chromedriver

# Set up environment
setup_environment

# Run the application
run_app

# Create stop script
create_stop_script

# Show access information and launch browser
show_access_info

print_info "\nPress Ctrl+C to stop the application or use ./stop.sh from another terminal"

# Keep the script running to show logs
wait $APP_PID
