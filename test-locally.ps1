# ComfyUI Setup Local Test Script for Windows
# This script helps test the setup locally before pushing to GitHub

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script should be run as Administrator. Please restart as Administrator."
    exit
}

# Create a temporary directory to simulate download from GitHub
$TEMP_DIR = New-Item -ItemType Directory -Path "$env:TEMP\comfyui-test-$(Get-Random)" -Force
Write-Host "Created temporary directory: $TEMP_DIR" -ForegroundColor Cyan

# Copy the main setup script to the temporary directory
Write-Host "Copying comfyui-setup.sh to temporary directory..." -ForegroundColor Cyan
Copy-Item -Path "comfyui-setup.sh" -Destination "$TEMP_DIR\comfyui-setup.sh"

# Create a modified bootstrap script that uses the local file
$BOOTSTRAP_CONTENT = @"
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
if [ "\$(id -u)" -ne 0 ]; then
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
SETUP_SCRIPT_PATH="$($TEMP_DIR.FullName -replace '\\', '/')/comfyui-setup.sh"

# Execute the main setup script
echo -e "\${GREEN}Starting ComfyUI setup...\${NC}"
bash "\$SETUP_SCRIPT_PATH"
"@

Set-Content -Path "$TEMP_DIR\bootstrap-local.sh" -Value $BOOTSTRAP_CONTENT

Write-Host "Local test environment prepared." -ForegroundColor Green
Write-Host ""
Write-Host "To test on a Linux system (WSL or RunPod):" -ForegroundColor Yellow
Write-Host "1. Copy the files to a Linux environment:" -ForegroundColor Yellow
Write-Host "   Copy-Item -Path '$TEMP_DIR\*' -Destination '\\wsl$\Ubuntu\home\username\' -Recurse" -ForegroundColor Gray
Write-Host "   # Or use SCP to copy to RunPod" -ForegroundColor Gray
Write-Host ""
Write-Host "2. In the Linux environment, run:" -ForegroundColor Yellow
Write-Host "   sudo bash bootstrap-local.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "The temporary directory location is: $TEMP_DIR" -ForegroundColor Cyan
