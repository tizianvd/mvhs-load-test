#!/bin/bash

# MVHS Load Test - Enhanced Web UI Launcher (Ubuntu/WSL)
# Optimized for web mode usage with enhanced features

echo ""
echo "========================================================"
echo "🚀 MVHS Load Test - Enhanced Web UI Launcher"
echo "========================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python availability
if ! command_exists python3 && ! command_exists python; then
    echo -e "${RED}❌ Python not found! Please install Python or ensure it's in your PATH.${NC}"
    echo "   Try: sudo apt update && sudo apt install python3 python3-pip"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command_exists python3; then
    PYTHON_CMD="python"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}✅ Found: $PYTHON_VERSION${NC}"

# Check if pip is available
PIP_CMD="pip3"
if ! command_exists pip3; then
    if command_exists pip; then
        PIP_CMD="pip"
    else
        echo -e "${RED}❌ pip not found! Installing pip...${NC}"
        sudo apt update && sudo apt install python3-pip
        PIP_CMD="pip3"
    fi
fi

# Check if locust is installed
if ! $PYTHON_CMD -c "import locust" >/dev/null 2>&1; then
    echo -e "${YELLOW}❌ Locust not found! Installing requirements...${NC}"
    if [[ -f "requirements.txt" ]]; then
        $PIP_CMD install -r requirements.txt
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}❌ Failed to install requirements! Please run: $PIP_CMD install -r requirements.txt${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}📦 Installing Locust directly...${NC}"
        $PIP_CMD install locust
        if [[ $? -ne 0 ]]; then
            echo -e "${RED}❌ Failed to install Locust! Please run: $PIP_CMD install locust${NC}"
            exit 1
        fi
    fi
    echo -e "${GREEN}✅ Requirements installed successfully!${NC}"
else
    echo -e "${GREEN}✅ Locust is installed and ready!${NC}"
fi

echo ""

# Set environment variables for web mode optimization
export TEST_MODE="realistic"
export USER_BEHAVIOR="realistic"
export WEBSITE_PROFILE="mvhs_production"

echo -e "${CYAN}🎛️ Environment configured for enhanced web mode:${NC}"
echo -e "   ${GRAY}Test Mode: $TEST_MODE${NC}"
echo -e "   ${GRAY}User Behavior: $USER_BEHAVIOR${NC}"
echo -e "   ${GRAY}Website Profile: $WEBSITE_PROFILE${NC}"
echo ""

# Create reports directory if it doesn't exist
if [[ ! -d "reports" ]]; then
    mkdir -p reports
    echo -e "${GRAY}📁 Created reports directory${NC}"
fi

# Create logs directory if it doesn't exist
if [[ ! -d "reports/logs" ]]; then
    mkdir -p reports/logs
    echo -e "${GRAY}📁 Created logs directory${NC}"
fi

echo -e "${GREEN}🌐 Starting Locust Web UI with enhanced features...${NC}"
echo ""
echo -e "${YELLOW}🌐 Web Interface will be available at:${NC}"
echo -e "   ${NC}📍 Main Dashboard: http://localhost:8089${NC}"
echo -e "   ${NC}🎯 Enhanced Dashboard: http://localhost:8089/test-dashboard${NC}"
echo -e "   ${NC}🔄 Profile Selector: http://localhost:8089/profile-selector${NC}"
echo -e "   ${NC}⚙️ Configuration: http://localhost:8089/test-config${NC}"
echo -e "   ${NC}📊 Live API Stats: http://localhost:8089/api/stats${NC}"
echo ""
echo -e "${YELLOW}💡 Quick Start Guide:${NC}"
echo -e "   ${GRAY}1. Open http://localhost:8089 in your browser${NC}"
echo -e "   ${GRAY}2. Set Number of users: 10-20 for testing${NC}"
echo -e "   ${GRAY}3. Set Spawn rate: 2 users per second${NC}"
echo -e "   ${GRAY}4. Click 'Start Test' and monitor the live charts${NC}"
echo -e "   ${GRAY}5. Use the floating widgets for quick configuration${NC}"
echo ""
echo -e "${MAGENTA}🔥 Enhanced Web Features:${NC}"
echo -e "   ${GRAY}✨ Real-time profile switching without restart${NC}"
echo -e "   ${GRAY}⚡ Live behavior configuration (realistic/fast/stress/mobile)${NC}"
echo -e "   ${GRAY}📊 Enhanced analytics and reporting${NC}"
echo -e "   ${GRAY}📱 Mobile-responsive interface${NC}"
echo -e "   ${GRAY}🎯 Floating control widgets${NC}"
echo -e "   ${GRAY}📈 Real-time statistics API${NC}"
echo ""

# Function to open browser (works in WSL with Windows browser)
open_browser() {
    sleep 3
    if command_exists wslview; then
        # WSL utility to open Windows applications
        wslview "http://localhost:8089" >/dev/null 2>&1 && echo -e "${GREEN}🌐 Browser opened automatically!${NC}"
    elif command_exists cmd.exe; then
        # Direct Windows command from WSL
        cmd.exe /c start "http://localhost:8089" >/dev/null 2>&1 && echo -e "${GREEN}🌐 Browser opened automatically!${NC}"
    elif [[ -n "$WSL_DISTRO_NAME" ]]; then
        # We're in WSL, try Windows browser via explorer
        /mnt/c/Windows/explorer.exe "http://localhost:8089" >/dev/null 2>&1 && echo -e "${GREEN}🌐 Browser opened automatically!${NC}"
    else
        # Try standard Linux browsers
        if command_exists xdg-open; then
            xdg-open "http://localhost:8089" >/dev/null 2>&1 && echo -e "${GREEN}🌐 Browser opened automatically!${NC}"
        elif command_exists firefox; then
            firefox "http://localhost:8089" >/dev/null 2>&1 &
            echo -e "${GREEN}🌐 Firefox opened automatically!${NC}"
        else
            echo -e "${YELLOW}💡 Please manually open: http://localhost:8089${NC}"
        fi
    fi
}

# Start browser opener in background
open_browser &

echo -e "${GREEN}🚀 Launching Locust Web UI...${NC}"
echo -e "${GRAY}   (Press Ctrl+C to stop the server)${NC}"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo -e "${CYAN}🏁 Locust Web UI session ended.${NC}"
    echo -e "${GRAY}📊 Check reports/ folder for detailed test results.${NC}"
    echo ""
    
    # Kill any background jobs
    jobs -p | xargs -r kill >/dev/null 2>&1
    
    echo "Press Enter to exit..."
    read
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Start Locust with web UI optimized settings
LOG_FILE="reports/logs/locust_web_$(date +%Y%m%d_%H%M%S).log"
echo -e "${GRAY}📝 Logging to: $LOG_FILE${NC}"

$PYTHON_CMD -m locust --web-host=0.0.0.0 --web-port=8089 --logfile="$LOG_FILE"
