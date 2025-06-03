#!/bin/bash
# Color for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

if [ -f .app.pid ]; then
    PID=$(cat .app.pid)
    echo -e "Stopping Tweet Screenshot Generator (PID: ${YELLOW}$PID${NC})..."
    # Check if process is still running
    if ps -p $PID > /dev/null; then
        kill $PID
        # Give it a moment to shut down
        sleep 1
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}Process still running, trying force kill...${NC}"
            kill -9 $PID
        fi
        echo -e "${GREEN}Application stopped successfully${NC}"
    else
        echo -e "${YELLOW}Process $PID no longer running${NC}"
    fi
    # Clean up files
    rm -f .app.pid
    if [ -f .app.port ]; then
        rm -f .app.port
    fi
else
    echo -e "${YELLOW}No running instance found${NC}"
    # Check for any stray Flask processes
    FLASK_PIDS=$(ps aux | grep -v grep | grep "python.*app.py" | awk '{print $2}')
    if [ ! -z "$FLASK_PIDS" ]; then
        echo -e "${YELLOW}Found stray Flask processes: $FLASK_PIDS${NC}"
        echo -e "Run: ${GREEN}kill $FLASK_PIDS${NC} to stop them"
    fi
fi
