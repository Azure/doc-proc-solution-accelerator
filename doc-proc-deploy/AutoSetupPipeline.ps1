#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Auto-Deploy Pipeline Setup Script (PowerShell)
    
.DESCRIPTION
    This script fetches configuration from a deployed Azure resource group
    and runs the setup-pipeline.py script with the correct parameters.
    
.PARAMETER ResourceGroupName
    Name of the Azure resource group containing deployed resources
    
.PARAMETER SubscriptionId
    Azure subscription ID (optional)
    
.PARAMETER InputContainer
    Input container name (default: documents)
    
.PARAMETER OutputContainer
    Output container name (default: output)
    
.PARAMETER DryRun
    Show configuration without executing setup
    
.EXAMPLE
    ./AutoSetupPipeline.ps1 -ResourceGroupName "rg-pwsh-02"
    
.EXAMPLE
    ./AutoSetupPipeline.ps1 -ResourceGroupName "rg-pwsh-02" -SubscriptionId "12345678-1234-1234-1234-123456789012"
    
.EXAMPLE
    ./AutoSetupPipeline.ps1 -ResourceGroupName "rg-pwsh-02" -InputContainer "documents" -OutputContainer "processed" -DryRun
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$false)]
    [string]$InputContainer = "documents",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputContainer = "output",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonScript = Join-Path $ScriptDir "setup-pipeline.py"

# Color functions
function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    switch ($Color) {
        "Green" { Write-Host "✅ $Message" -ForegroundColor Green }
        "Red" { Write-Host "❌ $Message" -ForegroundColor Red }
        "Yellow" { Write-Host "⚠️ $Message" -ForegroundColor Yellow }
        "Blue" { Write-Host "ℹ️ $Message" -ForegroundColor Blue }
        default { Write-Host $Message }
    }
}

function Write-Success { param([string]$Message) Write-ColoredOutput $Message "Green" }
function Write-Error-Custom { param([string]$Message) Write-ColoredOutput $Message "Red" }
function Write-Warning-Custom { param([string]$Message) Write-ColoredOutput $Message "Yellow" }
function Write-Info { param([string]$Message) Write-ColoredOutput $Message "Blue" }

function Write-Header {
    Write-Host "=================================================" -ForegroundColor Blue
    Write-Host "  Auto-Deploy Pipeline Setup Script (PowerShell)" -ForegroundColor Blue
    Write-Host "=================================================" -ForegroundColor Blue
    Write-Host
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check if Azure CLI is available
    try {
        $null = Get-Command az -ErrorAction Stop
    }
    catch {
        Write-Error-Custom "Azure CLI (az) is not installed or not in PATH"
        Write-Host "Please install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    }
    
    # Check if Python is available
    $pythonCmd = $null
    try {
        $null = Get-Command python3 -ErrorAction Stop
        $pythonCmd = "python3"
    }
    catch {
        try {
            $null = Get-Command python -ErrorAction Stop
            $pythonCmd = "python"
        }
        catch {
            Write-Error-Custom "Python 3 is not installed or not in PATH"
            Write-Host "Please install Python 3: https://www.python.org/downloads/"
            exit 1
        }
    }
    
    # Check if setup-pipeline.py exists
    if (-not (Test-Path $PythonScript)) {
        Write-Error-Custom "setup-pipeline.py not found at: $PythonScript"
        Write-Host "Make sure the Python script is in the same directory as this script"
        exit 1
    }
    
    # Check if logged into Azure
    try {
        $null = az account show 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Not logged in"
        }
    }
    catch {
        Write-Error-Custom "Not logged into Azure CLI"
        Write-Host "Please run: az login"
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
    return $pythonCmd
}

# Function to get API URL from Container App
function Get-ApiUrl {
    param(
        [string]$ResourceGroup,
        [string]$Subscription
    )
    
    Write-Info "Fetching API URL from Container App..."
    
    # Build Azure CLI command
    $azCmd = @("containerapp", "list", "--resource-group", $ResourceGroup, "--output", "json")
    if ($Subscription) {
        $azCmd += @("--subscription", $Subscription)
    }
    
    # Get container apps in the resource group
    try {
        $containerAppsJson = & az @azCmd 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to list container apps"
        }
        
        $containerApps = $containerAppsJson | ConvertFrom-Json
    }
    catch {
        Write-Error-Custom "Failed to fetch container apps from resource group: $ResourceGroup"
        return $null
    }
    
    if (-not $containerApps -or $containerApps.Count -eq 0) {
        Write-Error-Custom "No container apps found in resource group: $ResourceGroup"
        return $null
    }
    
    # Look for the API container app (typically contains 'api' in the name)
    $apiApp = $containerApps | Where-Object { $_.name -like "*api*" } | Select-Object -First 1
    
    if (-not $apiApp) {
        # Fallback: get the first container app with ingress enabled
        $apiApp = $containerApps | Where-Object { $_.properties.configuration.ingress } | Select-Object -First 1
    }
    
    if (-not $apiApp -or -not $apiApp.properties.configuration.ingress.fqdn) {
        Write-Error-Custom "Could not find API container app with ingress enabled"
        Write-Info "Available container apps:"
        $containerApps | ForEach-Object { Write-Host "  - $($_.name)" }
        return $null
    }
    
    $apiUrl = "https://$($apiApp.properties.configuration.ingress.fqdn)"
    Write-Success "Found API URL: $apiUrl"
    return $apiUrl
}

# Function to get storage account details
function Get-StorageConfig {
    param(
        [string]$ResourceGroup,
        [string]$Subscription
    )
    
    Write-Info "Fetching Storage Account configuration..."
    
    # Build Azure CLI command
    $azCmd = @("storage", "account", "list", "--resource-group", $ResourceGroup, "--output", "json")
    if ($Subscription) {
        $azCmd += @("--subscription", $Subscription)
    }
    
    # Get storage accounts in the resource group
    try {
        $storageAccountsJson = & az @azCmd 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to list storage accounts"
        }
        
        $storageAccounts = $storageAccountsJson | ConvertFrom-Json
    }
    catch {
        Write-Error-Custom "Failed to fetch storage accounts from resource group: $ResourceGroup"
        return $null
    }
    
    if (-not $storageAccounts -or $storageAccounts.Count -eq 0) {
        Write-Error-Custom "No storage accounts found in resource group: $ResourceGroup"
        return $null
    }
    
    # Get the first storage account (or look for one with 'docproc' in the name)
    $storageAccount = $storageAccounts | Where-Object { $_.name -like "*docproc*" } | Select-Object -First 1
    
    if (-not $storageAccount) {
        # Fallback: get the first storage account
        $storageAccount = $storageAccounts | Select-Object -First 1
    }
    
    if (-not $storageAccount) {
        Write-Error-Custom "Could not find storage account"
        return $null
    }
    
    $storageAccountName = $storageAccount.name
    Write-Success "Found Storage Account: $storageAccountName"
    
    # Get storage account key
    Write-Info "Fetching Storage Account key..."
    
    $keyCmd = @("storage", "account", "keys", "list", "--account-name", $storageAccountName, "--resource-group", $ResourceGroup, "--output", "json")
    if ($Subscription) {
        $keyCmd += @("--subscription", $Subscription)
    }
    
    try {
        $keysJson = & az @keyCmd 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to get storage keys"
        }
        
        $keys = $keysJson | ConvertFrom-Json
        $storageKey = $keys[0].value
    }
    catch {
        Write-Error-Custom "Could not retrieve storage account key"
        return $null
    }
    
    if (-not $storageKey) {
        Write-Error-Custom "Could not retrieve storage account key"
        return $null
    }
    
    Write-Success "Retrieved Storage Account key"
    
    # Return configuration object
    return @{
        AccountName = $storageAccountName
        AccountKey = $storageKey
    }
}

# Function to test API connectivity
function Test-ApiConnectivity {
    param([string]$ApiUrl)
    
    Write-Info "Testing API connectivity..."
    
    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/api/health" -Method Get -TimeoutSec 10 -ErrorAction Stop
        Write-Success "API is accessible at $ApiUrl"
        return $true
    }
    catch {
        Write-Warning-Custom "API health check failed, but continuing (API might still be starting up)"
        return $false
    }
}

# Main execution
try {
    Write-Header
    
    Write-Info "Resource Group: $ResourceGroupName"
    if ($SubscriptionId) {
        Write-Info "Subscription: $SubscriptionId"
    }
    Write-Info "Input Container: $InputContainer"
    Write-Info "Output Container: $OutputContainer"
    Write-Host
    
    # Check prerequisites
    $pythonCmd = Test-Prerequisites
    Write-Host
    
    # Get API URL
    $apiUrl = Get-ApiUrl -ResourceGroup $ResourceGroupName -Subscription $SubscriptionId
    if (-not $apiUrl) {
        exit 1
    }
    Write-Host
    
    # Get storage configuration
    Write-Info "Retrieving storage configuration..."
    $storageConfig = Get-StorageConfig -ResourceGroup $ResourceGroupName -Subscription $SubscriptionId
    if (-not $storageConfig) {
        exit 1
    }
    Write-Host
    
    # Test API connectivity
    Test-ApiConnectivity -ApiUrl $apiUrl
    Write-Host
    
    # Display configuration
    Write-Info "Configuration Retrieved:"
    Write-Host "  • API URL: $apiUrl" -ForegroundColor Green
    Write-Host "  • Storage Account: $($storageConfig.AccountName)" -ForegroundColor Green
    Write-Host "  • Storage Key: $($storageConfig.AccountKey.Substring(0,8))...$($storageConfig.AccountKey.Substring($storageConfig.AccountKey.Length-4))" -ForegroundColor Green
    Write-Host "  • Input Container: $InputContainer" -ForegroundColor Green
    Write-Host "  • Output Container: $OutputContainer" -ForegroundColor Green
    Write-Host
    
    # Prepare Python script arguments
    $pythonArgs = @(
        "--api-url", $apiUrl
        "--storage-account", $storageConfig.AccountName
        "--storage-key", $storageConfig.AccountKey
        "--input-container", $InputContainer
        "--output-container", $OutputContainer
    )
    
    if ($DryRun) {
        $pythonArgs += "--dry-run"
    }
    
    # Run the Python setup script
    Write-Info "Running pipeline setup script..."
    Write-Host
    
    if ($DryRun) {
        Write-Info "DRY RUN MODE - Would execute:"
        Write-Host "$pythonCmd $PythonScript $($pythonArgs -join ' ')"
        Write-Host
    }
    
    # Execute the Python script
    & $pythonCmd $PythonScript @pythonArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Pipeline setup failed with exit code: $LASTEXITCODE"
        exit $LASTEXITCODE
    }
    
}
catch {
    Write-Error-Custom "Script failed: $($_.Exception.Message)"
    exit 1
}