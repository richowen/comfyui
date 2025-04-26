#!/bin/bash
# ComfyUI RunPod Setup Script
# Provides a TUI for configuring and installing ComfyUI with various options

# Set up error handling
set -e
trap 'echo "An error occurred. Exiting..."; exit 1' ERR

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables with defaults
COMFYUI_DIR="$HOME/ComfyUI"
CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
MODELS_DIR="$COMFYUI_DIR/models"
WORKFLOWS_DIR="$COMFYUI_DIR/workflows"
COMFYUI_REPO="https://github.com/comfyanonymous/ComfyUI.git"
COMFYUI_BRANCH="master"
PORT="8188"
CUDA_VISIBLE_DEVICES="0"
CUSTOM_PACKAGE_URL=""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check and install dependencies
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    local missing_deps=()
    
    # Check for necessary tools
    for cmd in git python3 pip3 wget dialog jq; do
        if ! command_exists "$cmd"; then
            missing_deps+=("$cmd")
        fi
    done
    
    # Install missing dependencies if any
    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${YELLOW}Installing missing dependencies: ${missing_deps[*]}${NC}"
        apt-get update
        apt-get install -y "${missing_deps[@]}"
    fi
    
    echo -e "${GREEN}All dependencies are installed.${NC}"
}

# Function to clone ComfyUI repository
clone_comfyui() {
    echo -e "${BLUE}Cloning ComfyUI from $COMFYUI_REPO (branch: $COMFYUI_BRANCH)...${NC}"
    
    if [ -d "$COMFYUI_DIR" ]; then
        echo -e "${YELLOW}ComfyUI directory already exists. Updating...${NC}"
        cd "$COMFYUI_DIR"
        git pull
        git checkout "$COMFYUI_BRANCH"
    else
        git clone "$COMFYUI_REPO" "$COMFYUI_DIR"
        cd "$COMFYUI_DIR"
        git checkout "$COMFYUI_BRANCH"
    fi
    
    # Create necessary directories
    mkdir -p "$CUSTOM_NODES_DIR"
    mkdir -p "$MODELS_DIR/checkpoints"
    mkdir -p "$MODELS_DIR/loras"
    mkdir -p "$MODELS_DIR/controlnet"
    mkdir -p "$MODELS_DIR/vae"
    mkdir -p "$WORKFLOWS_DIR"
    
    echo -e "${GREEN}ComfyUI cloned successfully.${NC}"
}

# Function to install Python requirements
install_requirements() {
    echo -e "${BLUE}Installing Python requirements...${NC}"
    cd "$COMFYUI_DIR"
    pip3 install -r requirements.txt
    echo -e "${GREEN}Python requirements installed.${NC}"
}

# Function to install selected extensions
install_extensions() {
    local extensions=("$@")
    
    if [ ${#extensions[@]} -eq 0 ]; then
        echo -e "${YELLOW}No extensions selected for installation.${NC}"
        return
    fi
    
    echo -e "${BLUE}Installing selected extensions...${NC}"
    
    for extension in "${extensions[@]}"; do
        case "$extension" in
            "ComfyUI-Manager")
                echo -e "${BLUE}Installing ComfyUI-Manager...${NC}"
                cd "$CUSTOM_NODES_DIR"
                git clone https://github.com/ltdrdata/ComfyUI-Manager.git
                ;;
            "ControlNet")
                echo -e "${BLUE}Installing ControlNet nodes...${NC}"
                cd "$CUSTOM_NODES_DIR"
                git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git
                pip3 install -r "$CUSTOM_NODES_DIR/comfyui_controlnet_aux/requirements.txt"
                ;;
            "ReActor")
                echo -e "${BLUE}Installing ReActor nodes...${NC}"
                cd "$CUSTOM_NODES_DIR"
                git clone https://github.com/Gourieff/comfyui-reactor-node.git
                pip3 install -r "$CUSTOM_NODES_DIR/comfyui-reactor-node/requirements.txt"
                ;;
            "Impact-Pack")
                echo -e "${BLUE}Installing Impact Pack...${NC}"
                cd "$CUSTOM_NODES_DIR"
                git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
                pip3 install -r "$CUSTOM_NODES_DIR/ComfyUI-Impact-Pack/requirements.txt"
                ;;
            "Efficiency-Nodes")
                echo -e "${BLUE}Installing Efficiency Nodes...${NC}"
                cd "$CUSTOM_NODES_DIR"
                git clone https://github.com/LucianoCirino/efficiency-nodes-comfyui.git
                ;;
            *)
                if [[ "$extension" == http* ]]; then
                    echo -e "${BLUE}Installing custom extension from: $extension${NC}"
                    cd "$CUSTOM_NODES_DIR"
                    git clone "$extension"
                    # Try to install requirements if they exist
                    extension_dir=$(basename "$extension" .git)
                    if [ -f "$CUSTOM_NODES_DIR/$extension_dir/requirements.txt" ]; then
                        pip3 install -r "$CUSTOM_NODES_DIR/$extension_dir/requirements.txt"
                    fi
                fi
                ;;
        esac
    done
    
    echo -e "${GREEN}Extensions installed successfully.${NC}"
}

# Function to download selected models
download_models() {
    local models=("$@")
    
    if [ ${#models[@]} -eq 0 ]; then
        echo -e "${YELLOW}No models selected for download.${NC}"
        return
    fi
    
    echo -e "${BLUE}Downloading selected models...${NC}"
    
    for model in "${models[@]}"; do
        case "$model" in
            "SD1.5")
                echo -e "${BLUE}Downloading Stable Diffusion 1.5...${NC}"
                wget -O "$MODELS_DIR/checkpoints/v1-5-pruned-emaonly.safetensors" \
                    "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors"
                ;;
            "SDXL")
                echo -e "${BLUE}Downloading Stable Diffusion XL...${NC}"
                wget -O "$MODELS_DIR/checkpoints/sdxl_base_1.0.safetensors" \
                    "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors"
                ;;
            "VAE-SDXL")
                echo -e "${BLUE}Downloading SDXL VAE...${NC}"
                wget -O "$MODELS_DIR/vae/sdxl_vae.safetensors" \
                    "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors"
                ;;
            "ControlNet-Canny")
                echo -e "${BLUE}Downloading ControlNet Canny...${NC}"
                wget -O "$MODELS_DIR/controlnet/control_canny-fp16.safetensors" \
                    "https://huggingface.co/comfyanonymous/ControlNet-v1-1_fp16_safetensors/resolve/main/control_canny-fp16.safetensors"
                ;;
            *)
                if [[ "$model" == http* ]]; then
                    echo -e "${BLUE}Downloading custom model from: $model${NC}"
                    filename=$(basename "$model")
                    if [[ "$model" == *civitai* ]]; then
                        # For CivitAI, try to use the model name from the URL
                        wget -O "$MODELS_DIR/checkpoints/$filename" "$model"
                    elif [[ "$model" == *huggingface* ]]; then
                        # For HuggingFace, download to checkpoints by default
                        wget -O "$MODELS_DIR/checkpoints/$filename" "$model"
                    else
                        # For generic URLs, download to checkpoints by default
                        wget -O "$MODELS_DIR/checkpoints/$filename" "$model"
                    fi
                fi
                ;;
        esac
    done
    
    echo -e "${GREEN}Models downloaded successfully.${NC}"
}

# Function to download and extract custom package
download_custom_package() {
    if [ -z "$CUSTOM_PACKAGE_URL" ]; then
        echo -e "${YELLOW}No custom package URL provided. Skipping...${NC}"
        return
    fi
    
    echo -e "${BLUE}Downloading custom package from: $CUSTOM_PACKAGE_URL${NC}"
    
    # Create a temporary directory
    local temp_dir=$(mktemp -d)
    local package_file="$temp_dir/custom_package.zip"
    
    # Download the package
    wget -O "$package_file" "$CUSTOM_PACKAGE_URL"
    
    # Check if download was successful
    if [ ! -f "$package_file" ]; then
        echo -e "${RED}Failed to download custom package.${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Extracting custom package...${NC}"
    
    # Extract the package to the temporary directory
    unzip -q "$package_file" -d "$temp_dir/extracted"
    
    # Check for workflows directory and copy files
    if [ -d "$temp_dir/extracted/workflows" ]; then
        cp -r "$temp_dir/extracted/workflows/"* "$WORKFLOWS_DIR/"
    fi
    
    # Check for custom_nodes directory and copy files
    if [ -d "$temp_dir/extracted/custom_nodes" ]; then
        cp -r "$temp_dir/extracted/custom_nodes/"* "$CUSTOM_NODES_DIR/"
    fi
    
    # Check for models directory and copy files
    if [ -d "$temp_dir/extracted/models" ]; then
        # Copy each model category if it exists
        for category in checkpoints loras controlnet vae embeddings insightface ultralytics; do
            if [ -d "$temp_dir/extracted/models/$category" ]; then
                mkdir -p "$MODELS_DIR/$category"
                cp -r "$temp_dir/extracted/models/$category/"* "$MODELS_DIR/$category/"
            fi
        done
    fi
    
    # Check for download_models.py script and process external models if exists
    if [ -f "$temp_dir/extracted/download_models.py" ]; then
        cp "$temp_dir/extracted/download_models.py" "$COMFYUI_DIR/download_models.py"
        chmod +x "$COMFYUI_DIR/download_models.py"
        
        echo -e "${BLUE}Found external model downloader. Processing external models...${NC}"
        
        # Check if user wants to download external models
        dialog --clear --backtitle "ComfyUI Setup" \
            --title "External Models" \
            --yesno "This package contains external models that need to be downloaded separately. Download them now?\n(This might take some time depending on model sizes)" 10 60 \
            2>&1 >/dev/tty
        
        if [ $? -eq 0 ]; then
            echo -e "${BLUE}Downloading external models...${NC}"
            cd "$COMFYUI_DIR"
            python3 download_models.py
        else
            echo -e "${YELLOW}Skipping external model downloads. You can run the downloader later with:${NC}"
            echo -e "cd $COMFYUI_DIR && python3 download_models.py"
        fi
    fi
    
    # Check for config.json and process if needed
    if [ -f "$temp_dir/extracted/config.json" ]; then
        echo -e "${BLUE}Processing configuration from custom package...${NC}"
        
        # Copy config.json to ComfyUI directory for reference
        cp "$temp_dir/extracted/config.json" "$COMFYUI_DIR/package_config.json"
        
        # Install dependencies from config.json
        if jq -e '.dependencies' "$temp_dir/extracted/config.json" >/dev/null 2>&1; then
            echo -e "${BLUE}Installing dependencies from config.json...${NC}"
            local deps=$(jq -r '.dependencies[]' "$temp_dir/extracted/config.json" 2>/dev/null || echo "")
            for dep in $deps; do
                if [[ "$dep" == pip:* ]]; then
                    # Handle pip dependencies
                    local pip_package=${dep#pip:}
                    echo -e "${BLUE}Installing pip package: $pip_package${NC}"
                    pip3 install "$pip_package"
                elif [[ "$dep" == apt:* ]]; then
                    # Handle apt dependencies
                    local apt_package=${dep#apt:}
                    echo -e "${BLUE}Installing apt package: $apt_package${NC}"
                    apt-get install -y "$apt_package"
                else
                    # Handle generic dependencies
                    echo -e "${BLUE}Installing dependency: $dep${NC}"
                    pip3 install "$dep"
                fi
            done
        fi
        
        # Process external models directly from config.json if no download script
        if [ ! -f "$temp_dir/extracted/download_models.py" ] && jq -e '.external_models' "$temp_dir/extracted/config.json" >/dev/null 2>&1; then
            echo -e "${BLUE}Found external models in config.json${NC}"
            
            # Ask user if they want to download external models
            dialog --clear --backtitle "ComfyUI Setup" \
                --title "External Models" \
                --yesno "This package references external models. Would you like to download them now?\n(This might take some time depending on model sizes)" 10 60 \
                2>&1 >/dev/tty
            
            if [ $? -eq 0 ]; then
                echo -e "${BLUE}Processing external models from config.json...${NC}"
                
                # Check if requests is installed
                if ! python3 -c "import requests" >/dev/null 2>&1; then
                    echo -e "${YELLOW}Installing Python requests module...${NC}"
                    pip3 install requests
                fi
                
                # Process each external model
                local model_count=$(jq '.external_models | length' "$temp_dir/extracted/config.json")
                echo -e "${BLUE}Found $model_count external models to download${NC}"
                
                for ((i=0; i<$model_count; i++)); do
                    local model_name=$(jq -r ".external_models[$i].name" "$temp_dir/extracted/config.json")
                    local model_type=$(jq -r ".external_models[$i].type" "$temp_dir/extracted/config.json")
                    local model_url=$(jq -r ".external_models[$i].url" "$temp_dir/extracted/config.json")
                    local model_path=$(jq -r ".external_models[$i].path // \"\"" "$temp_dir/extracted/config.json")
                    
                    # Create destination directory
                    mkdir -p "$MODELS_DIR/$model_type"
                    local dest_dir="$MODELS_DIR/$model_type"
                    
                    # Handle subdirectory if specified in path
                    if [ ! -z "$model_path" ] && [[ "$model_path" == */* ]]; then
                        local subdir=$(dirname "$model_path")
                        mkdir -p "$dest_dir/$subdir"
                        dest_dir="$dest_dir/$subdir"
                    fi
                    
                    local dest_file="$dest_dir/$model_name"
                    
                    echo -e "${BLUE}Downloading $model_name from $model_url${NC}"
                    
                    # Download with progress using wget
                    if ! wget --progress=bar:force -O "$dest_file" "$model_url"; then
                        echo -e "${RED}Failed to download $model_name. Please download it manually from:${NC}"
                        echo -e "${RED}$model_url${NC}"
                        echo -e "${RED}And place it in: $dest_dir/${NC}"
                    else
                        echo -e "${GREEN}Successfully downloaded $model_name${NC}"
                    fi
                done
            else
                echo -e "${YELLOW}Skipping external model downloads.${NC}"
            fi
        fi
        
        # Apply GPU settings if specified
        if jq -e '.gpu_settings' "$temp_dir/extracted/config.json" >/dev/null 2>&1; then
            echo -e "${BLUE}Applying GPU settings from config.json...${NC}"
            # Example: Set VRAM optimization
            if jq -e '.gpu_settings.vram_optimize' "$temp_dir/extracted/config.json" >/dev/null 2>&1; then
                local vram_optimize=$(jq -r '.gpu_settings.vram_optimize' "$temp_dir/extracted/config.json")
                if [ "$vram_optimize" = "true" ]; then
                    echo -e "${BLUE}Enabling VRAM optimization...${NC}"
                    # Set appropriate environment variable or config
                    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
                fi
            fi
        fi
        
        # Run post-install commands if specified
        if jq -e '.post_install_commands' "$temp_dir/extracted/config.json" >/dev/null 2>&1; then
            echo -e "${BLUE}Running post-install commands from config.json...${NC}"
            local commands=$(jq -r '.post_install_commands[]' "$temp_dir/extracted/config.json" 2>/dev/null || echo "")
            for cmd in "$commands"; do
                echo -e "${BLUE}Running command: $cmd${NC}"
                cd "$COMFYUI_DIR"
                eval "$cmd"
            fi
        fi
    fi
    
    # Clean up
    rm -rf "$temp_dir"
    
    echo -e "${GREEN}Custom package processed successfully.${NC}"
}

# Function to create a launch script
create_launch_script() {
    echo -e "${BLUE}Creating launch script...${NC}"
    
    # Create the launch script
    cat > "$COMFYUI_DIR/start_comfyui.sh" << EOF
#!/bin/bash
# ComfyUI Launch Script

export CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES

cd "$COMFYUI_DIR"
python3 main.py --port $PORT --listen 0.0.0.0
EOF
    
    # Make it executable
    chmod +x "$COMFYUI_DIR/start_comfyui.sh"
    
    echo -e "${GREEN}Launch script created at $COMFYUI_DIR/start_comfyui.sh${NC}"
}

# Function to display TUI for ComfyUI installation options
tui_comfyui_options() {
    COMFYUI_BRANCH=$(dialog --clear --backtitle "ComfyUI Setup" \
        --title "ComfyUI Installation Options" \
        --menu "Select ComfyUI branch:" 15 60 4 \
        "master" "Main branch (stable)" \
        "main" "Main branch (alias)" \
        "dev" "Development branch (may be unstable)" \
        2>&1 >/dev/tty)
    
    PORT=$(dialog --clear --backtitle "ComfyUI Setup" \
        --title "ComfyUI Configuration" \
        --inputbox "Enter port number for ComfyUI:" 8 40 "$PORT" \
        2>&1 >/dev/tty)
}

# Function to display TUI for extensions selection
tui_extensions() {
    local choices=$(dialog --clear --backtitle "ComfyUI Setup" \
        --title "Extensions Selection" \
        --checklist "Select extensions to install:" 20 60 10 \
        "ComfyUI-Manager" "Node management and installation tool" ON \
        "ControlNet" "Control your generations with images" OFF \
        "ReActor" "Face swapping and restoration" OFF \
        "Impact-Pack" "Additional utility nodes" OFF \
        "Efficiency-Nodes" "Performance optimization nodes" OFF \
        "Custom" "Add custom extension URL" OFF \
        2>&1 >/dev/tty)
    
    # Parse the choices
    local selected_extensions=()
    for choice in $choices; do
        # Remove quotes
        choice=$(echo "$choice" | tr -d '"')
        
        if [ "$choice" = "Custom" ]; then
            # Ask for custom extension URL
            local custom_url=$(dialog --clear --backtitle "ComfyUI Setup" \
                --title "Custom Extension" \
                --inputbox "Enter GitHub URL for custom extension:" 8 60 "" \
                2>&1 >/dev/tty)
            
            if [ -n "$custom_url" ]; then
                selected_extensions+=("$custom_url")
            fi
        else
            selected_extensions+=("$choice")
        fi
    done
    
    echo "${selected_extensions[@]}"
}

# Function to display TUI for models selection
tui_models() {
    local choices=$(dialog --clear --backtitle "ComfyUI Setup" \
        --title "Models Selection" \
        --checklist "Select models to download:" 20 60 10 \
        "SD1.5" "Stable Diffusion 1.5" ON \
        "SDXL" "Stable Diffusion XL" OFF \
        "VAE-SDXL" "SDXL VAE" OFF \
        "ControlNet-Canny" "ControlNet Canny model" OFF \
        "Custom" "Add custom model URL" OFF \
        2>&1 >/dev/tty)
    
    # Parse the choices
    local selected_models=()
    for choice in $choices; do
        # Remove quotes
        choice=$(echo "$choice" | tr -d '"')
        
        if [ "$choice" = "Custom" ]; then
            # Ask for custom model URL
            local custom_url=$(dialog --clear --backtitle "ComfyUI Setup" \
                --title "Custom Model" \
                --inputbox "Enter URL for custom model:" 8 60 "" \
                2>&1 >/dev/tty)
            
            if [ -n "$custom_url" ]; then
                selected_models+=("$custom_url")
            fi
        else
            selected_models+=("$choice")
        fi
    done
    
    echo "${selected_models[@]}"
}

# Function to display TUI for custom package URL
tui_custom_package() {
    CUSTOM_PACKAGE_URL=$(dialog --clear --backtitle "ComfyUI Setup" \
        --title "Custom Package" \
        --inputbox "Enter URL for custom package (leave empty to skip):" 8 60 "" \
        2>&1 >/dev/tty)
}

# Function to display TUI for advanced configuration
tui_advanced_config() {
    CUDA_VISIBLE_DEVICES=$(dialog --clear --backtitle "ComfyUI Setup" \
        --title "Advanced Configuration" \
        --inputbox "Enter CUDA_VISIBLE_DEVICES (comma-separated GPU indices, e.g., 0,1):" 8 60 "$CUDA_VISIBLE_DEVICES" \
        2>&1 >/dev/tty)
}

# Function to display the main TUI menu
tui_main_menu() {
    local selected_extensions=()
    local selected_models=()
    
    while true; do
        local choice=$(dialog --clear --backtitle "ComfyUI Setup" \
            --title "Main Menu" \
            --menu "Select an option:" 20 60 10 \
            1 "ComfyUI Installation Options" \
            2 "Select Extensions" \
            3 "Select Models" \
            4 "Custom Package URL" \
            5 "Advanced Configuration" \
            6 "Start Installation" \
            7 "Exit" \
            2>&1 >/dev/tty)
        
        case "$choice" in
            1)
                tui_comfyui_options
                ;;
            2)
                selected_extensions=($(tui_extensions))
                ;;
            3)
                selected_models=($(tui_models))
                ;;
            4)
                tui_custom_package
                ;;
            5)
                tui_advanced_config
                ;;
            6)
                # Confirm installation
                dialog --clear --backtitle "ComfyUI Setup" \
                    --title "Confirm Installation" \
                    --yesno "Ready to install ComfyUI with the selected options. Proceed?" 8 60 \
                    2>&1 >/dev/tty
                
                if [ $? -eq 0 ]; then
                    clear
                    # Perform installation
                    check_dependencies
                    clone_comfyui
                    install_requirements
                    install_extensions "${selected_extensions[@]}"
                    download_models "${selected_models[@]}"
                    download_custom_package
                    create_launch_script
                    
                    # Display completion message
                    dialog --clear --backtitle "ComfyUI Setup" \
                        --title "Installation Complete" \
                        --msgbox "ComfyUI has been installed successfully.\n\nTo start ComfyUI, run:\nbash $COMFYUI_DIR/start_comfyui.sh" 10 60 \
                        2>&1 >/dev/tty
                    
                    # Exit the loop
                    break
                fi
                ;;
            7|"")
                # Exit
                clear
                echo "ComfyUI setup canceled."
                exit 0
                ;;
        esac
    done
}

# Main function to run the script
main() {
    # Check if running as root
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${RED}This script must be run as root. Please use sudo or run as root.${NC}"
        exit 1
    fi
    
    # Check if dialog is installed
    if ! command_exists dialog; then
        echo -e "${YELLOW}Installing dialog package...${NC}"
        apt-get update
        apt-get install -y dialog
    fi
    
    # Run the TUI
    tui_main_menu
    
    # Start ComfyUI if requested
    dialog --clear --backtitle "ComfyUI Setup" \
        --title "Start ComfyUI" \
        --yesno "Do you want to start ComfyUI now?" 8 40 \
        2>&1 >/dev/tty
    
    if [ $? -eq 0 ]; then
        clear
        echo -e "${GREEN}Starting ComfyUI...${NC}"
        bash "$COMFYUI_DIR/start_comfyui.sh"
    else
        clear
        echo -e "${GREEN}Setup complete. You can start ComfyUI later by running:${NC}"
        echo -e "bash $COMFYUI_DIR/start_comfyui.sh"
    fi
}

# Run the main function
main
