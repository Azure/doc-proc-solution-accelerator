#!/usr/bin/env pwsh

# Doc Processing Solution - Auto-Setup Pipeline Script
# This script fetches configuration from a deployed Azure resource group
# and runs the setup-pipeline.py script with the correct parameters

# Enable strict mode for better error handling
$ErrorActionPreference = "Stop"

# Default values
$ResourceGroup = ""

# Color codes for output (ANSI escape sequences)
$Colors = @{
    RED    = "`e[0;31m"
    GREEN  = "`e[0;32m"
    YELLOW = "`e[1;33m"
    BLUE   = "`e[0;34m"
    NC     = "`e[0m"  # No Color
}

# Function to show usage
function Show-Usage {
    Write-Host "Usage: $($MyInvocation.ScriptName) -ResourceGroup <resource-group> [options]"
    Write-Host ""
    Write-Host "Required:"
    Write-Host "  -ResourceGroup, -g     Azure Resource Group"
    Write-Host ""
    Write-Host "  -Help, -h              Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  $($MyInvocation.ScriptName) -ResourceGroup my-resource-group"
    Write-Host "  $($MyInvocation.ScriptName) -g my-resource-group"
    exit 1
}

# Function to write colored output
function Write-Colored {
    param(
        [string]$Message,
        [string]$Color
    )
    Write-Host "$($Colors[$Color])$Message$($Colors.NC)"
}

# Parse command line arguments
param(
    [Parameter(Mandatory=$false)]
    [Alias("g")]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$false)]
    [Alias("h")]
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Show-Usage
}

# Validate required parameters
if ([string]::IsNullOrEmpty($ResourceGroup)) {
    Write-Colored "❌ Error: Resource group is required" "RED"
    Show-Usage
}

Write-Colored "🚀 Auto-Setup Pipeline Configuration" "BLUE"
Write-Host ""

# Check if Azure CLI is installed
try {
    $null = Get-Command az -ErrorAction Stop
} catch {
    Write-Colored "❌ Azure CLI is not installed. Please install it first." "RED"
    exit 1
}

# Check if Python is installed
$pythonCommand = $null
try {
    $null = Get-Command python3 -ErrorAction Stop
    $pythonCommand = "python3"
} catch {
    try {
        $null = Get-Command python -ErrorAction Stop
        $pythonCommand = "python"
    } catch {
        Write-Colored "❌ Python 3 is not installed. Please install it first." "RED"
        exit 1
    }
}

# Check if user is logged in to Azure
try {
    $null = az account show --output json 2>$null
} catch {
    Write-Colored "⚠️ You are not logged in to Azure. Please login first." "YELLOW"
    az login
}

Write-Host ""
Write-Colored "📋 Current Azure subscription:" "YELLOW"
az account show --output table
Write-Host ""

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "setup-pipeline.py"
$PythonRequirements = Join-Path $ScriptDir "requirements.txt"
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Colored "📁 Moving to Project Root: $ProjectRoot" "BLUE"
# Change to project root
Set-Location $ProjectRoot

# Install the required Python packages
Write-Host ""
Write-Colored "Installing required Python packages..." "BLUE"
& pip install -r $PythonRequirements
if ($LASTEXITCODE -ne 0) {
    Write-Colored "❌ Failed to install Python packages" "RED"
    exit 1
}

Write-Host ""
Write-Colored "Retrieving required parameters for setup..." "BLUE"
Write-Host "------------------"

Write-Colored "Retrieving App Configuration - (1/3)..." "BLUE"
# Retrieve the App Configuration endpoint from the infra deployment
try {
    # Get the deployment name
    $deploymentName = az deployment group list --resource-group $ResourceGroup --query "[?contains(name, 'doc-proc-infra')].name | [0]" --output tsv
    if ([string]::IsNullOrEmpty($deploymentName)) {
        throw "No deployment found"
    }
    
    # Get the app config store name from deployment output
    $appConfigStoreName = az deployment group show --resource-group $ResourceGroup --name $deploymentName --query "properties.outputs.appConfigStoreName.value" --output tsv
    if ([string]::IsNullOrEmpty($appConfigStoreName)) {
        throw "No app config store name in deployment output"
    }
    
    # Get the actual app config store
    $AppConfigStore = az appconfig show --name $appConfigStoreName --query name --output tsv
    if ([string]::IsNullOrEmpty($AppConfigStore)) {
        throw "App config store not found"
    }
    
    Write-Colored "✅ App Configuration Store: $AppConfigStore" "GREEN"
} catch {
    Write-Colored "❌ App Configuration Store not found. Please run deploy-azure-infra.sh first." "RED"
    exit 1
}

Write-Host ""
Write-Colored "Retrieving API URL - (2/3)..." "BLUE"
try {
    $ApiAppName = az containerapp list --resource-group $ResourceGroup --query "[?contains(name, 'api')].name | [0]" --output tsv
    if ([string]::IsNullOrEmpty($ApiAppName)) {
        throw "API app name not found"
    }
    
    $ApiUrl = az containerapp show --name $ApiAppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" --output tsv
    if ([string]::IsNullOrEmpty($ApiUrl)) {
        throw "API URL not found"
    }
    
    Write-Colored "✅ API URL: https://$ApiUrl" "GREEN"
} catch {
    Write-Colored "❌ API URL not found. Please check your deployment." "RED"
    exit 1
}

Write-Host ""
Write-Colored "Retrieving Storage Account - (3/3)..." "BLUE"
try {
    $StorageAccountName = az appconfig kv show --name $AppConfigStore --key "doc-proc.api.BLOB_STORAGE_ACCOUNT_NAME" --query "value" --output tsv
    if ([string]::IsNullOrEmpty($StorageAccountName)) {
        throw "Storage account name not found"
    }
    
    Write-Colored "✅ Storage Account Name: $StorageAccountName" "GREEN"
} catch {
    Write-Colored "❌ Storage Account Name not found in App Configuration. Please check your deployment." "RED"
    exit 1
}

Write-Host "------------------"
Write-Host ""
Write-Colored "Running setup-pipeline.py with retrieved parameters..." "BLUE"
Write-Host ""

# Run the Python script with the retrieved parameters
& $pythonCommand $PythonScript --api-url "https://$ApiUrl" --storage-account $StorageAccountName
if ($LASTEXITCODE -ne 0) {
    Write-Colored "❌ Python script execution failed" "RED"
    exit 1
}