#!/bin/bash
# Setup script for variance monitor cron job

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Variance Monitor Cron Job${NC}"

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/variance_monitor.py"
LOG_FILE="$SCRIPT_DIR/variance_monitor.log"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}Error: variance_monitor.py not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Make sure the Python script is executable
chmod +x "$PYTHON_SCRIPT"

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Please copy .env.example to .env and configure it.${NC}"
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        echo -e "${YELLOW}Created .env from .env.example. Please edit it with your configuration.${NC}"
    fi
fi

# Find Python interpreter
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python not found. Please install Python 3.7+${NC}"
    exit 1
fi

echo "Using Python: $(which $PYTHON_CMD)"

# Check if required packages are installed
echo "Checking Python dependencies..."
$PYTHON_CMD -c "import requests, pandas, sqlalchemy" 2>/dev/null || {
    echo -e "${YELLOW}Installing required packages...${NC}"
    
    # Try to install with pip, handle different scenarios
    if $PYTHON_CMD -m pip install -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null; then
        echo -e "${GREEN}Dependencies installed successfully${NC}"
    elif $PYTHON_CMD -m pip install --user -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null; then
        echo -e "${GREEN}Dependencies installed in user directory${NC}"
    else
        echo -e "${YELLOW}Could not install dependencies automatically.${NC}"
        echo -e "${YELLOW}Please install manually:${NC}"
        echo "  $PYTHON_CMD -m pip install requests pandas sqlalchemy python-dotenv"
        echo "  Or create a virtual environment:"
        echo "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
}

# Create the cron job entry
# Runs every Monday at 9:00 AM
CRON_JOB="0 9 * * 1 cd $SCRIPT_DIR && $PYTHON_CMD $PYTHON_SCRIPT >> $LOG_FILE 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "variance_monitor.py"; then
    echo -e "${YELLOW}Cron job already exists. Removing old entry...${NC}"
    crontab -l 2>/dev/null | grep -v "variance_monitor.py" | crontab -
fi

# Add the new cron job
echo "Adding cron job: $CRON_JOB"
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

# Verify cron job was added
if crontab -l 2>/dev/null | grep -q "variance_monitor.py"; then
    echo -e "${GREEN}✅ Cron job successfully added!${NC}"
    echo -e "${GREEN}The variance monitor will run every Monday at 9:00 AM${NC}"
else
    echo -e "${RED}❌ Failed to add cron job${NC}"
    exit 1
fi

# Create log file if it doesn't exist
touch "$LOG_FILE"

echo ""
echo -e "${GREEN}Setup Complete!${NC}"
echo ""
echo "📋 Next Steps:"
echo "1. Edit .env file with your database connection and Slack webhook URL"
echo "2. Test the script manually: $PYTHON_CMD $PYTHON_SCRIPT"
echo "3. Check cron jobs: crontab -l"
echo "4. Monitor logs: tail -f $LOG_FILE"
echo ""
echo "📅 Schedule: Every Monday at 9:00 AM"
echo "📊 Query Range: First of month to yesterday"
echo "🔔 Alerts: Sent to Slack when variance ≠ 0"