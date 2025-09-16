<#
.SYNOPSIS
    deploy.ps1 — validate APP_CONFIG_ENDPOINT, load App Config (label=gpt-rag), then build & push

.DESCRIPTION
    - Checks for APP_CONFIG_ENDPOINT in environment; if missing, tries to fetch from `azd env get-values`.
    - Parses App Configuration name from endpoint.
    - Checks Azure CLI login.
    - Fetches required keys (CONTAINER_REGISTRY_NAME, CONTAINER_REGISTRY_LOGIN_SERVER, RESOURCE_GROUP_NAME, DATA_INGEST_APP_NAME) from Azure App Configuration with label "gpt-rag".
      If a key is not found with original casing, tries uppercase.
    - Logs into ACR, builds Docker image (tag from git short HEAD unless $env:tag is set). If local Docker is unavailable, uses `az acr build`.
    - Pushes image and updates the Container App.
.NOTES
    - Requires Azure CLI installed and logged in.
    - Running in PowerShell 5.1+ or PowerShell Core.
#>

#region Helper: color output functions
function Write-Green($msg) {
    Write-Host $msg -ForegroundColor Green
}
function Write-Blue($msg) {
    Write-Host $msg -ForegroundColor Cyan
}
function Write-Yellow($msg) {
    Write-Host $msg -ForegroundColor Yellow
}
function Write-ErrorColored($msg) {
    Write-Host $msg -ForegroundColor Red
}
#endregion

#region Debug toggle
if ($env:DEBUG -eq 'true') {
    $VerbosePreference = 'Continue'
    Write-Verbose "DEBUG mode is ON"
} else {
    $VerbosePreference = 'SilentlyContinue'
}
#endregion

Write-Host ""  # blank line

#region APP_CONFIG_ENDPOINT check
if ($null -ne $env:APP_CONFIG_ENDPOINT -and $env:APP_CONFIG_ENDPOINT.Trim() -ne '') {
    Write-Green "✅ Using APP_CONFIG_ENDPOINT from environment: $($env:APP_CONFIG_ENDPOINT)"
    $APP_CONFIG_ENDPOINT = $env:APP_CONFIG_ENDPOINT.Trim()
} else {
    Write-Blue "🔍 Fetching APP_CONFIG_ENDPOINT from azd env…"
    try {
        $envValues = azd env get-values 2>$null
    } catch {
        $envValues = $null
    }
    if ($envValues) {
        foreach ($line in $envValues -split "`n") {
            if ($line -match '^\s*APP_CONFIG_ENDPOINT\s*=\s*"?([^"]+)"?\s*$') {
                $APP_CONFIG_ENDPOINT = $Matches[1].Trim()
                break
            }
        }
    }
}
if (-not $APP_CONFIG_ENDPOINT) {
    Write-Yellow "⚠️  Missing APP_CONFIG_ENDPOINT."
    Write-Host "  • Set it with: azd env set APP_CONFIG_ENDPOINT <your-endpoint>"
    Write-Host "  • Or in PowerShell: `$env:APP_CONFIG_ENDPOINT = '<your-endpoint>'` before running."
    exit 1
}
Write-Green "✅ APP_CONFIG_ENDPOINT: $APP_CONFIG_ENDPOINT"
Write-Host ""
#endregion

#region Parse configName from endpoint
$configName = $APP_CONFIG_ENDPOINT -replace '^https?://', ''
$configName = $configName -replace '\.azconfig\.io/?$', ''
if (-not $configName) {
    Write-Yellow ("⚠️ Could not parse config name from endpoint '{0}'." -f $APP_CONFIG_ENDPOINT)
    exit 1
}
Write-Green "✅ App Configuration name: $configName"
Write-Host ""
#endregion

#region Azure CLI login check
Write-Blue "🔐 Checking Azure CLI login and subscription…"
try {
    az account show > $null 2>&1
} catch {
    Write-Yellow "⚠️  Not logged in. Please run 'az login'."
    exit 1
}
Write-Green "✅ Azure CLI is logged in."
Write-Host ""
#endregion

#region Fetch App Configuration values
$label = "gpt-rag"
Write-Green "⚙️ Loading App Configuration settings (label=$label)…"
Write-Host ""

function Get-ConfigValue {
    param(
        [Parameter(Mandatory=$true)][string]$Key
    )
    Write-Blue ("🛠️  Retrieving '{0}' (label={1}) from App Configuration…" -f $Key, $label)
    try {
        $val = az appconfig kv show `
            --name $configName `
            --key $Key `
            --label $label `
            --auth-mode login `
            --query value -o tsv 2>&1
        $exitCode = $LASTEXITCODE
    } catch {
        $val = $_.Exception.Message
        $exitCode = 1
    }
    if ($exitCode -ne 0 -or [string]::IsNullOrWhiteSpace($val)) {
        Write-Yellow ("⚠️  Key '{0}' not found or empty. CLI output: {1}" -f $Key, $val)
        return $null
    }
    return $val.Trim()
}

# Define required keys
$keyNames = @('CONTAINER_REGISTRY_NAME', 'CONTAINER_REGISTRY_LOGIN_SERVER', 'SUBSCRIPTION_ID', 'RESOURCE_GROUP_NAME', 'RESOURCE_TOKEN', 'DATA_INGEST_APP_NAME')
$values = @{}
$missing = @()

foreach ($k in $keyNames) {
    $v = Get-ConfigValue -Key $k
    if ($null -eq $v) {
        # try uppercase fallback
        $upperKey = $k.ToUpper()
        if ($upperKey -ne $k) {
            Write-Blue ("🔍 Trying uppercase key '{0}'…" -f $upperKey)
            $v = Get-ConfigValue -Key $upperKey
        }
    }
    if ($null -eq $v) {
        $missing += $k
    } else {
        $values[$k] = $v
    }
}
if ($missing.Count -gt 0) {
    Write-Yellow ("⚠️  Missing or invalid App Config keys: {0}" -f ($missing -join ', '))
    exit 1
}

Write-Green "✅ All App Configuration values retrieved:"
Write-Host ("   CONTAINER_REGISTRY_NAME = {0}" -f $values.CONTAINER_REGISTRY_NAME)
Write-Host ("   CONTAINER_REGISTRY_LOGIN_SERVER = {0}" -f $values.CONTAINER_REGISTRY_LOGIN_SERVER)
Write-Host ("   RESOURCE_GROUP_NAME = {0}" -f $values.RESOURCE_GROUP_NAME)
Write-Host ("   DATA_INGEST_APP_NAME = {0}" -f $values.DATA_INGEST_APP_NAME)
Write-Host ""
#endregion

#region Login to ACR
Write-Green ("🔐 Logging into ACR ({0})…" -f $values.CONTAINER_REGISTRY_NAME)
try {
    az acr login --name $values.CONTAINER_REGISTRY_NAME --resource-group $values.RESOURCE_GROUP_NAME
    Write-Green "✅ Logged into ACR."
} catch {
    $errMsg = $_.Exception.Message
    Write-Yellow ("⚠️  Failed to login to ACR: {0}" -f $errMsg)
    exit 1
}
Write-Host ""
#endregion

#region Determine tag
Write-Blue "🛢️ Defining tag…"
if ($env:tag) {
    $tag = $env:tag.Trim()
    Write-Verbose ("Using tag from environment: {0}" -f $tag)
} else {
    try {
        $gitTag = & git rev-parse --short HEAD 2>$null
        if ($LASTEXITCODE -eq 0 -and $gitTag) {
            $tag = $gitTag.Trim()
        } else {
            Write-Yellow "⚠️  Could not get git short HEAD. Please set environment variable `tag`."
            exit 1
        }
    } catch {
        $errMsg = $_.Exception.Message
        Write-Yellow ("⚠️  Error running git: {0}" -f $errMsg)
        exit 1
    }
}
Write-Green ("✅ tag set to: {0}" -f $tag)
Write-Host ""
#endregion

#region Build or ACR build image
$fullImageName = "$($values.CONTAINER_REGISTRY_LOGIN_SERVER)/azure-gpt-rag/data-ingestion:$tag"
Write-Green "🛠️  Building Docker image…"
if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        docker build -t $fullImageName ./doc-proc-lib
        Write-Green "✅ Docker build succeeded."
    } catch {
        $errMsg = $_.Exception.Message
        Write-Yellow ("⚠️  Docker build failed: {0}" -f $errMsg)
        exit 1
    }
} else {
    Write-Blue "⚠️  Docker CLI not found locally. Falling back to 'az acr build'."
    try {
        az acr build `
            --registry $values.CONTAINER_REGISTRY_NAME `
            --image "azure-gpt-rag/data-ingestion:$tag" `
            --file Dockerfile `
            .
        Write-Green "✅ ACR cloud build succeeded."
    } catch {
        $errMsg = $_.Exception.Message
        Write-Yellow ("⚠️  ACR build failed: {0}" -f $errMsg)
        exit 1
    }
}
Write-Host ""
#endregion

#region Push Docker image (if local build used)
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Green "📤 Pushing image…"
    try {
        docker push $fullImageName
        Write-Green "✅ Image pushed."
    } catch {
        $errMsg = $_.Exception.Message
        Write-Yellow ("⚠️  Docker push failed: {0}" -f $errMsg)
        exit 1
    }
    Write-Host ""
} else {
    # If using az acr build, image is already in ACR
    Write-Green "ℹ️  Image built in ACR; no local push needed."
    Write-Host ""
}
#endregion

#Make sure container registry is registered
Write-Green "🔄 Updating container app registry…"
try {
    $ids = $(az containerapp identity show `
        --name $values.DATA_INGEST_APP_NAME `
        --resource-group $values.RESOURCE_GROUP_NAME `
        --output json) | ConvertFrom-Json

    if ($ids.type.tostring().contains("UserAssigned"))
    {
        az containerapp registry set `
            --name $values.DATA_INGEST_APP_NAME `
            --resource-group $values.RESOURCE_GROUP_NAME `
            --server "$($values.CONTAINER_REGISTRY_NAME).azurecr.io" `
            --identity "/subscriptions/$($values.SUBSCRIPTION_ID)/resourceGroups/$($values.RESOURCE_GROUP_NAME)/providers/Microsoft.ManagedIdentity/userAssignedIdentities/uai-ca-$($values.RESOURCE_TOKEN)-dataingest" `
    }
    else {
        az containerapp registry set `
        --name $values.DATA_INGEST_APP_NAME `
        --resource-group $values.RESOURCE_GROUP_NAME `
        --server "$($values.CONTAINER_REGISTRY_NAME).azurecr.io" `
        --identity "system"
    }
    

    Write-Green "✅ Container app updated."
} catch {
    $errMsg = $_.Exception.Message
    Write-Yellow ("⚠️  Failed to update container app: {0}" -f $errMsg)
    exit 1
}

#region Update Container App
Write-Green "🔄 Updating container app…"
try {
    az containerapp update `
        --name $values.DATA_INGEST_APP_NAME `
        --resource-group $values.RESOURCE_GROUP_NAME `
        --image $fullImageName
    Write-Green "✅ Container app updated."
} catch {
    $errMsg = $_.Exception.Message
    Write-Yellow ("⚠️  Failed to update container app: {0}" -f $errMsg)
    exit 1
}

#get the current revision
Write-Blue "🔍 Fetching current revision…"
$currentRevision = az containerapp revision list `
    --name $values.DATA_INGEST_APP_NAME `
    --resource-group $values.RESOURCE_GROUP_NAME `
    --query "[0].name" -o tsv

#region Restart Container App
Write-Green "🔄 Restarting container app revision : $currentRevision…"
try {
    az containerapp revision restart `
        --name $values.DATA_INGEST_APP_NAME `
        --resource-group $values.RESOURCE_GROUP_NAME `
        --revision $currentRevision

    Write-Green "✅ Container app revision restarted."
} catch {
    $errMsg = $_.Exception.Message
    Write-Yellow ("⚠️  Failed to restart container app: {0}" -f $errMsg)
    exit 1
}
#endregion
