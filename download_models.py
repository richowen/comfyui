#!/usr/bin/env python3
"""
ComfyUI Package Model Downloader
Downloads external models specified in config.json
"""
import os
import json
import hashlib
import sys
import tempfile
import shutil
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("requests module not found, trying urllib")

MODEL_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

def install_requests_if_needed():
    if not REQUESTS_AVAILABLE:
        print("The requests module is required for downloading. Would you like to install it?")
        choice = input("(y/n): ").lower()
        if choice == 'y':
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
                print("requests installed successfully")
                global requests
                import requests
                return True
            except Exception as e:
                print(f"Error installing requests: {e}")
                return False
        else:
            return False
    return True

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
            print(f"Error reading config file: {e}")
    
    return None

def download_with_requests(url, path, display_name):
    import requests
    headers = {}
    
    # Add Civitai API key if downloading from Civitai
    if "civitai.com" in url:
        api_key = get_civitai_api_key()
        if not api_key:
            print("Civitai API key not found. Set CIVITAI_API_KEY environment variable or create civitai_config.json with an api_key field.")
            print(f"Please download manually from {url} and place in {os.path.dirname(path)}")
            return False
        headers["Authorization"] = f"Bearer {api_key}"
    
    resp = requests.get(url, headers=headers, stream=True)
    total = int(resp.headers.get('content-length', 0))
    downloaded = 0
    
    # Create a temporary file for downloading
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, os.path.basename(path))
    
    try:
        with open(temp_file, 'wb') as file:
            for data in resp.iter_content(chunk_size=1024*1024):
                downloaded += len(data)
                file.write(data)
                
                # Display progress
                done = int(50 * downloaded / total) if total > 0 else 50
                sys.stdout.write(f"{display_name}: [{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.2f}MB/{total/1024/1024:.2f}MB")
                sys.stdout.flush()
        
        # Move from temp to final destination
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.move(temp_file, path)
        sys.stdout.write(f"{display_name}: Download complete{' ' * 50}\n")
    finally:
        # Clean up temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)

def download_with_urllib(url, path, display_name):
    from urllib.request import urlopen, Request
    import ssl
    
    # Create a temporary file for downloading
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, os.path.basename(path))
    
    # Create context to avoid SSL issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Add Civitai API key if needed
    if "civitai.com" in url:
        api_key = get_civitai_api_key()
        if not api_key:
            print("Civitai API key not found. Set CIVITAI_API_KEY environment variable or create civitai_config.json with an api_key field.")
            print(f"Please download manually from {url} and place in {os.path.dirname(path)}")
            return False
        request = Request(url)
        request.add_header("Authorization", f"Bearer {api_key}")
        try:
            with urlopen(request, context=ctx) as response:
                total = int(response.info().get('Content-Length', 0))
                downloaded = 0
                
                with open(temp_file, 'wb') as f:
                    while True:
                        chunk = response.read(1024*1024)
                        if not chunk:
                            break
                        downloaded += len(chunk)
                        f.write(chunk)
                        
                        # Display progress
                        done = int(50 * downloaded / total) if total > 0 else 50
                        sys.stdout.write(f"{display_name}: [{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.2f}MB/{total/1024/1024:.2f}MB")
                        sys.stdout.flush()
            
            # Move from temp to final destination
            os.makedirs(os.path.dirname(path), exist_ok=True)
            shutil.move(temp_file, path)
            sys.stdout.write(f"{display_name}: Download complete{' ' * 50}\n")
            return True
        except Exception as e:
            print(f"Error downloading with API key: {e}")
            return False
    
    # Regular download without API key
    try:
        with urlopen(url, context=ctx) as response:
            total = int(response.info().get('Content-Length', 0))
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                while True:
                    chunk = response.read(1024*1024)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    f.write(chunk)
                    
                    # Display progress
                    done = int(50 * downloaded / total) if total > 0 else 50
                    sys.stdout.write(f"{display_name}: [{'=' * done}{' ' * (50-done)}] {downloaded/1024/1024:.2f}MB/{total/1024/1024:.2f}MB")
                    sys.stdout.flush()
        
        # Move from temp to final destination
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.move(temp_file, path)
        sys.stdout.write(f"{display_name}: Download complete{' ' * 50}\n")
    finally:
        # Clean up temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)

def verify_hash(file_path, expected_hash):
    """Verify the MD5 hash of a file."""
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

def main():
    # Check if config exists
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if not os.path.exists(config_path):
        print("Error: config.json not found")
        return
    
    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    if "external_models" not in config or not config["external_models"]:
        print("No external models to download")
        return
    
    # Ensure requests is available
    if not REQUESTS_AVAILABLE and not install_requests_if_needed():
        print("Will use urllib instead of requests")
    
    # Process each model
    models = config["external_models"]
    print(f"Found {len(models)} external models to download")
    
    for i, model in enumerate(models):
        name = model["name"]
        model_type = model["type"]
        url = model["url"]
        expected_hash = model.get("hash")
        path_component = model.get("path")
        
        print(f"\n[{i+1}/{len(models)}] Processing {name}")
        
        # Determine destination path
        dest_dir = os.path.join(MODEL_ROOT, model_type)
        if path_component:
            dest_dir = os.path.join(dest_dir, os.path.dirname(path_component))
        
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, name)
        
        # Check if model already exists and has correct hash
        if os.path.exists(dest_path) and expected_hash:
            if verify_hash(dest_path, expected_hash):
                print(f"{name} already exists with correct hash. Skipping download.")
                continue
            else:
                print(f"Hash mismatch for existing file. Re-downloading {name}...")
        
        # Download the model
        print(f"Downloading {name} from {url}")
        try:
            if 'requests' in sys.modules:
                download_with_requests(url, dest_path, name)
            else:
                download_with_urllib(url, dest_path, name)
                
            # Verify hash if provided
            if expected_hash and not verify_hash(dest_path, expected_hash):
                print(f"Warning: Hash verification failed for {name}. The download may be corrupted.")
        except Exception as e:
            print(f"Error downloading {name}: {e}")
            print(f"Please download manually from {url} and place in {dest_dir}")
    
    print("\nDownload process complete.")
    print("If any downloads failed, please download them manually from the URLs in config.json")

if __name__ == "__main__":
    main()
