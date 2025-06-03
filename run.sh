#!/bin/bash
# Tweet Screenshot Generator - Easy Setup Script
# This script helps you easily run the Tweet Screenshot Generator application using Docker

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "==============================================="
    echo "      Tweet Screenshot Generator Setup"
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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        print_info "Visit https://docs.docker.com/get-docker/ for installation instructions."
        exit 1
    else
        print_success "✓ Docker is installed"
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        print_info "Visit https://docs.docker.com/compose/install/ for installation instructions."
        exit 1
    else
        print_success "✓ Docker Compose is installed"
    fi
}

# Run the application with Docker Compose
run_app() {
    print_info "\nBuilding and starting the Tweet Screenshot Generator..."
    
    # Check which version of docker-compose command to use
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
    
    # Build and start the containers
    if ! $DOCKER_COMPOSE up --build -d; then
        print_error "Failed to build and start the containers. See error above."
        exit 1
    fi
    
    print_success "✓ Application is now running!"
}

# Display access information
show_access_info() {
    CONTAINER_RUNNING=$($DOCKER_COMPOSE ps | grep -q "tweet-screenshotter" && echo "yes" || echo "no")
    
    if [ "$CONTAINER_RUNNING" = "yes" ]; then
        print_info "\n==============================================="
        print_info "  Tweet Screenshot Generator is ready!"
        print_info "==============================================="
        print_info ""
        print_info "Access the web interface at: ${GREEN}http://localhost:5001${NC}"
        print_info ""
        print_info "To stop the application, run:"
        print_info "  ${YELLOW}$DOCKER_COMPOSE down${NC}"
        print_info ""
        print_info "To view logs:"
        print_info "  ${YELLOW}$DOCKER_COMPOSE logs -f${NC}"
        print_info "==============================================="
    else
        print_error "The container doesn't appear to be running. There might have been an error."
        print_info "Check the logs with: ${YELLOW}$DOCKER_COMPOSE logs${NC}"
    fi
}

# Check for updates (optional)
check_for_updates() {
    # Check if this is a git repository
    if [ -d ".git" ] && command -v git &> /dev/null; then
        print_info "\nChecking for updates..."
        git remote update > /dev/null 2>&1
        
        UPSTREAM=${1:-'@{u}'}
        LOCAL=$(git rev-parse @)
        REMOTE=$(git rev-parse "$UPSTREAM" 2>/dev/null || echo "$LOCAL")
        
        if [ "$LOCAL" != "$REMOTE" ]; then
            print_warning "Updates are available. Would you like to update? (y/n)"
            read -r ANSWER
            if [[ $ANSWER =~ ^[Yy] ]]; then
                git pull
                print_success "✓ Repository updated"
            else
                print_info "Continuing with current version"
            fi
        else
            print_success "✓ You are using the latest version"
        fi
    fi
}

# Main execution
print_header

# Check dependencies
check_docker

# Optional: Check for updates 
# Remove the comment below if you want to enable update checks
# check_for_updates

# Run the application
run_app

# Show access information
show_access_info

exit 0
