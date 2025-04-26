# ComfyUI Model Downloader

This utility helps download external models specified in your `config.json` file for ComfyUI packages.

## Configuration Files

### `config.json`

The main package configuration file that includes a section for external models to download:

```json
{
  "package_name": "Your Package Name",
  "package_description": "Package description",
  "author": "Your Name",
  "version": "1.0.0",
  "external_models": [
    {
      "name": "model-name.safetensors",
      "type": "checkpoints",
      "url": "https://example.com/path/to/model.safetensors",
      "hash": "optional-md5-hash-for-verification"
    }
  ]
}
```

### `civitai_config.json`

This file stores your Civitai API key for downloading models from Civitai:

```json
{
  "api_key": "YOUR_CIVITAI_API_KEY_HERE"
}
```

## API Key Configuration

When using the `create_package.ps1` script, you will be prompted if you want to use a Civitai API key. If you choose to use one:

1. The API key will be saved to `civitai_config.json` in your package directory
2. The same API key will also be saved to `civitai_config.json` in the current working directory
3. This allows the downloader to access the API key both when creating packages and when running locally

## Usage

Run the model downloader with:

```
python download_models.py
```

The script will:
1. Check for `config.json` in the current directory
2. Read the `external_models` section
3. Download each model to the appropriate directory under `models/`
4. Verify file hashes if provided

## Civitai Downloads

When downloading from Civitai, the script will:
1. Look for a Civitai API key in the environment variable `CIVITAI_API_KEY`
2. If not found, check for `civitai_config.json` in the current directory
3. If neither is available, prompt you to download the model manually

## Troubleshooting

- If you encounter SyntaxError: "unterminated f-string literal", update to the latest version of the script
- For download failures, check your network connection and API key configuration
- The script creates temporary directories during downloads to ensure integrity
