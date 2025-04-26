# ComfyUI Custom Package Example

This is an example of how to structure a custom package for the ComfyUI Setup script.

## Structure

The ZIP file should have the following structure:

```
custom-comfyui-package.zip
├── workflows/
│   └── example-workflow.json
├── custom_nodes/
│   ├── ExampleNode1/
│   │   ├── __init__.py
│   │   └── requirements.txt
│   └── ExampleNode2/
│       ├── __init__.py
│       └── requirements.txt
├── models/
│   ├── checkpoints/
│   │   └── example_model.safetensors
│   ├── loras/
│   │   └── example_lora.safetensors
│   ├── controlnet/
│   │   └── example_controlnet.safetensors
│   └── vae/
│       └── example_vae.safetensors
└── config.json
```

## How to Use

1. Organize your custom nodes, models, and workflows following this structure
2. Create a `config.json` file with your desired settings
3. Zip the entire directory structure (ensure the top-level directories are directly in the zip)
4. Host the zip file somewhere accessible (e.g., GitHub, Dropbox, your server)
5. When running the ComfyUI Setup, enter the URL to your zip file when prompted

## Configuration Options

See the `config.json` file for details on available configuration options.
