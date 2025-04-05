#!/bin/bash
# Script to set up a virtual environment and install required dependencies

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up virtual environment for the booking agent project...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python -m venv venv
else
    echo -e "${BLUE}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Verify activation
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}Virtual environment activated successfully!${NC}"
else
    echo "Failed to activate virtual environment. Exiting."
    exit 1
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt

# Verify installation
echo -e "${BLUE}Installed packages:${NC}"
pip list

echo -e "${GREEN}Setup complete! The virtual environment is now ready.${NC}"
echo -e "${BLUE}To activate the virtual environment, run:${NC}"
echo -e "    source venv/bin/activate"
echo -e "${BLUE}To deactivate, simply run:${NC}"
echo -e "    deactivate"
