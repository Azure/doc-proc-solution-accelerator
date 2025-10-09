#Requires -Version 7.0

<#
.SYNOPSIS
    Doc Processing Solution - Build and Push Docker Images to Azure Container Registry
    This script builds Docker images and pushes them to Azure Container Registry

.DESCRIPTION
    PowerShell script to build Docker images and push them to Azure Container Registry.
    The script can build all images or specific images based on parameters.

.PARAMETER Registry
    Azure Container Registry login server (required)

.PARAMETER Tag
    Image tag (default: latest)

.PARAMETER Api
    Build API app image. If specified with other specific flags, only specified images will be built.

.PARAMETER Web
    Build web app image. If specified with other specific flags, only specified images will be built.

.PARAMETER Worker
    Build worker app image. If specified with other specific flags, only specified images will be built.

.PARAMETER Crawler
    Build crawler app image. If specified with other specific flags, only specified images will be built.

.PARAMETER Help
    Show help message

.EXAMPLE
    .\build-and-push-images.ps1 -Registry "myregistry.azurecr.io"

.EXAMPLE
    .\build-and-push-images.ps1 -Registry "myregistry.azurecr.io" -Tag "v1.0.0"

.EXAMPLE
    .\build-and-push-images.ps1 -Registry "myregistry.azurecr.io" -Tag "v1.0.0" -Api -Web
#>

param(
    [Parameter(Mandatory = $true, HelpMessage = "Azure Container Registry login server")]
    [Alias("r")]
    [string]$Registry,

    [Parameter(Mandatory = $false, HelpMessage = "Image tag (default: latest)")]
    [Alias("t")]
    [string]$Tag = "latest",

    [Parameter(Mandatory = $false, HelpMessage = "Build API app image")]
    [switch]$Api,

    [Parameter(Mandatory = $false, HelpMessage = "Build web app image")]
    [switch]$Web,

    [Parameter(Mandatory = $false, HelpMessage = "Build worker app image")]
    [switch]$Worker,

    [Parameter(Mandatory = $false, HelpMessage = "Build crawler app image")]
    [switch]$Crawler,

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
    Write-Host "Usage: pwsh .\build-and-push-images.ps1 -Registry <registry-login-server> [options]"
    Write-Host ""
    Write-Host "Required:"
    Write-Host "  -Registry, -r          Azure Container Registry login server"
    Write-Host ""
    Write-Host "Optional:"
    Write-Host "  -Tag, -t              Image tag (default: latest)"
    Write-Host "  -Api                  Build API app image. If specified with other specific flags, only specified images will be built."
    Write-Host "  -Web                  Build web app image. If specified with other specific flags, only specified images will be built."
    Write-Host "  -Worker               Build worker app image. If specified with other specific flags, only specified images will be built."
    Write-Host "  -Crawler              Build crawler app image. If specified with other specific flags, only specified images will be built."
    Write-Host "  -Help, -h             Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  pwsh .\build-and-push-images.ps1 -Registry 'myregistry.azurecr.io'"
    Write-Host "  pwsh .\build-and-push-images.ps1 -Registry 'myregistry.azurecr.io' -Tag 'v1.0.0'"
    Write-Host "  pwsh .\build-and-push-images.ps1 -Registry 'myregistry.azurecr.io' -Tag 'v1.0.0' -Api -Web"
    exit 1
}

# Show help if requested
if ($Help) {
    Show-Usage
}

# Determine what to build
$BuildAll = $true
if ($Api -or $Web -or $Worker -or $Crawler) {
    $BuildAll = $false
}

Write-BlueOutput "🚀 Building and pushing Docker images to Azure Container Registry"
Write-BlueOutput "Registry: $Registry"
Write-BlueOutput "Tag: $Tag"
Write-Host ""

# Output what will be built
if ($BuildAll) {
    Write-BlueOutput "⚙️  Building all images (API, Web, Worker, Crawler)"
    Write-Host ""
} else {
    Write-BlueOutput "⚙️  Building selected images:"
    if ($Api) { Write-BlueOutput "✔️ API" }
    if ($Web) { Write-BlueOutput "✔️ Web" }
    if ($Worker) { Write-BlueOutput "✔️ Worker" }
    if ($Crawler) { Write-BlueOutput "✔️ Crawler" }
    Write-Host ""
}

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-BlueOutput "📁 Moving to Project Root: $ProjectRoot"
# Change to project root
Set-Location $ProjectRoot

# Check if Docker is running
try {
    $dockerInfo = docker info 2>$null
    if (-not $dockerInfo) {
        throw "Docker not running"
    }
}
catch {
    Write-RedOutput "❌ Docker is not running. Please start Docker first."
    exit 1
}

# Check if npm is installed
try {
    $npmVersion = npm --version 2>$null
    if (-not $npmVersion) {
        throw "npm not found"
    }
}
catch {
    Write-RedOutput "❌ npm is not installed. Please install Node.js and npm first."
    exit 1
}

# Check if Azure CLI is installed
try {
    $azVersion = az version --output json 2>$null | ConvertFrom-Json
    if (-not $azVersion) {
        throw "Azure CLI not found"
    }
}
catch {
    Write-RedOutput "❌ Azure CLI is not installed. Please install it first."
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

Write-Host ""
Write-YellowOutput "📋 Current Azure subscription:"
az account show --output table

# Login to Azure Container Registry
Write-Host ""
Write-BlueOutput "🔐 Logging in to Azure Container Registry..."
$registryName = $Registry.Split('.')[0]
try {
    az acr login --name $registryName
    Write-GreenOutput "✅ Successfully logged in to ACR"
}
catch {
    Write-RedOutput "❌ Failed to login to Azure Container Registry"
    exit 1
}
Write-Host ""

# Get Resource Group of the ACR
try {
    $ResourceGroup = az acr show --name $registryName --query "resourceGroup" --output tsv
}
catch {
    Write-YellowOutput "⚠️ Could not retrieve ACR resource group"
    $ResourceGroup = $null
}

# Function to build and push image
function Build-And-Push {
    param(
        [string]$Name,
        [string]$Dockerfile,
        [string]$Context
    )
    
    $FullImageName = "$Registry/doc-proc-$Name`:$Tag"
    
    Write-YellowOutput "📦 Building $Name..."
    Write-YellowOutput "📁  Using docker file: $Dockerfile"
    Write-YellowOutput "📁  Context: $Context"
    Write-YellowOutput "🏷️  Tagging image as $FullImageName"

    try {
        # Build the image
        docker buildx build --platform linux/amd64 -t $FullImageName -f $Dockerfile $Context
        Write-GreenOutput "✅ Successfully built $FullImageName"
        
        # Push the image
        Write-YellowOutput "📤 Pushing $Name to registry..."
        docker push $FullImageName
        Write-GreenOutput "✅ Successfully pushed $FullImageName"
        return $true
    }
    catch {
        Write-RedOutput "❌ Failed to build or push $Name"
        Write-Error $_.Exception.Message
        return $false
    }
    finally {
        Write-Host ("-" * 100)
        Write-Host ""
    }
}

# Build and push all images
Write-Host ("=" * 100)
Write-Host ""
Write-BlueOutput "Building and pushing images..."
Write-Host ""

$BuildResults = @()
$AllSuccessful = $true

# Build API
if ($BuildAll -or $Api) {
    $result = Build-And-Push -Name "api" -Dockerfile "doc-proc-api/Dockerfile" -Context "."
    $BuildResults += @{ Name = "api"; Success = $result; Image = "$Registry/doc-proc-api:$Tag" }
    if (-not $result) { $AllSuccessful = $false }
}

# Build Web
if ($BuildAll -or $Web) {
    $result = Build-And-Push -Name "web" -Dockerfile "doc-proc-web/Dockerfile" -Context "."
    $BuildResults += @{ Name = "web"; Success = $result; Image = "$Registry/doc-proc-web:$Tag" }
    if (-not $result) { $AllSuccessful = $false }
}

# Build Worker
if ($BuildAll -or $Worker) {
    $result = Build-And-Push -Name "worker" -Dockerfile "doc-proc-worker/Dockerfile" -Context "."
    $BuildResults += @{ Name = "worker"; Success = $result; Image = "$Registry/doc-proc-worker:$Tag" }
    if (-not $result) { $AllSuccessful = $false }
}

# Build Crawler
if ($BuildAll -or $Crawler) {
    $result = Build-And-Push -Name "crawler" -Dockerfile "doc-proc-crawler/Dockerfile" -Context "."
    $BuildResults += @{ Name = "crawler"; Success = $result; Image = "$Registry/doc-proc-crawler:$Tag" }
    if (-not $result) { $AllSuccessful = $false }
}

if ($AllSuccessful) {
    Write-GreenOutput "🎉 Image(s) built and pushed successfully!"
} else {
    Write-YellowOutput "⚠️ Some images failed to build or push. Check the output above for details."
}

Write-Host ""
Write-Host ""
Write-BlueOutput "📊 Build Results:"
foreach ($result in $BuildResults) {
    if ($result.Success) {
        Write-GreenOutput "✅ $($result.Image)"
    } else {
        Write-RedOutput "❌ $($result.Image)"
    }
}

Write-Host ""
Write-Host ""
if ($AllSuccessful -and $ResourceGroup) {
    Write-BlueOutput "➡️ Next step: Deploy the applications using the deployment script"
    Write-Host "   pwsh .\doc-proc-deploy\DeployApps.ps1 -ResourceGroup '$ResourceGroup'"
} elseif ($AllSuccessful) {
    Write-BlueOutput "➡️ Next step: Deploy the applications using the deployment script"
    Write-Host "   pwsh .\doc-proc-deploy\DeployApps.ps1 -ResourceGroup '<your-resource-group>'"
} else {
    Write-YellowOutput "Please fix the build errors and try again."
}
Write-Host ""