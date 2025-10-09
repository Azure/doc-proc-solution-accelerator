#Requires -Version 7.0

<#
.SYNOPSIS
    Doc Processing Solution - Deploy Applications to Azure
    This script deploys API, web, and worker applications to Azure Container Apps

.DESCRIPTION
    PowerShell script to deploy applications to Azure Container Apps.
    The script can deploy all applications or specific applications based on parameters.

.PARAMETER ResourceGroup
    Azure Resource Group name (required)

.PARAMETER NamePrefix
    Resource name prefix (default: docproc)

.PARAMETER Environment
    Environment name (default: dev)

.PARAMETER Tag
    Image tag (default: latest)

.PARAMETER App
    Deploy API and WEB apps. If specified with other flags, only specified apps will be deployed.

.PARAMETER Worker
    Deploy worker app. If specified with other flags, only specified apps will be deployed.

.PARAMETER Crawler
    Deploy crawler app. If specified with other flags, only specified apps will be deployed.

.PARAMETER Help
    Show help message

.EXAMPLE
    .\deploy-apps.ps1 -ResourceGroup "my-rg"

.EXAMPLE
    .\deploy-apps.ps1 -ResourceGroup "my-rg" -Environment "prod" -Tag "v1.0.0"

.EXAMPLE
    .\deploy-apps.ps1 -ResourceGroup "my-rg" -Environment "prod" -Tag "v1.0.0" -App

.EXAMPLE
    .\deploy-apps.ps1 -ResourceGroup "my-rg" -Environment "prod" -Tag "v1.0.0" -Worker
#>

param(
    [Parameter(Mandatory = $true, HelpMessage = "Azure Resource Group name")]
    [Alias("g")]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $false, HelpMessage = "Resource name prefix (default: docproc)")]
    [Alias("p")]
    [string]$NamePrefix = "docproc",

    [Parameter(Mandatory = $false, HelpMessage = "Environment name (default: dev)")]
    [Alias("e")]
    [string]$Environment = "dev",

    [Parameter(Mandatory = $false, HelpMessage = "Image tag (default: latest)")]
    [Alias("t")]
    [string]$Tag = "latest",

    [Parameter(Mandatory = $false, HelpMessage = "Deploy API and WEB apps")]
    [switch]$App,

    [Parameter(Mandatory = $false, HelpMessage = "Deploy worker app")]
    [switch]$Worker,

    [Parameter(Mandatory = $false, HelpMessage = "Deploy crawler app")]
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
    Write-Host "Usage: pwsh .\deploy-apps.ps1 -ResourceGroup <resource-group> [options]"
    Write-Host ""
    Write-Host "Required:"
    Write-Host "  -ResourceGroup, -g     Azure Resource Group name"
    Write-Host ""
    Write-Host "Optional:"
    Write-Host "  -NamePrefix, -p        Resource name prefix (default: docproc)"
    Write-Host "  -Environment, -e       Environment name (default: dev)"
    Write-Host "  -Tag, -t              Image tag (default: latest)"
    Write-Host "  -App                  Deploy API and WEB apps. If specified with other flags, only specified apps will be deployed."
    Write-Host "  -Worker               Deploy worker app. If specified with other flags, only specified apps will be deployed."
    Write-Host "  -Crawler              Deploy crawler app. If specified with other flags, only specified apps will be deployed."
    Write-Host "  -Help, -h             Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  pwsh .\deploy-apps.ps1 -ResourceGroup 'my-rg'"
    Write-Host "  pwsh .\deploy-apps.ps1 -ResourceGroup 'my-rg' -Environment 'prod' -Tag 'v1.0.0'"
    Write-Host "  pwsh .\deploy-apps.ps1 -ResourceGroup 'my-rg' -Environment 'prod' -Tag 'v1.0.0' -App"
    Write-Host "  pwsh .\deploy-apps.ps1 -ResourceGroup 'my-rg' -Environment 'prod' -Tag 'v1.0.0' -Worker"
    exit 1
}

# Show help if requested
if ($Help) {
    Show-Usage
}

# Determine what to deploy
$DeployAll = $true
if ($App -or $Worker -or $Crawler) {
    $DeployAll = $false
}

Write-BlueOutput "🚀 Deploying applications to Azure"
Write-BlueOutput "Resource Group: $ResourceGroup"
Write-BlueOutput "Name Prefix: $NamePrefix"
Write-BlueOutput "Environment: $Environment"
Write-BlueOutput "Image Tag: $Tag"
Write-Host ""

# Confirm to continue
$confirm = Read-Host "Proceed with deployment? (y/n)"
if ($confirm -ne "y") {
    Write-YellowOutput "⚠️ Deployment cancelled by user."
    exit 0
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
Write-Host ""

# Output what will be deployed
if ($DeployAll) {
    Write-BlueOutput "⚙️  Deploying all apps (API, Web, Worker, Crawler)"
    Write-Host ""
} else {
    Write-BlueOutput "⚙️  Deploying selected apps:"
    if ($App) { 
        Write-BlueOutput "✔️ API"
        Write-BlueOutput "✔️ Web"
    }
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

Write-Host ""
Write-BlueOutput "Retrieving required parameters for deployment ($Environment)..."
Write-Host "------------------"

# Function to retry operations with exponential backoff
function Invoke-WithRetry {
    param(
        [ScriptBlock]$ScriptBlock,
        [string]$OperationName,
        [int]$MaxRetries = 3,
        [int]$InitialDelay = 2
    )
    
    $retryCount = 0
    $delay = $InitialDelay
    
    while ($retryCount -lt $MaxRetries) {
        try {
            $result = & $ScriptBlock
            if ($result) {
                return $result
            }
            throw "Operation returned null or empty result"
        }
        catch {
            $retryCount++
            if ($retryCount -ge $MaxRetries) {
                Write-RedOutput "❌ $OperationName failed after $MaxRetries attempts"
                throw $_.Exception
            }
            
            Write-YellowOutput "⚠️ $OperationName failed (attempt $retryCount/$MaxRetries), retrying in $delay seconds..."
            Start-Sleep -Seconds $delay
            $delay *= 2  # Exponential backoff
        }
    }
}

# Retrieve Container Registry Login Server
Write-BlueOutput "Retrieving Container Registry Login Server - (1/4)..."
try {
    $infraDeploymentName = az deployment group list --resource-group $ResourceGroup --query "[?contains(name, 'doc-proc-infra')].name | [0]" --output tsv
    if (-not $infraDeploymentName) {
        throw "No infrastructure deployment found"
    }
    
    $Registry = az deployment group show --resource-group $ResourceGroup --name $infraDeploymentName --query "properties.outputs.containerRegistryLoginServer.value" --output tsv
    if (-not $Registry) {
        throw "Container Registry not found"
    }
    
    Write-GreenOutput "✅ Container Registry: $Registry"
}
catch {
    Write-RedOutput "❌ Container Registry not found. Please run deploy-azure-infra.ps1 first."
    exit 1
}

Start-Sleep -Seconds 2

# Retrieve App Configuration endpoint
Write-BlueOutput "Retrieving App Configuration endpoint - (2/4)..."
try {
    $appConfigName = az deployment group show --resource-group $ResourceGroup --name $infraDeploymentName --query "properties.outputs.appConfigStoreName.value" --output tsv
    if (-not $appConfigName) {
        throw "App Configuration name not found"
    }
    
    $AppConfigStoreEndpoint = az appconfig show --name $appConfigName --query endpoint --output tsv
    if (-not $AppConfigStoreEndpoint) {
        throw "App Configuration Endpoint not found"
    }
    
    Write-GreenOutput "✅ App Configuration Endpoint: $AppConfigStoreEndpoint"
}
catch {
    Write-RedOutput "❌ App Configuration Endpoint not found. Please run deploy-azure-infra.ps1 first."
    exit 1
}

Start-Sleep -Seconds 2

# Retrieve User Assigned Identity Name
Write-BlueOutput "Retrieving User Assigned Identity Name - (3/4)..."
try {
    $UserAssignedIdentityName = az deployment group show --resource-group $ResourceGroup --name $infraDeploymentName --query "properties.outputs.userAssignedIdentityName.value" --output tsv
    if (-not $UserAssignedIdentityName) {
        throw "User Assigned Identity Name not found"
    }
    
    Write-GreenOutput "✅ User Assigned Identity Name: $UserAssignedIdentityName"
}
catch {
    Write-RedOutput "❌ User Assigned Identity Name not found. Please run deploy-azure-infra.ps1 first."
    exit 1
}

Start-Sleep -Seconds 2

# Get Container Apps Environment Name
Write-BlueOutput "Retrieving Container Apps Environment - (4/4)..."
try {
    $ContainerAppsEnvName = Invoke-WithRetry -ScriptBlock {
        az containerapp env list --resource-group $ResourceGroup --query "[?contains(name, '$NamePrefix')].name | [0]" --output tsv
    } -OperationName "Container Apps Environment retrieval"
    
    if (-not $ContainerAppsEnvName) {
        throw "Container Apps Environment not found"
    }
    
    Write-GreenOutput "✅ Container Apps Environment Name: $ContainerAppsEnvName"
}
catch {
    Write-RedOutput "❌ Container Apps Environment not found. Please run deploy-azure-infra.ps1 first."
    exit 1
}

Write-Host ""
Write-BlueOutput "Waiting for some seconds to let connections settle..."
Start-Sleep -Seconds 5

Write-Host ""
Write-BlueOutput "🌐 Deploying Solution Apps..."
Write-Host "------------------"

# Initialize deployment results
$DeploymentResults = @{
    ApiSuccess = $false
    WebSuccess = $false
    WorkerSuccess = $false
    CrawlerSuccess = $false
    ApiUrl = ""
    WebUrl = ""
}

# Function to deploy application with retry logic
function Deploy-Application {
    param(
        [string]$AppType,
        [string]$TemplateFile,
        [hashtable]$Parameters,
        [int]$MaxRetries = 3
    )
    
    $deploymentName = "doc-proc-apps-$AppType-$(Get-Date -Format 'yyyyMMddHHmmss')"
    $success = $false
    $retryCount = 0
    $appName = ""
    $appUrl = ""
    
    Write-BlueOutput "👷 Deploying $AppType App..."
    
    while ($retryCount -lt $MaxRetries -and -not $success) {
        $retryCount++
        Write-BlueOutput "Attempt $retryCount/$MaxRetries`: Deploying $AppType App..."
        
        try {
            # Build parameter string for Azure CLI
            $parameterString = ""
            foreach ($key in $Parameters.Keys) {
                $parameterString += "$key=$($Parameters[$key]) "
            }
            
            # Execute deployment
            $deploymentArgs = @(
                "deployment", "group", "create",
                "--resource-group", $ResourceGroup,
                "--template-file", $TemplateFile,
                "--parameters"
            ) + $parameterString.Trim().Split(' ') + @(
                "--name", $deploymentName,
                "--output", "table"
            )
            
            & az @deploymentArgs
            
            if ($LASTEXITCODE -eq 0) {
                Write-GreenOutput "✅ $AppType App deployed successfully"
                
                # Get the Container App name from deployment outputs
                $appName = az deployment group show --resource-group $ResourceGroup --name $deploymentName --query "properties.outputs.containerAppName.value" --output tsv
                
                # Force a new app revision to ensure the latest image is pulled
                Write-BlueOutput "Forcing a new revision to pull the latest image..."
                $revisionSuffix = Get-Date -Format "yyyyMMddHHmmss"
                az containerapp update --name $appName --resource-group $ResourceGroup --image "$Registry/doc-proc-$($AppType.ToLower()):$Tag" --revision-suffix $revisionSuffix --output none --no-wait
                Write-GreenOutput "✅ Updated Container App to pull latest image"
                
                # Get URL for API and Web apps
                if ($AppType -eq "api" -or $AppType -eq "web") {
                    $fqdn = az containerapp show --name $appName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" --output tsv 2>$null
                    if ($fqdn) {
                        $appUrl = "https://$fqdn"
                        Write-GreenOutput "$AppType URL: $appUrl"
                    } else {
                        Write-YellowOutput "⚠️ Could not retrieve $AppType URL"
                    }
                }
                
                $success = $true
            } else {
                throw "Deployment command failed with exit code $LASTEXITCODE"
            }
        }
        catch {
            Write-RedOutput "❌ $AppType deployment failed (attempt $retryCount/$MaxRetries)"
            if ($retryCount -lt $MaxRetries) {
                Write-YellowOutput "⚠️ Retrying $AppType deployment in 5 seconds..."
                Start-Sleep -Seconds 5
            }
        }
    }
    
    if (-not $success) {
        Write-RedOutput "❌ $AppType deployment failed after $MaxRetries attempts"
    }
    
    return @{
        Success = $success
        AppName = $appName
        AppUrl = $appUrl
    }
}

######################################################################
## API APP DEPLOYMENT
######################################################################

if ($DeployAll -or $App) {
    $apiParameters = @{
        environment = $Environment
        namePrefix = $NamePrefix
        containerImage = "$Registry/doc-proc-api:$Tag"
        containerAppsEnvironment = $ContainerAppsEnvName
        containerRegistryServer = $Registry
        appConfigStoreEndpoint = $AppConfigStoreEndpoint
        userAssignedIdentityName = $UserAssignedIdentityName
    }
    
    $apiResult = Deploy-Application -AppType "api" -TemplateFile "doc-proc-api/infra/bicep/main.bicep" -Parameters $apiParameters
    $DeploymentResults.ApiSuccess = $apiResult.Success
    $DeploymentResults.ApiUrl = $apiResult.AppUrl
    Write-Host ""
} else {
    Write-YellowOutput "⚠️ Skipping API deployment"
    Write-Host ""
}

######################################################################
## WEB APP DEPLOYMENT
######################################################################

if ($DeployAll -or $App) {
    $webParameters = @{
        namePrefix = $NamePrefix
        environment = $Environment
        containerImage = "$Registry/doc-proc-web:$Tag"
        backendApiUrl = $DeploymentResults.ApiUrl
        containerAppsEnvironment = $ContainerAppsEnvName
        containerRegistryServer = $Registry
        userAssignedIdentityName = $UserAssignedIdentityName
    }
    
    $webResult = Deploy-Application -AppType "web" -TemplateFile "doc-proc-web/infra/bicep/main.bicep" -Parameters $webParameters
    $DeploymentResults.WebSuccess = $webResult.Success
    $DeploymentResults.WebUrl = $webResult.AppUrl
    Write-Host ""
} else {
    Write-YellowOutput "⚠️ Skipping Web App deployment"
    Write-Host ""
}

######################################################################
## WORKER APP DEPLOYMENT
######################################################################

if ($DeployAll -or $Worker) {
    $workerParameters = @{
        environment = $Environment
        namePrefix = $NamePrefix
        containerImage = "$Registry/doc-proc-worker:$Tag"
        containerAppsEnvironment = $ContainerAppsEnvName
        containerRegistryServer = $Registry
        appConfigStoreEndpoint = $AppConfigStoreEndpoint
        userAssignedIdentityName = $UserAssignedIdentityName
    }
    
    $workerResult = Deploy-Application -AppType "worker" -TemplateFile "doc-proc-worker/infra/bicep/main.bicep" -Parameters $workerParameters
    $DeploymentResults.WorkerSuccess = $workerResult.Success
    Write-Host ""
} else {
    Write-YellowOutput "⚠️ Skipping Worker deployment"
    Write-Host ""
}

######################################################################
## CRAWLER APP DEPLOYMENT
######################################################################

if ($DeployAll -or $Crawler) {
    $crawlerParameters = @{
        environment = $Environment
        namePrefix = $NamePrefix
        containerImage = "$Registry/doc-proc-crawler:$Tag"
        containerAppsEnvironment = $ContainerAppsEnvName
        containerRegistryServer = $Registry
        appConfigStoreEndpoint = $AppConfigStoreEndpoint
        userAssignedIdentityName = $UserAssignedIdentityName
    }
    
    $crawlerResult = Deploy-Application -AppType "crawler" -TemplateFile "doc-proc-crawler/infra/bicep/main.bicep" -Parameters $crawlerParameters
    $DeploymentResults.CrawlerSuccess = $crawlerResult.Success
    Write-Host ""
} else {
    Write-YellowOutput "⚠️ Skipping Crawler deployment"
    Write-Host ""
}

######################################################################
## DEPLOYMENT SUMMARY
######################################################################

Write-Host ""
Write-GreenOutput "🎉 Application deployment completed!"
Write-Host ""
Write-BlueOutput "📊 Deployment Summary:"

if ($DeploymentResults.ApiSuccess) {
    Write-GreenOutput "✅ API App: $($DeploymentResults.ApiUrl)"
    Write-GreenOutput "   Health Check: $($DeploymentResults.ApiUrl)/api/health"
    Write-GreenOutput "   API Docs: $($DeploymentResults.ApiUrl)/docs"
}

if ($DeploymentResults.WebSuccess) {
    Write-GreenOutput "✅ Web App: $($DeploymentResults.WebUrl)"
}

if ($DeploymentResults.WorkerSuccess) {
    Write-GreenOutput "✅ Worker: Container App deployed"
}

if ($DeploymentResults.CrawlerSuccess) {
    Write-GreenOutput "✅ Crawler: Container App deployed"
}

if (-not $DeploymentResults.ApiSuccess -and -not $DeploymentResults.WebSuccess -and -not $DeploymentResults.WorkerSuccess -and -not $DeploymentResults.CrawlerSuccess) {
    Write-YellowOutput "⚠️ No applications were deployed successfully."
    Write-YellowOutput " - Did you run BuildAndPushImages.ps1 first?"
    Write-YellowOutput " - Are you missing the prefix or environment args?"
    Write-YellowOutput "Please check the logs above for errors."
}

Write-Host ""
Write-Host ""
Write-BlueOutput "🔧 Next Steps (if needed):"
Write-Host "1. Setup Sample Doc Proc Pipeline using SetupSamplePipeline.ps1 script"
Write-Host "   pwsh .\doc-proc-deploy\SetupSamplePipeline.ps1 -ResourceGroup '$ResourceGroup' -Environment '$Environment'"
Write-Host ""