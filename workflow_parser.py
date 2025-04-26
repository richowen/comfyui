#!/usr/bin/env python3
"""
ComfyUI Workflow Parser
Utility to extract model and custom node dependencies from ComfyUI workflow files.
"""

import json
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

class WorkflowParser:
    def __init__(self, comfyui_path: str):
        """
        Initialize the workflow parser with the root ComfyUI directory.
        
        Args:
            comfyui_path: Path to the ComfyUI installation
        """
        self.comfyui_path = os.path.abspath(comfyui_path)
        self.model_paths = self._load_model_paths()
        self.custom_node_packages = self._get_custom_node_packages()
        
    def _load_model_paths(self) -> Dict[str, List[str]]:
        """
        Load model paths from ComfyUI's default locations and extra_model_paths.yaml if it exists.
        
        Returns:
            Dictionary mapping model types to lists of possible paths
        """
        # Default ComfyUI model paths
        model_paths = {
            "checkpoints": [os.path.join(self.comfyui_path, "models", "checkpoints")],
            "vae": [os.path.join(self.comfyui_path, "models", "vae")],
            "loras": [os.path.join(self.comfyui_path, "models", "loras")],
            "embeddings": [os.path.join(self.comfyui_path, "models", "embeddings")],
            "controlnet": [os.path.join(self.comfyui_path, "models", "controlnet")],
            "clip": [os.path.join(self.comfyui_path, "models", "clip")],
            "clip_vision": [os.path.join(self.comfyui_path, "models", "clip_vision")],
            "upscale_models": [os.path.join(self.comfyui_path, "models", "upscale_models")],
            "facerestore_models": [os.path.join(self.comfyui_path, "models", "facerestore_models")],
            "insightface": [os.path.join(self.comfyui_path, "models", "insightface")],
            "ultralytics": [os.path.join(self.comfyui_path, "models", "ultralytics")],
            "unet": [os.path.join(self.comfyui_path, "models", "unet")],
            "diffusion_models": [os.path.join(self.comfyui_path, "models", "diffusion_models")],
            "text_encoders": [os.path.join(self.comfyui_path, "models", "text_encoders")],
            "LLM": [os.path.join(self.comfyui_path, "models", "LLM")],
            "configs": [os.path.join(self.comfyui_path, "models", "configs")],
            "vae_approx": [os.path.join(self.comfyui_path, "models", "vae_approx")],
            "sams": [os.path.join(self.comfyui_path, "models", "sams")],
            "gligen": [os.path.join(self.comfyui_path, "models", "gligen")],
            "hypernetworks": [os.path.join(self.comfyui_path, "models", "hypernetworks")],
        }
        
        # Check for extra_model_paths.yaml
        extra_paths_file = os.path.join(self.comfyui_path, "extra_model_paths.yaml")
        if os.path.exists(extra_paths_file):
            try:
                with open(extra_paths_file, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f)
                
                if yaml_data:
                    for ui_name, ui_config in yaml_data.items():
                        if not isinstance(ui_config, dict) or 'base_path' not in ui_config:
                            continue
                            
                        base_path = ui_config['base_path']
                        
                        # Process each model type in the UI config
                        for model_type, rel_path in ui_config.items():
                            if model_type in ('base_path', 'is_default'):
                                continue
                                
                            # Handle multi-line paths (pipe character in YAML)
                            if isinstance(rel_path, str):
                                if '\n' in rel_path:
                                    paths = [p.strip() for p in rel_path.split('\n') if p.strip()]
                                else:
                                    paths = [rel_path.strip()]
                                    
                                for path in paths:
                                    full_path = os.path.join(base_path, path)
                                    
                                    # Add to our model paths
                                    model_type_normalized = model_type.lower()
                                    if model_type_normalized not in model_paths:
                                        model_paths[model_type_normalized] = []
                                    
                                    model_paths[model_type_normalized].append(full_path)
            except Exception as e:
                print(f"Error loading extra_model_paths.yaml: {e}")
                
        return model_paths
    
    def _get_custom_node_packages(self) -> Dict[str, str]:
        """
        Get a mapping of custom node package identifiers to their paths.
        
        Returns:
            Dictionary mapping custom node IDs to their file paths
        """
        custom_nodes_dir = os.path.join(self.comfyui_path, "custom_nodes")
        custom_node_packages = {}
        
        if os.path.exists(custom_nodes_dir):
            for node_package in os.listdir(custom_nodes_dir):
                package_path = os.path.join(custom_nodes_dir, node_package)
                if os.path.isdir(package_path):
                    # Various ways custom nodes identify themselves
                    # 1. Node ID in the format 'author/package_name' 
                    custom_node_packages[node_package.lower()] = package_path
                    
                    # 2. Try to find IDs in the Python files
                    for root, _, files in os.walk(package_path):
                        for file in files:
                            if file.endswith('.py'):
                                try:
                                    file_path = os.path.join(root, file)
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        
                                    # Look for common patterns for node IDs
                                    # Pattern: NODE_CLASS_MAPPINGS, id_mapping, aux_id, etc.
                                    id_patterns = [
                                        r'cnr_id["\s\']+:\s*["\']([^"\']+)["\']',
                                        r'aux_id["\s\']+:\s*["\']([^"\']+)["\']',
                                        r'id_mapping\s*=\s*[\'"]([\w\d_\-\/]+)[\'"]',
                                        r'ID\s*=\s*[\'"]([\w\d_\-\/]+)[\'"]',
                                    ]
                                    
                                    for pattern in id_patterns:
                                        matches = re.findall(pattern, content)
                                        for match in matches:
                                            custom_node_packages[match.lower()] = package_path
                                except:
                                    pass  # Ignore errors in reading files
        
        return custom_node_packages
    
    def parse_workflow(self, workflow_path: str) -> Dict[str, List[str]]:
        """
        Parse a workflow file to extract model and custom node dependencies.
        
        Args:
            workflow_path: Path to the workflow JSON file
            
        Returns:
            Dictionary with parsed dependencies:
            {
                'custom_nodes': [(package_id, package_path), ...],
                'models': {
                    'checkpoints': [(model_name, model_path), ...],
                    'vae': [...],
                    ...
                }
            }
        """
        result = {
            'custom_nodes': [],
            'models': {}
        }
        
        # Initialize model types
        for model_type in self.model_paths.keys():
            result['models'][model_type] = []
        
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            if not isinstance(workflow, dict) or 'nodes' not in workflow:
                return result
                
            # Track custom node IDs
            custom_node_ids = set()
            
            # Process each node
            for node in workflow['nodes']:
                if not isinstance(node, dict):
                    continue
                
                # Extract custom node package ID
                if 'properties' in node and isinstance(node['properties'], dict):
                    props = node['properties']
                    
                    # Check for custom node identifier
                    node_id = None
                    if 'cnr_id' in props:
                        node_id = props['cnr_id']
                    elif 'aux_id' in props:
                        node_id = props['aux_id']
                    elif 'Node name for S&R' in props:
                        node_id = props['Node name for S&R']
                        
                    if node_id and node_id.lower() not in custom_node_ids:
                        custom_node_ids.add(node_id.lower())
                
                # Extract model paths from widgets
                if 'widgets_values' in node and isinstance(node['widgets_values'], list):
                    values = node['widgets_values']
                    
                    # Check node type to determine model type
                    node_type = node.get('type', '').lower()
                    
                    model_type = self._guess_model_type(node_type)
                    
                    # Check if any widget value looks like a model path
                    for value in values:
                        if not isinstance(value, str) or not value:
                            continue
                            
                        # Skip values that are clearly not model files
                        if value in ('randomize', 'true', 'false', 'enable', 'disable'):
                            continue
                            
                        # If it has a file extension that looks like a model, add it
                        extensions = ('.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.onnx')
                        if any(value.endswith(ext) for ext in extensions):
                            # If we didn't guess the model type from the node, try from the extension
                            if not model_type:
                                model_type = self._guess_model_type_from_filename(value)
                            
                            if model_type:
                                result['models'][model_type].append(value)
            
            # Resolve custom node paths
            resolved_nodes = set()
            for node_id in custom_node_ids:
                # Check for direct match
                if node_id in self.custom_node_packages:
                    path = self.custom_node_packages[node_id]
                    package_name = os.path.basename(path)
                    resolved_nodes.add((package_name, path))
                else:
                    # Check for partial matches
                    for package_id, path in self.custom_node_packages.items():
                        if node_id in package_id or package_id in node_id:
                            package_name = os.path.basename(path)
                            resolved_nodes.add((package_name, path))
                
            result['custom_nodes'] = list(resolved_nodes)
            
            # Resolve model paths
            for model_type in result['models']:
                resolved_models = []
                for model_name in result['models'][model_type]:
                    resolved_path = self._resolve_model_path(model_type, model_name)
                    if resolved_path:
                        resolved_models.append((model_name, resolved_path))
                        
                result['models'][model_type] = resolved_models
            
            return result
            
        except Exception as e:
            print(f"Error parsing workflow: {e}")
            return result
    
    def _guess_model_type(self, node_type: str) -> Optional[str]:
        """
        Guess the model type based on the node type.
        
        Args:
            node_type: The type of the node
            
        Returns:
            The guessed model type or None
        """
        node_type = node_type.lower()
        
        # Map node types to model types
        type_mapping = {
            'checkpoint': 'checkpoints',
            'checkpointloader': 'checkpoints', 
            'load': 'checkpoints',
            'vae': 'vae',
            'vaeloader': 'vae',
            'clip': 'clip',
            'lora': 'loras',
            'loraloader': 'loras',
            'embedding': 'embeddings',
            'textualinversion': 'embeddings',
            'hypernetwork': 'hypernetworks',
            'controlnet': 'controlnet',
            'upscale': 'upscale_models',
            'facedetection': 'insightface',
            'facerestore': 'facerestore_models',
            'ultralytics': 'ultralytics',
            'llm': 'LLM',
            'sam': 'sams',
        }
        
        for key, value in type_mapping.items():
            if key in node_type:
                return value
                
        return None
    
    def _guess_model_type_from_filename(self, filename: str) -> Optional[str]:
        """
        Guess the model type based on the filename.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            The guessed model type or None
        """
        filename = filename.lower()
        
        # Check extensions
        if filename.endswith('.safetensors') or filename.endswith('.ckpt'):
            # Try to determine by filename patterns
            if 'lora' in filename:
                return 'loras'
            elif 'vae' in filename:
                return 'vae'
            elif 'embedding' in filename or 'embed' in filename:
                return 'embeddings'
            elif 'controlnet' in filename or 'control_' in filename:
                return 'controlnet'
            else:
                return 'checkpoints'  # Default for .safetensors/.ckpt
        
        # Check other extensions
        elif filename.endswith('.pt') or filename.endswith('.pth'):
            if 'sam' in filename:
                return 'sams'
            elif 'gfpgan' in filename or 'codeformer' in filename or 'face' in filename:
                return 'facerestore_models'
            elif 'upscale' in filename or 'esrgan' in filename:
                return 'upscale_models'
            
        elif filename.endswith('.onnx'):
            if 'inswapper' in filename:
                return 'insightface'
                
        # When in doubt, default to checkpoints
        return 'checkpoints'
    
    def _resolve_model_path(self, model_type: str, model_name: str) -> Optional[str]:
        """
        Resolve a model name to its actual file path.
        
        Args:
            model_type: Type of the model (checkpoints, vae, etc.)
            model_name: Name of the model file
            
        Returns:
            Full path to the model file or None if not found
        """
        if model_type not in self.model_paths:
            return None
            
        # Check all possible paths for this model type
        for base_path in self.model_paths[model_type]:
            # Handle potential subfolder in the model name
            model_path = os.path.join(base_path, model_name)
            if os.path.exists(model_path):
                return model_path
                
            # Check if the file exists without subfolders
            if os.path.sep in model_name:
                filename = os.path.basename(model_name)
                direct_path = os.path.join(base_path, filename)
                if os.path.exists(direct_path):
                    return direct_path
        
        # If still not found, try a more exhaustive search in the model directories
        for base_path in self.model_paths[model_type]:
            for root, _, files in os.walk(base_path):
                # Check exact filename
                filename = os.path.basename(model_name)
                if filename in files:
                    return os.path.join(root, filename)
                    
                # Check case-insensitive on Windows
                if os.name == 'nt':  # Windows
                    for file in files:
                        if file.lower() == filename.lower():
                            return os.path.join(root, file)
        
        return None

if __name__ == "__main__":
    # Simple example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python workflow_parser.py <comfyui_path> <workflow_path>")
        sys.exit(1)
        
    comfyui_path = sys.argv[1]
    workflow_path = sys.argv[2]
    
    parser = WorkflowParser(comfyui_path)
    dependencies = parser.parse_workflow(workflow_path)
    
    print("\nCustom Nodes:")
    for package_name, path in dependencies['custom_nodes']:
        print(f"  - {package_name}: {path}")
        
    print("\nModels:")
    for model_type, models in dependencies['models'].items():
        if models:
            print(f"  {model_type}:")
            for model_name, model_path in models:
                print(f"    - {model_name}: {model_path}")
