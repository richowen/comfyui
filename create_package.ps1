# ComfyUI Package Creator (PowerShell)
Write-Host "`n===============================" -ForegroundColor Cyan
Write-Host " ComfyUI Package Creator" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host ""

# --- Get ComfyUI Root Directory ---
do {
    $comfyuiPath = Read-Host "Enter the full path to your ComfyUI root folder"
    if (-not $comfyuiPath) {
        Write-Host "[ERROR] You must enter a path." -ForegroundColor Red
        $valid = $false
    } elseif (-not (Test-Path $comfyuiPath -PathType Container)) {
        Write-Host "[ERROR] Directory not found: $comfyuiPath" -ForegroundColor Red
        $valid = $false
    } else {
        $valid = $true
    }
} until ($valid)

# --- List Workflows ---
$workflowsDir = Join-Path $comfyuiPath "user\default\workflows"
if (-not (Test-Path $workflowsDir -PathType Container)) {
    Write-Host "[ERROR] Workflows directory not found: $workflowsDir" -ForegroundColor Red
    exit 1
}

$workflowFiles = Get-ChildItem -Path $workflowsDir -Filter "*.json"
if ($workflowFiles.Count -eq 0) {
    Write-Host "[ERROR] No workflow files found in $workflowsDir" -ForegroundColor Red
    exit 1
}

Write-Host "`nAvailable workflows:"
for ($i = 0; $i -lt $workflowFiles.Count; $i++) {
    Write-Host ("  {0}. {1}" -f ($i+1), $workflowFiles[$i].Name)
}

# --- Select Workflow ---
do {
    $selection = Read-Host "Select workflow number"
    $valid = $selection -match '^\d+$' -and $selection -ge 1 -and $selection -le $workflowFiles.Count
    if (-not $valid) {
        Write-Host "[ERROR] Invalid selection." -ForegroundColor Red
    }
} until ($valid)
$workflowPath = $workflowFiles[$selection-1].FullName

# --- Ask for Save Directory ---
do {
    $saveDir = Read-Host "Enter directory to save the package (leave blank for current folder)"
    if (-not $saveDir) {
        $saveDir = (Get-Location).Path
    }
    if (-not (Test-Path $saveDir -PathType Container)) {
        try {
            New-Item -ItemType Directory -Path $saveDir -Force | Out-Null
            $valid = $true
        } catch {
            Write-Host "[ERROR] Could not create directory: $saveDir" -ForegroundColor Red
            $valid = $false
        }
    } else {
        $valid = $true
    }
} until ($valid)

# --- Ask for Output Name ---
$outputName = Read-Host "Enter package name (without .zip, leave blank for workflow name)"
if (-not $outputName) {
    $outputName = [System.IO.Path]::GetFileNameWithoutExtension($workflowPath) + "-package"
}

# --- Ask for Civitai API Key ---
$useCivitaiKey = $null
do {
    $response = Read-Host "Do you want to use a Civitai API key for downloading models? (Y/N)"
    if ($response -imatch '^[yn]$') {
        $useCivitaiKey = $response -ieq 'y'
        $valid = $true
    } else {
        Write-Host "[ERROR] Please enter Y or N." -ForegroundColor Red
        $valid = $false
    }
} until ($valid)

if ($useCivitaiKey) {
    $apiKey = Read-Host "Enter your Civitai API key" -AsSecureString
    if ($apiKey.Length -gt 0) {
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
        $plainApiKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
        
        # Set API key as environment variable
        $env:CIVITAI_API_KEY = $plainApiKey
        Write-Host "Civitai API key set for this session." -ForegroundColor Green
        
        # Save API key in config file for package
        $civitaiConfig = @{
            "api_key" = $plainApiKey
        } | ConvertTo-Json
        
        # The config file will be created in the package directory after it's created
        $global:saveApiKeyToPackage = $true
        $global:apiKeyForPackage = $plainApiKey
    }
}

# --- Create Package ---
Write-Host ""
Write-Host "Creating package from:"
Write-Host "  $workflowPath"
Write-Host "Using ComfyUI at: $comfyuiPath"
Write-Host "Output will be: $saveDir\$outputName.zip"
Write-Host ""

$pythonExe = "python"
$pythonArgs = @(
    "package_creator_windows.py"
    "`"$workflowPath`""
    "--output"
    "`"$outputName`""
    "--comfyui-path"
    "`"$comfyuiPath`""
) -join ' '

$proc = Start-Process -FilePath $pythonExe -ArgumentList $pythonArgs -Wait -NoNewWindow -PassThru

if ($proc.ExitCode -ne 0) {
    Write-Host "`n[FAIL] Package creation failed." -ForegroundColor Red
    exit 1
}

# --- Save API Key to Package ---
if ($global:saveApiKeyToPackage -and $global:apiKeyForPackage) {
    $packageDir = Join-Path (Get-Location) $outputName
    if (Test-Path $packageDir -PathType Container) {
        $civitaiConfigPath = Join-Path $packageDir "civitai_config.json"
        $civitaiConfig = @{
            "api_key" = $global:apiKeyForPackage
        } | ConvertTo-Json
        
        Set-Content -Path $civitaiConfigPath -Value $civitaiConfig
        Write-Host "Saved Civitai API key to package configuration." -ForegroundColor Green
    }
}

# --- Move ZIP to Save Directory ---
$zipPath = Join-Path (Get-Location) "$outputName.zip"
$destZip = Join-Path $saveDir "$outputName.zip"
if (-not (Test-Path $zipPath)) {
    Write-Host "[ERROR] Package ZIP not found: $zipPath" -ForegroundColor Red
    exit 1
}
Move-Item -Force $zipPath $destZip

Write-Host "`n[SUCCESS] Package saved at:"
Write-Host "  $destZip" -ForegroundColor Green
Write-Host ""
Pause
