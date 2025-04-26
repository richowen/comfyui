#!/usr/bin/env python3
"""
ComfyUI Package Creator for Windows
A simplified script to analyze ComfyUI workflows and create packages with dependencies.
Supports external model downloads for large models.
"""

import os
import json
import shutil
import zipfile
import hashlib
import argparse
import sys
from pathlib import Path
from workflow_parser import WorkflowParser

def create_package(workflow_path, output_name=None, comfyui_path=None, size_threshold_gb=2):
    """
    Create a ComfyUI package from a workflow file.
    
    Args:
        workflow_path: Path to the workflow JSON file to analyze
        output_name: Name for the output package (defaults to workflow filename)
        comfyui_path: Path to ComfyUI installation (defaults to auto-detect)
        size_threshold_gb: Size threshold in GB for prompting about large models
    """
    # Validate workflow path
    if not os.path.exists(workflow_path):
        print(f"Error: Workflow file not found: {workflow_path}")
        return False
    
    # Set output name if not provided
    if not output_name:
        output_name = os.path.splitext(os.path.basename(workflow_path))[0] + "-package"
    
    # Detect ComfyUI path if not provided
    if not comfyui_path:
        comfyui_path = auto_detect_comfyui()
        if not comfyui_path:
            print("Error: Could not auto-detect ComfyUI directory. Please specify with --comfyui-path")
            return False
    else:
        if not os.path.exists(comfyui_path):
            print(f"Error: ComfyUI directory not found: {comfyui_path}")
            return False
    
    print(f"Using ComfyUI directory: {comfyui_path}")
    
    # Convert size threshold to bytes
    size_threshold = size_threshold_gb * 1024 * 1024 * 1024
    
    # Parse workflow to find dependencies
    print(f"Analyzing workflow: {workflow_path}")
    parser = WorkflowParser(comfyui_path)
    dependencies = parser.parse_workflow(workflow_path)
    
    # Create package directory structure
    temp_dir = os.path.abspath(output_name)
    if os.path.exists(temp_dir):
        # Check if civitai_config.json exists and save it if it does
        civitai_config_path = os.path.join(temp_dir, "civitai_config.json")
        civitai_config_content = None
        if os.path.exists(civitai_config_path):
            print("Preserving existing civitai_config.json...")
            with open(civitai_config_path, 'r') as f:
                civitai_config_content = f.read()
        
        choice = input(f"Package directory '{temp_dir}' already exists. Overwrite? (y/n): ").lower()
        if choice != 'y':
            print("Aborted.")
            return False
        shutil.rmtree(temp_dir)
        
        # Recreate directory and restore civitai_config.json if it existed
        os.makedirs(temp_dir, exist_ok=True)
        if civitai_config_content:
            with open(civitai_config_path, 'w') as f:
                f.write(civitai_config_content)
    else:
        os.makedirs(temp_dir, exist_ok=True)
        
    # Create directory structure
    print(f"Creating package structure in {temp_dir}")
    os.makedirs(os.path.join(temp_dir, "workflows"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "custom_nodes"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "models", "checkpoints"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "models", "loras"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "models", "controlnet"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "models", "vae"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "models", "embeddings"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "models", "insightface"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "models", "ultralytics"), exist_ok=True)
    
    # Copy workflow file
    print("Copying workflow file...")
    shutil.copy2(workflow_path, os.path.join(temp_dir, "workflows", os.path.basename(workflow_path)))
    
    # Package metadata
    package_config = {
        "name": output_name,
        "description": f"Auto-generated package from {os.path.basename(workflow_path)}",
        "version": "1.0.0",
        "author": "ComfyUI Package Creator",
    }
    
    # Copy custom nodes
    if dependencies['custom_nodes']:
        print(f"Copying {len(dependencies['custom_nodes'])} custom node packages...")
        package_config["installation_order"] = []
        
        for package_name, package_path in dependencies['custom_nodes']:
            try:
                target_path = os.path.join(temp_dir, "custom_nodes", package_name)
                print(f"  - {package_name}")
                copytree_filtered(package_path, target_path)
                package_config["installation_order"].append(f"custom_nodes/{package_name}")
            except Exception as e:
                print(f"    Error copying {package_name}: {e}")
    
    # Process models
    external_models = []
    total_models = sum(len(models) for models in dependencies['models'].values() if models)
    processed_models = 0
    
    if total_models > 0:
        print(f"Processing {total_models} model files...")
        
        for model_type, models in dependencies['models'].items():
            if not models:
                continue
                
            for model_name, model_path in models:
                processed_models += 1
                if not model_path:
                    print(f"  - Warning: Could not locate {model_name}")
                    continue
                
                if not os.path.exists(model_path):
                    print(f"  - Warning: Model file not found: {model_path}")
                    continue
                
                # Check model size
                model_size = os.path.getsize(model_path)
                
                # Determine target directory based on model type
                if model_type == "loras":
                    dest_dir = os.path.join(temp_dir, "models", "loras")
                elif model_type == "controlnet":
                    dest_dir = os.path.join(temp_dir, "models", "controlnet")
                elif model_type == "vae":
                    dest_dir = os.path.join(temp_dir, "models", "vae")
                elif model_type == "embeddings":
                    dest_dir = os.path.join(temp_dir, "models", "embeddings")
                elif model_type == "insightface":
                    dest_dir = os.path.join(temp_dir, "models", "insightface")
                elif model_type == "ultralytics":
                    dest_dir = os.path.join(temp_dir, "models", "ultralytics")
                else:
                    dest_dir = os.path.join(temp_dir, "models", "checkpoints")
                
                # Handle subdirectories in model path
                rel_path = os.path.basename(model_name)
                if '/' in model_name or '\\' in model_name:
                    rel_dir = os.path.dirname(model_name)
                    rel_path = model_name
                    dest_dir = os.path.join(dest_dir, rel_dir)
                    os.makedirs(dest_dir, exist_ok=True)
                
                dest_path = os.path.join(dest_dir, os.path.basename(rel_path))
                
                # Handle large model prompting
                if model_size > size_threshold:
                    size_gb = model_size / (1024 * 1024 * 1024)
                    print(f"\n[{processed_models}/{total_models}] Model '{model_name}' is large ({size_gb:.2f} GB)")
                    print("Options:")
                    print("1. Include in package (not recommended for large files)")
                    print("2. Add download URL to config.json (recommended)")
                    print("3. Skip this model")
                    
                    choice = input("Enter choice (1-3): ")
                    
                    if choice == "1":
                        print(f"  - Copying large model {model_name}...")
                        shutil.copy2(model_path, dest_path)
                    elif choice == "2":
                        # Get model URL
                        print("\nPlease provide a download URL for this model.")
                        print("Suggested sources: Civitai, Hugging Face, or other model repositories")
                        model_url = input("URL: ")
                        
                        if model_url:
                            # Calculate file hash for verification
                            print("  - Calculating hash for verification...")
                            file_hash = calculate_file_hash(model_path)
                            
                            # Add to external models list
                            external_models.append({
                                "name": os.path.basename(model_name),
                                "type": model_type,
                                "path": rel_path if '/' in model_name or '\\' in model_name else None,
                                "url": model_url,
                                "hash": file_hash,
                                "size": model_size
                            })
                            print(f"  - Added {model_name} as external download")
                        else:
                            print("  - No URL provided, skipping model")
                    else:
                        print(f"  - Skipping model {model_name}")
                else:
                    # Regular-sized model, include it directly
                    print(f"  - Copying model {model_name}...")
                    shutil.copy2(model_path, dest_path)
    
    # Create config.json
    print("Creating config.json...")
    config_path = os.path.join(temp_dir, "config.json")
    
    # Add external models if any
    if external_models:
        package_config["external_models"] = external_models
        # Add installation script information
        package_config["download_script"] = "download_models.py"
    
    # Add placeholder settings
    package_config["gpu_settings"] = {
        "vram_optimize": True,
        "precision": "fp16",
        "xformers": True
    }
    
    # Save config
    with open(config_path, 'w') as f:
        json.dump(package_config, f, indent=2)
    
    # Copy download script if we have external models
    if external_models:
        print("Copying model download script...")
        source_download_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_models.py")
        if os.path.exists(source_download_script):
            download_script_path = os.path.join(temp_dir, "download_models.py")
            shutil.copy2(source_download_script, download_script_path)
            print("  - Added download_models.py to package")
        else:
            print("Warning: download_models.py not found in current directory. Model downloading may not work.")
    
    # Create zip file
    print("Creating ZIP archive...")
    zip_path = os.path.join(os.getcwd(), f"{output_name}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    print(f"\nPackage created successfully in {zip_path}")
    
    # Clean up the unzipped package directory to avoid leaving it behind
    print(f"Cleaning up temporary directory...")
    shutil.rmtree(temp_dir)
    
    return True

def auto_detect_comfyui():
    """Try to auto-detect a ComfyUI installation directory."""
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    
    # Check if current directory might be ComfyUI
    if is_comfyui_directory(current_dir):
        return current_dir
        
    # Check if parent directory might contain ComfyUI
    try:
        for entry in os.scandir(parent_dir):
            if entry.is_dir() and is_comfyui_directory(entry.path):
                return entry.path
    except:
        pass
        
    # Check common locations
    common_locations = []
    
    # Add Desktop and Documents folders
    if os.name == 'nt':  # Windows
        home = os.path.expanduser("~")
        common_locations.extend([
            os.path.join(home, "Desktop", "ComfyUI"),
            os.path.join(home, "Documents", "ComfyUI"),
            os.path.join(home, "Downloads", "ComfyUI")
        ])
    
    for location in common_locations:
        if os.path.isdir(location) and is_comfyui_directory(location):
            return location
            
    return None

def is_comfyui_directory(directory):
    """Check if a directory looks like a ComfyUI installation."""
    if not os.path.isdir(directory):
        return False
        
    # Check for common ComfyUI directories and files
    comfy_indicators = ['comfy', 'web', 'models', 'custom_nodes']
    
    try:
        dir_contents = os.listdir(directory)
        matches = sum(1 for indicator in comfy_indicators if any(item.lower() == indicator.lower() for item in dir_contents))
        return matches >= 2  # If at least 2 indicators match, it's likely ComfyUI
    except:
        return False

def copytree_filtered(src, dst):
    """
    Custom directory copy function that skips problematic folders like .git
    
    Args:
        src: Source directory
        dst: Destination directory
    """
    os.makedirs(dst, exist_ok=True)
    
    # Skip problematic directories
    skip_dirs = ['.git', '.github', '__pycache__', '.venv', 'venv', '.egg-info']
    
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        
        if os.path.isdir(s):
            if item not in skip_dirs:
                try:
                    copytree_filtered(s, d)
                except Exception as e:
                    print(f"Warning: Could not copy {s}: {e}")
        else:
            try:
                shutil.copy2(s, d)
            except Exception as e:
                print(f"Warning: Could not copy {s}: {e}")

def calculate_file_hash(file_path):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def main():
    parser = argparse.ArgumentParser(description='ComfyUI Package Creator for Windows')
    parser.add_argument('workflow', help='Path to workflow JSON file')
    parser.add_argument('--output', '-o', help='Output package name (default: based on workflow name)')
    parser.add_argument('--comfyui-path', '-c', help='Path to ComfyUI installation (default: auto-detect)')
    parser.add_argument('--size-threshold', '-s', type=float, default=2, 
                        help='Size threshold in GB for large model prompting (default: 2)')
    
    args = parser.parse_args()
    
    try:
        create_package(args.workflow, args.output, args.comfyui_path, args.size_threshold)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
