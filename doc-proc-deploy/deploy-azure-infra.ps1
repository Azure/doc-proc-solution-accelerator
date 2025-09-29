#Requires -Version 7.0

<#
.SYNOPSIS
    Doc Processing Solution - Azure Deployment Script
    This script deploys the entire solution to Azure using Bicep templates

.DESCRIPTION
    PowerShell script to deploy the Doc Processing solution infrastructure to Azure using Bicep templates.
    The script creates the resource group if it doesn't exist, deploys the infrastructure, and provides
    next steps for application deployment.

.PARAMETER ResourceGroup
    Azure Resource Group name (required)

.PARAMETER Location
    Azure location (default: westus2)

.PARAMETER NamePrefix
    Resource name prefix (default: docproc)

.PARAMETER Environment
    Environment name (default: dev)

.PARAMETER Debug
    Enable debug logging

.PARAMETER Help
    Show help message

.EXAMPLE
    .\deploy-azure-infra.ps1 -ResourceGroup "my-resource-group"

.EXAMPLE
    .\deploy-azure-infra.ps1 -ResourceGroup "my-rg" -Location "westus2" -NamePrefix "myapp" -Environment "prod"
#>

param(
    [Parameter(Mandatory = $true, HelpMessage = "Azure Resource Group name")]
    [Alias("g")]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $false, HelpMessage = "Azure location (default: westus2)")]
    [Alias("l")]
    [string]$Location = "westus2",

    [Parameter(Mandatory = $false, HelpMessage = "Resource name prefix (default: docproc)")]
    [Alias("p")]
    [string]$NamePrefix = "docproc",

    [Parameter(Mandatory = $false, HelpMessage = "Environment name (default: dev)")]
    [Alias("e")]
    [string]$Environment = "dev",

    [Parameter(Mandatory = $false, HelpMessage = "Enable debug logging")]
    [Alias("d")]
    [switch]$Debug,

    [Parameter(Mandatory = $false, HelpMessage = "Show help message")]
    [Alias("h")]
    [switch]$Help
)

# Set error action preference to stop on errors
$ErrorActionPreference = "Stop"

# Color functions for output
function Write-ColoredOutput {
    param(
        [string]$Message,
        [ConsoleColor]$ForegroundColor = [ConsoleColor]::White
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-RedOutput { param([string]$Message) Write-ColoredOutput $Message -ForegroundColor Red }
function Write-GreenOutput { param([string]$Message) Write-ColoredOutput $Message -ForegroundColor Green }
function Write-YellowOutput { param([string]$Message) Write-ColoredOutput $Message -ForegroundColor Yellow }
function Write-BlueOutput { param([string]$Message) Write-ColoredOutput $Message -ForegroundColor Blue }

# Function to show usage
function Show-Usage {
    Write-Host "Usage: .\deploy-azure-infra.ps1 -ResourceGroup <resource-group> [options]"
    Write-Host ""
    Write-Host "Required:"
    Write-Host "  -ResourceGroup, -g     Azure Resource Group name"
    Write-Host ""
    Write-Host "Optional:"
    Write-Host "  -Location, -l          Azure location (default: westus2)"
    Write-Host "  -NamePrefix, -p        Resource name prefix (default: docproc)"
    Write-Host "  -Environment, -e       Environment name (default: dev)"
    Write-Host "  -Debug, -d             Enable debug logging"
    Write-Host "  -Help, -h              Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy-azure-infra.ps1 -ResourceGroup 'my-resource-group'"
    Write-Host "  .\deploy-azure-infra.ps1 -ResourceGroup 'my-rg' -Location 'westus2' -NamePrefix 'myapp' -Environment 'prod'"
    exit 1
}

# Show help if requested
if ($Help) {
    Show-Usage
}

Write-BlueOutput "🚀 Starting Azure deployment for Doc Processing Solution"
Write-BlueOutput "Resource Group: $ResourceGroup"
Write-BlueOutput "Location: $Location"
Write-BlueOutput "Name Prefix: $NamePrefix"
Write-BlueOutput "Environment: $Environment"
Write-Host ""

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-BlueOutput "📁 Moving to Project Root: $ProjectRoot"
Write-Host ""

# Change to project root
Set-Location $ProjectRoot

# Check if Azure CLI is installed
try {
    $azVersion = az version --output json 2>$null | ConvertFrom-Json
    if (-not $azVersion) {
        throw "Azure CLI not found"
    }
}
catch {
    Write-RedOutput "❌ Azure CLI is not installed. Please install it first."
    Write-Host "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Check if user is logged in to Azure
try {
    $accountInfo = az account show --output json 2>$null | ConvertFrom-Json
    if (-not $accountInfo) {
        throw "Not logged in"
    }
}
catch {
    Write-YellowOutput "⚠️ You are not logged in to Azure. Please login first."
    az login
}

Write-YellowOutput "📋 Current Azure subscription:"
az account show --output table

# Ask for confirmation
Write-Host ""
$confirmation = Read-Host "Continue with deployment? (y/N)"
if ($confirmation -notmatch "^[Yy]$") {
    Write-Host "Deployment cancelled"
    exit 0
}

# Create resource group if it doesn't exist
Write-BlueOutput "🏗️ Ensuring resource group exists..."
try {
    $existingGroup = az group show --name $ResourceGroup --output json 2>$null | ConvertFrom-Json
    if (-not $existingGroup) {
        throw "Resource group not found"
    }
    Write-GreenOutput "✅ Resource group already exists"
}
catch {
    Write-YellowOutput "Creating resource group: $ResourceGroup"
    az group create --name $ResourceGroup --location $Location --output table
    Write-GreenOutput "✅ Resource group created"
}

# Deploy full infrastructure using main Bicep template
Write-BlueOutput "🏗️ Deploying Azure infrastructure..."
$DeploymentName = "doc-proc-infra-$(Get-Date -Format 'yyyyMMddHHmmss')"

# Build Azure CLI command arguments
$deploymentArgs = @(
    "deployment", "group", "create",
    "--resource-group", $ResourceGroup,
    "--template-file", "doc-proc-deploy/infra/bicep/main.bicep",
    "--parameters",
    "namePrefix=$NamePrefix",
    "environment=$Environment",
    "location=$Location",
    "--name", $DeploymentName,
    "--output", "table"
)

if ($Debug) {
    $deploymentArgs += "--debug"
}

# Execute deployment
try {
    & az @deploymentArgs
    $deploymentResult = $LASTEXITCODE
}
catch {
    Write-RedOutput "❌ Infrastructure deployment failed"
    Write-Error $_.Exception.Message
    exit 1
}

if ($deploymentResult -eq 0) {
    Write-Host ""
    Write-GreenOutput "✅ Infrastructure deployed successfully"
    
    # Get deployment outputs
    try {
        $AcrLoginServer = az deployment group show `
            --resource-group $ResourceGroup `
            --name $DeploymentName `
            --query "properties.outputs.containerRegistryLoginServer.value" `
            --output tsv
        
        $ContainerAppsEnvId = az deployment group show `
            --resource-group $ResourceGroup `
            --name $DeploymentName `
            --query "properties.outputs.containerAppsEnvironmentId.value" `
            --output tsv

        $AppConfigStoreEndpoint = az deployment group show `
            --resource-group $ResourceGroup `
            --name $DeploymentName `
            --query "properties.outputs.appConfigStoreEndpoint.value" `
            --output tsv
        
        Write-GreenOutput "Container Registry: $AcrLoginServer"
        Write-GreenOutput "Container Apps Environment: $(Split-Path -Leaf $ContainerAppsEnvId)"
        Write-GreenOutput "App Configuration Store Endpoint: $AppConfigStoreEndpoint"
        Write-Host ""
    }
    catch {
        Write-YellowOutput "⚠️ Could not retrieve all deployment outputs, but deployment was successful."
    }
}
else {
    Write-RedOutput "❌ Infrastructure deployment failed"
    exit 1
}

Write-Host ""
Write-GreenOutput "🎉 Azure infrastructure deployment completed!"
Write-Host ""
Write-BlueOutput "Next Steps:"
Write-Host "1. Build and push your Docker images to the Container Registry:"
if ($AcrLoginServer) {
    Write-Host "   .\doc-proc-deploy\build-and-push-images.sh -r $AcrLoginServer"
} else {
    Write-Host "   .\doc-proc-deploy\build-and-push-images.sh -r <ACR_LOGIN_SERVER>"
}
Write-Host ""
Write-Host "2. Deploy your applications using pushed images:"
Write-Host "   .\doc-proc-deploy\deploy-apps.sh -g $ResourceGroup"
Write-Host ""