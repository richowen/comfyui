#!/usr/bin/env python3
"""
ComfyUI Model Downloader
A unified, robust script for downloading models defined in config.json

Features:
- Automatically installs requests if missing
- Supports Civitai API key authentication
- Verifies file hashes when provided
- Handles all model types and custom paths
- Non-interactive and suitable for automation
- Clear logging and progress reporting
"""
import os
import json
import hashlib
import sys
import tempfile
import shutil
import argparse
from pathlib import Path


def ensure_requests():
    """Ensure requests module is available, auto-install if missing"""
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
            # Fall back to urllib
            print("Will use urllib instead for downloads")
            return False


def get_civitai_api_key():
    """Get Civitai API key from environment variable or config file"""
    # First try environment variable
    api_key = os.environ.get("CIVITAI_API_KEY")
    if api_key:
        return api_key
    
    # Then try config file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "civitai_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                if config.get("api_key"):
                    return config["api_key"]
        except Exception as e:
            print(f"Error reading Civitai config file: {e}")
    
    return None


def verify_hash(file_path, expected_hash):
    """Verify the MD5 hash of a file"""
    print(f"Verifying file integrity for {os.path.basename(file_path)}...")
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    actual_hash = hash_md5.hexdigest()
    if actual_hash == expected_hash:
        print("Hash verification successful")
        return True
    else:
        print(f"Hash verification failed! Expected {expected_hash}, got {actual_hash}")
        return False


def download_with_requests(url, dest_path, display_name):
    """Download file using requests with progress reporting"""
    import requests
    
    headers = {}
    # Add Civitai API key if necessary
    if "civitai.com" in url:
        api_key = get_civitai_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            print("Warning: Civitai API key not found. Some downloads may fail.")
            print("Set CIVITAI_API_KEY environment variable or create civitai_config.json with an api_key field.")
    
    # Create temporary directory for downloading
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, os.path.basename(dest_path))
    
    try:
        # Create directory structure if needed
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Start download
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} from server.")
            if "civitai.com" in url and response.status_code in [401, 403]:
                print("This may be due to missing or invalid Civitai API key.")
            return False
            
        total = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(temp_file, 'wb') as file:
            for data in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                downloaded += len(data)
                file.write(data)
                
                # Display progress
                done = int(50 * downloaded / total) if total > 0 else 50
                sys.stdout.write(f"\r{display_name}: [{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.2f}MB/{total/1024/1024:.2f}MB")
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


def download_with_urllib(url, dest_path, display_name):
    """Fallback download method using urllib"""
    from urllib.request import urlopen, Request
    import ssl
    
    # Create a temporary file for downloading
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, os.path.basename(dest_path))
    
    # Create context to avoid SSL issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Add Civitai API key if needed
    headers = {}
    request = Request(url)
    if "civitai.com" in url:
        api_key = get_civitai_api_key()
        if api_key:
            request.add_header("Authorization", f"Bearer {api_key}")
        else:
            print("Warning: Civitai API key not found. Some downloads may fail.")
            print("Set CIVITAI_API_KEY environment variable or create civitai_config.json with an api_key field.")
    
    try:
        # Create directory structure if needed
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Start download
        with urlopen(request, context=ctx) as response:
            total = int(response.info().get('Content-Length', 0))
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                while True:
                    chunk = response.read(1024*1024)  # 1MB chunks
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    f.write(chunk)
                    
                    # Display progress
                    done = int(50 * downloaded / total) if total > 0 else 50
                    sys.stdout.write(f"\r{display_name}: [{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.2f}MB/{total/1024/1024:.2f}MB")
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


def download_model(url, dest_path, display_name, expected_hash=None):
    """Download a model using the best available method"""
    # Create any necessary directories
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # Check if file already exists and has correct hash
    if os.path.exists(dest_path):
        # If hash is provided, verify existing file
        if expected_hash:
            if verify_hash(dest_path, expected_hash):
                print(f"File already exists with correct hash: {display_name}. Skipping download.")
                return True
            else:
                print(f"Hash mismatch for existing file. Re-downloading {display_name}...")
        else:
            size_mb = os.path.getsize(dest_path) / (1024 * 1024)
            print(f"File already exists ({size_mb:.2f}MB): {display_name}. Skipping download.")
            return True
    
    # Choose download method
    if 'requests' in sys.modules:
        success = download_with_requests(url, dest_path, display_name)
    else:
        success = download_with_urllib(url, dest_path, display_name)
    
    # Verify hash if provided and download succeeded
    if success and expected_hash and not verify_hash(dest_path, expected_hash):
        print(f"Warning: Hash verification failed for {display_name}. The download may be corrupted.")
        return False
    
    return success


def ensure_models_directory(base_dir):
    """Ensure the models directory structure exists"""
    models_dir = os.path.join(base_dir, "models")
    
    # Create if it doesn't exist
    if not os.path.exists(models_dir):
        os.makedirs(models_dir, exist_ok=True)
    
    # Create standard subdirectories if they don't exist
    for subdir in ["checkpoints", "loras", "controlnet", "vae", "embeddings", "insightface", "ultralytics"]:
        os.makedirs(os.path.join(models_dir, subdir), exist_ok=True)
    
    return models_dir


def download_models_from_config(config_path, base_dir=None):
    """Process model downloads from a config file"""
    # Set default base directory if not provided
    if not base_dir:
        base_dir = os.path.dirname(os.path.abspath(config_path))
    
    # Load config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse config file: {e}")
        return False
    except Exception as e:
        print(f"Error loading config file: {e}")
        return False
    
    # Check for models
    if "external_models" not in config or not config["external_models"]:
        print("No external models found in config")
        return True
    
    models = config["external_models"]
    print(f"Found {len(models)} external models to download")
    
    # Ensure models directory exists
    models_dir = ensure_models_directory(base_dir)
    
    # Track results
    success_count = 0
    failure_count = 0
    
    # Process each model
    for i, model in enumerate(models):
        try:
            name = model["name"]
            model_type = model["type"]
            url = model["url"]
            expected_hash = model.get("hash")
            path_component = model.get("path", "")
            
            print(f"\n[{i+1}/{len(models)}] Processing {name}")
            
            # Determine destination path
            dest_dir = os.path.join(models_dir, model_type)
            if path_component:
                path_dir = os.path.dirname(path_component)
                if path_dir:
                    dest_dir = os.path.join(dest_dir, path_dir)
            
            dest_path = os.path.join(dest_dir, os.path.basename(path_component) if path_component else name)
            
            # Download the model
            if download_model(url, dest_path, name, expected_hash):
                success_count += 1
            else:
                failure_count += 1
                print(f"Failed to download {name}. Please download manually:")
                print(f"  URL: {url}")
                print(f"  Save to: {dest_path}")
        except KeyError as e:
            print(f"Error: Missing required field in model definition: {e}")
            failure_count += 1
        except Exception as e:
            print(f"Error processing model {i+1}: {e}")
            failure_count += 1
    
    # Print summary
    print("\nDownload summary:")
    print(f"  Total models: {len(models)}")
    print(f"  Successfully downloaded/found: {success_count}")
    print(f"  Failed: {failure_count}")
    
    return failure_count == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ComfyUI Model Downloader")
    parser.add_argument("--comfyui-dir", help="Path to ComfyUI directory", 
                        default=os.environ.get("COMFYUI_DIR", os.path.dirname(os.path.abspath(__file__))))
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
        print(f"Looked in: {', '.join(locations if 'locations' in locals() else ['--config argument'])}")
        return 1
    
    print(f"Using ComfyUI directory: {comfyui_dir}")
    print(f"Using config file: {config_path}")
    
    # Ensure requests module is available if possible
    ensure_requests()
    
    # Download models from config
    success = download_models_from_config(config_path, comfyui_dir)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
