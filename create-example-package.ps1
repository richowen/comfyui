# ComfyUI Example Package Creator
# This script creates a ZIP file from the package-example directory

# Check for the existence of the package-example directory
if (-not (Test-Path -Path "package-example" -PathType Container)) {
    Write-Error "The package-example directory does not exist. Make sure you're running this script from the correct directory."
    exit 1
}

# Define the output ZIP file name
$outputZip = "custom-comfyui-package.zip"

# Remove existing ZIP file if it exists
if (Test-Path -Path $outputZip) {
    Remove-Item -Path $outputZip -Force
    Write-Host "Removed existing $outputZip file." -ForegroundColor Yellow
}

# Create the ZIP file
Write-Host "Creating ZIP file from package-example directory..." -ForegroundColor Cyan

# Method 1: Using Compress-Archive (PowerShell 5.0+)
try {
    Compress-Archive -Path "package-example\*" -DestinationPath $outputZip
    Write-Host "ZIP file created successfully using Compress-Archive." -ForegroundColor Green
}
catch {
    Write-Warning "Failed to create ZIP using Compress-Archive. Trying alternative method..."
    
    # Method 2: Using .NET IO.Compression (for compatibility)
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory("$PWD\package-example", "$PWD\$outputZip")
        Write-Host "ZIP file created successfully using .NET IO.Compression." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to create ZIP file using both methods. Error: $_"
        exit 1
    }
}

# Verify the ZIP file was created
if (Test-Path -Path $outputZip) {
    $zipSize = (Get-Item -Path $outputZip).Length / 1KB
    Write-Host "Created $outputZip (Size: $([math]::Round($zipSize, 2)) KB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "To test this package with the ComfyUI setup script:" -ForegroundColor Yellow
    Write-Host "1. Host this ZIP file somewhere accessible (e.g., GitHub, Dropbox, your server)" -ForegroundColor Yellow
    Write-Host "2. When running the setup script, provide the URL to this ZIP file" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "For local testing, you can use:" -ForegroundColor Yellow
    Write-Host "   file://$(Resolve-Path $outputZip)" -ForegroundColor Gray
    Write-Host "Or if using a local web server:" -ForegroundColor Yellow
    Write-Host "   http://localhost:8000/$outputZip" -ForegroundColor Gray
} else {
    Write-Error "Failed to create $outputZip for unknown reasons."
    exit 1
}
