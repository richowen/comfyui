# ComfyUI RunPod Setup

This repository contains scripts to easily deploy and configure ComfyUI on RunPod instances. The setup provides a text-based user interface (TUI) for selecting various options, including custom nodes, models, and configuration settings.

## Base Image

This setup is designed to work with the following RunPod image:
```
runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04
```

## Quick Start

To set up ComfyUI on your RunPod instance, run the following command:

```bash
sudo bash -c "$(curl -sSL https://raw.githubusercontent.com/richowen/comfyui/main/bootstrap.sh)"
```

This one-liner will:
1. Download the bootstrap script
2. Execute the script, which in turn downloads and runs the main setup
3. Present you with a TUI to configure your ComfyUI installation

## Features

- **Easy Installation**: One-liner command to start the setup process
- **Customizable**: TUI for selecting various options
- **Modular**: Install only the components you need
- **Custom Package Support**: Upload your own package with workflows, nodes, and models

## TUI Options

The setup script presents a TUI with the following options:

1. **ComfyUI Installation Options**
   - Select ComfyUI branch (master, main, dev)
   - Configure the port for the web UI

2. **Extensions Selection**
   - ComfyUI-Manager
   - ControlNet
   - ReActor
   - Impact Pack
   - Efficiency Nodes
   - Custom extension URL

3. **Models Selection**
   - Stable Diffusion 1.5
   - Stable Diffusion XL
   - SDXL VAE
   - ControlNet models
   - Custom model URL

4. **Custom Package URL**
   - URL to your custom zip package containing workflows, nodes, and models

5. **Advanced Configuration**
   - CUDA visible devices
   - Other advanced settings

## Creating a Custom Package

You can create your own custom package with workflows, nodes, and models. The package should be a zip file with the following structure:

```
custom-comfyui-package.zip
├── workflows/
│   └── *.json
├── custom_nodes/
│   └── [node_directories]/
├── models/
│   ├── checkpoints/
│   ├── loras/
│   ├── controlnet/
│   └── vae/
└── config.json (optional)
```

Upload this zip file to a web-accessible location (e.g., GitHub, Dropbox, your own server), and provide the URL when prompted during setup.

## Example config.json (Optional)

```json
{
  "dependencies": [
    "pip:transformers==4.30.2",
    "pip:opencv-python==4.7.0.72"
  ],
  "gpu_settings": {
    "vram_optimize": true
  }
}
```

## After Installation

After installation, the script creates a convenient launch script. You can start ComfyUI with:

```bash
bash ~/ComfyUI/start_comfyui.sh
```

## Requirements

- RunPod instance with the specified base image
- Root access to install dependencies
- Internet connection to download packages and models

## Troubleshooting

If you encounter any issues during installation:

1. Make sure you're running the script as root (using sudo)
2. Check that your RunPod instance has internet connectivity
3. Ensure you have enough disk space for the models you're downloading

## License

This project is open source and available under the MIT License.
