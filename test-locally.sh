#!/bin/bash
# ComfyUI Setup Local Test Script
# This script helps test the setup locally before pushing to GitHub

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
    echo -e "${RED}This script should be run as root. Please use sudo or run as root.${NC}"
    exit 1
fi

# Create a temporary directory to simulate download from GitHub
TEMP_DIR=$(mktemp -d)
echo -e "${BLUE}Created temporary directory: $TEMP_DIR${NC}"

# Copy the main setup script to the temporary directory
echo -e "${BLUE}Copying comfyui-setup.sh to temporary directory...${NC}"
cp comfyui-setup.sh "$TEMP_DIR/comfyui-setup.sh"
chmod +x "$TEMP_DIR/comfyui-setup.sh"

# Create a modified bootstrap script that uses the local file
cat > "$TEMP_DIR/bootstrap-local.sh" << EOF
#!/bin/bash
# ComfyUI RunPod Bootstrap Script (LOCAL TEST VERSION)
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
    echo -e "\${RED}This script must be run as root. Please use sudo or run as root.\${NC}"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "\$1" >/dev/null 2>&1
}

# Check and install basic dependencies
echo -e "\${BLUE}Checking basic dependencies...\${NC}"
if ! command_exists wget; then
    echo -e "\${YELLOW}Installing wget...\${NC}"
    apt-get update
    apt-get install -y wget
fi

# Use the local copy of the setup script
SETUP_SCRIPT_PATH="$TEMP_DIR/comfyui-setup.sh"

# Execute the main setup script
echo -e "\${GREEN}Starting ComfyUI setup...\${NC}"
bash "\$SETUP_SCRIPT_PATH"
EOF

chmod +x "$TEMP_DIR/bootstrap-local.sh"

echo -e "${GREEN}Local test environment prepared.${NC}"
echo -e "${YELLOW}To test the setup script, run:${NC}"
echo -e "    sudo bash $TEMP_DIR/bootstrap-local.sh"
echo -e "${YELLOW}This will simulate the experience of running the setup script from GitHub.${NC}"
echo -e "${YELLOW}The temporary directory will be deleted on system reboot.${NC}"
