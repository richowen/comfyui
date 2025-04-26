#!/bin/bash
# ComfyUI RunPod Bootstrap Script
# Downloads and executes the main setup script

# Set up error handling
set -e
trap 'echo "An error occurred. Exiting..."; exit 1' ERR

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}This script must be run as root. Please use sudo or run as root.${NC}"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check and install basic dependencies
echo -e "${BLUE}Checking basic dependencies...${NC}"
if ! command_exists wget; then
    echo -e "${YELLOW}Installing wget...${NC}"
    apt-get update
    apt-get install -y wget
fi

# URL of the main setup script
SETUP_SCRIPT_URL="https://raw.githubusercontent.com/richowen/comfyui/main/comfyui-setup.sh"

# Download the main setup script
echo -e "${BLUE}Downloading main setup script...${NC}"
wget -O /tmp/comfyui-setup.sh "$SETUP_SCRIPT_URL"

# Make the script executable
chmod +x /tmp/comfyui-setup.sh

# Execute the main setup script
echo -e "${GREEN}Starting ComfyUI setup...${NC}"
bash /tmp/comfyui-setup.sh

# Clean up
rm -f /tmp/comfyui-setup.sh
