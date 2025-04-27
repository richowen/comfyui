# ComfyUI Model Downloader

A unified, robust Python script for downloading machine learning models for ComfyUI.

## Features

- Automatically installs dependencies (requests) if missing
- Supports Civitai API key authentication
- Verifies file hashes when provided
- Handles all model types and custom paths
- Non-interactive and suitable for automation
- Provides clear logging and progress reporting
- Falls back to urllib if requests module isn't available

## Usage

### Basic Usage

```bash
python model_downloader.py
```

This will automatically look for a config.json file in the standard locations and process any model downloads defined there.

### Advanced Usage

```bash
python model_downloader.py --comfyui-dir /path/to/comfyui --config /path/to/config.json
```

### Parameters

- `--comfyui-dir`: Path to the ComfyUI installation directory (default: current directory)
- `--config`: Path to a specific config.json file (default: looks in standard locations)

## Config File Format

The downloader uses a JSON configuration file with the following structure:

```json
{
  "external_models": [
    {
      "name": "model_filename.safetensors",
      "type": "checkpoints",
      "url": "https://example.com/path/to/model.safetensors",
      "hash": "md5hash123456789",
      "path": "optional/subdirectory/filename.safetensors"
    },
    {
      "name": "another_model.safetensors",
      "type": "loras",
      "url": "https://civitai.com/api/download/models/12345"
    }
  ]
}
```

### Configuration Fields

- `name`: The filename for the downloaded model
- `type`: The model type (determines the subdirectory, e.g., "checkpoints", "loras", "controlnet", "vae")
- `url`: The download URL for the model
- `hash` (optional): MD5 hash for verification
- `path` (optional): Custom path within the model type directory

## Civitai API Authentication

For downloading models from Civitai that require authentication:

1. Create a file named `civitai_config.json` in the same directory as the script:

```json
{
  "api_key": "your_civitai_api_key_here"
}
```

2. Or set the `CIVITAI_API_KEY` environment variable.

## Integration with comfyui-setup.sh

The `comfyui-setup.sh` script uses this unified downloader for all model downloads, providing a consistent and reliable way to download models from various sources.
