#!/usr/bin/env python3
"""
Helper script for ComfyUI Setup
This script helps download models when the regular download_models.py fails
"""
import argparse
import os
import json
import sys
import tempfile
import shutil
from pathlib import Path

def ensure_requests():
    """Ensure requests module is installed"""
    try:
        import requests
        return True
    except ImportError:
        print("The requests module is required but not found.")
        print("Installing requests...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            import requests
            print("Successfully installed requests.")
            return True
        except Exception as e:
            print(f"Error installing requests: {e}")
            return False

def fix_models_directory(comfyui_dir):
    """
    Locate and use the proper models directory structure
    Returns the models root directory
    """
    # Try standard location first
    model_root = os.path.join(comfyui_dir, "models")
    
    # Create if it doesn't exist
    if not os.path.exists(model_root):
        os.makedirs(model_root, exist_ok=True)
        for subdir in ["checkpoints", "loras", "controlnet", "vae"]:
            os.makedirs(os.path.join(model_root, subdir), exist_ok=True)
    
    return model_root

def download_model(url, dest_path, display_name):
    """Download a model file with progress indication"""
    import requests
    
    print(f"Downloading {display_name} from {url}")
    print(f"Destination: {dest_path}")
    
    # Create a temporary file for downloading
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, os.path.basename(dest_path))
    
    try:
        # Create directory structure if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Start download
        response = requests.get(url, stream=True)
        total = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(temp_file, 'wb') as file:
            for data in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                downloaded += len(data)
                file.write(data)
                
                # Display progress
                done = int(50 * downloaded / total) if total > 0 else 50
                sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.2f}MB/{total/1024/1024:.2f}MB")
                sys.stdout.flush()
        
        # Move from temp to final destination
        shutil.move(temp_file, dest_path)
        print(f"\nDownload complete: {display_name}")
        return True
    except Exception as e:
        print(f"\nError downloading {display_name}: {e}")
        return False
    finally:
        # Clean up temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Helper script for ComfyUI Setup")
    parser.add_argument("--comfyui-dir", help="Path to ComfyUI directory", default=os.environ.get("COMFYUI_DIR", os.path.expanduser("~/ComfyUI")))
    parser.add_argument("--config", help="Path to config.json file", default=None)
    args = parser.parse_args()
    
    comfyui_dir = args.comfyui_dir
    config_path = args.config
    
    # If config path not provided, look in standard locations
    if not config_path:
        locations = [
            os.path.join(comfyui_dir, "config.json"),
            os.path.join(comfyui_dir, "package_config.json"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        ]
        
        for loc in locations:
            if os.path.exists(loc):
                config_path = loc
                break
    
    if not config_path or not os.path.exists(config_path):
        print("Error: Cannot find config.json file.")
        print(f"Looked in: {', '.join(locations)}")
        return 1
    
    print(f"Using ComfyUI directory: {comfyui_dir}")
    print(f"Using config file: {config_path}")
    
    # Ensure requests module is available
    if not ensure_requests():
        print("Error: Failed to install required dependencies.")
        return 1
    
    # Load config
    with open(config_path, 'r') as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse config.json: {e}")
            return 1
    
    # Find models section
    if "external_models" not in config or not config["external_models"]:
        print("No external models found in config.json")
        return 0
    
    models = config["external_models"]
    print(f"Found {len(models)} external models to download")
    
    # Fix models directory
    model_root = fix_models_directory(comfyui_dir)
    print(f"Using models directory: {model_root}")
    
    # Process each model
    success_count = 0
    failure_count = 0
    
    for i, model in enumerate(models):
        name = model["name"]
        model_type = model["type"]
        url = model["url"]
        path_component = model.get("path", "")
        
        # Determine destination path
        dest_dir = os.path.join(model_root, model_type)
        if path_component:
            path_dir = os.path.dirname(path_component)
            if path_dir:
                dest_dir = os.path.join(dest_dir, path_dir)
        
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, name)
        
        # Download the model
        print(f"\n[{i+1}/{len(models)}] Processing {name}")
        
        if os.path.exists(dest_path):
            size_mb = os.path.getsize(dest_path) / (1024 * 1024)
            print(f"File already exists ({size_mb:.2f}MB). Skipping download.")
            success_count += 1
            continue
        
        if download_model(url, dest_path, name):
            success_count += 1
        else:
            failure_count += 1
            print(f"Failed to download {name}. Please download manually:")
            print(f"  URL: {url}")
            print(f"  Save to: {dest_path}")
    
    print("\nDownload summary:")
    print(f"  Total models: {len(models)}")
    print(f"  Successfully downloaded/found: {success_count}")
    print(f"  Failed: {failure_count}")
    
    if failure_count > 0:
        print("\nSome downloads failed. Please check the messages above for manual download instructions.")
        return 1
    else:
        print("\nAll models downloaded successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
