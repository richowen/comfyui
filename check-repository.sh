#!/bin/bash
# ComfyUI Repository Check Script
# Verifies that the GitHub repository URLs are accessible

# Set up error handling
set -e
trap 'echo "An error occurred. Exiting..."; exit 1' ERR

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GitHub repository information
GITHUB_USERNAME="richowen"
REPO_NAME="comfyui"
BRANCH="main"
FILES_TO_CHECK=(
    "bootstrap.sh"
    "comfyui-setup.sh"
    "README.md"
)

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if curl is installed
if ! command_exists curl; then
    echo -e "${YELLOW}The 'curl' command is not installed. Installing...${NC}"
    apt-get update && apt-get install -y curl
fi

echo -e "${BLUE}Checking GitHub repository: https://github.com/$GITHUB_USERNAME/$REPO_NAME${NC}"

# Check if the repository exists and is accessible
REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$REPO_URL")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Repository exists and is accessible${NC}"
else
    echo -e "${RED}✗ Repository check failed (HTTP code: $HTTP_CODE)${NC}"
    echo -e "${YELLOW}Please check if the repository exists and is public at:${NC}"
    echo -e "${YELLOW}$REPO_URL${NC}"
    exit 1
fi

# Check each file
echo -e "\n${BLUE}Checking required files:${NC}"
for file in "${FILES_TO_CHECK[@]}"; do
    FILE_URL="https://raw.githubusercontent.com/$GITHUB_USERNAME/$REPO_NAME/$BRANCH/$file"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FILE_URL")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ $file is accessible${NC}"
    else
        echo -e "${RED}✗ $file is not accessible (HTTP code: $HTTP_CODE)${NC}"
        echo -e "${YELLOW}URL: $FILE_URL${NC}"
    fi
done

echo ""
echo -e "${BLUE}Repository status summary:${NC}"
echo -e "Repository: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo -e "Branch: $BRANCH"

# Count successful checks
SUCCESSFUL=0
for file in "${FILES_TO_CHECK[@]}"; do
    FILE_URL="https://raw.githubusercontent.com/$GITHUB_USERNAME/$REPO_NAME/$BRANCH/$file"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FILE_URL")
    
    if [ "$HTTP_CODE" = "200" ]; then
        SUCCESSFUL=$((SUCCESSFUL + 1))
    fi
done

# Print overall status
if [ "$SUCCESSFUL" -eq "${#FILES_TO_CHECK[@]}" ]; then
    echo -e "${GREEN}All files are accessible. Repository is ready to use.${NC}"
    echo -e "${GREEN}The one-liner installation command should work:${NC}"
    echo -e "sudo bash -c \"\$(curl -sSL https://raw.githubusercontent.com/$GITHUB_USERNAME/$REPO_NAME/$BRANCH/bootstrap.sh)\""
else
    echo -e "${RED}Some files are not accessible. Please check your repository setup.${NC}"
    echo -e "${YELLOW}Steps to fix:${NC}"
    echo -e "1. Make sure you have pushed all files to GitHub"
    echo -e "2. Ensure the repository is public or accessible to the intended users"
    echo -e "3. Verify that the files are in the correct location (root of the repository)"
    echo -e "4. Check that the branch name ($BRANCH) is correct"
fi
