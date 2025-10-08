# Doc Processing Solution - Deployment Scripts

This directory contains all the deployment scripts and configuration files for the Document Processing Solution. The solution can be deployed using Docker containers, run locally for development, or deployed to Microsoft Azure.

## 🏗️ Architecture

The solution consists of four main components:

- **doc-proc-api**: FastAPI backend service (port 8090) - Built and deployed via Azure Container Registry tasks
- **doc-proc-worker**: Background worker for async processing
- **doc-proc-crawler**: Distributed crawler with intelligent source discovery and lease-based coordination
- **doc-proc-web**: React frontend application (port 8080)

## 📁 Project Structure

```
doc-proc-solution-accelerator/
├── doc-proc-deploy/                # 👈 All deployment scripts are here
│   ├── start-services-locally.sh   # Start services locally for development
│   ├── deploy-azure-infra.sh       # Deploy Azure infrastructure (Bash)
│   ├── DeployAzureInfra.ps1      # Deploy Azure infrastructure (PowerShell)
│   ├── build-and-push-images.sh    # Build and push images to ACR (Bash)
│   ├── BuildAndPushImages.ps1   # Build and push images to ACR (PowerShell)
│   ├── deploy-apps.sh              # Deploy applications to Azure (Bash)
│   ├── DeployApps.ps1             # Deploy applications to Azure (PowerShell)
│   ├── infra/
│   │   └── bicep/                  # Azure Bicep templates
│   └── README.md                   # This file
├── doc-proc-api/                   # API service
│   └── Dockerfile                  # API Dockerfile
├── doc-proc-worker/                # Worker service
│   └── Dockerfile                  # Worker Dockerfile
├── doc-proc-crawler/               # Crawler service with distributed architecture
│   └── Dockerfile                  # Crawler Dockerfile
├── doc-proc-web/                   # Frontend service
│   └── Dockerfile                  # Frontend Dockerfile
└── ...
```

## 🚀 Quick Start

### Option 1: Azure Cloud Deployment (PowerShell)

1. **Deploy infrastructure:**
   ```powershell
   pwsh .\doc-proc-deploy\DeployAzureInfra.ps1 -ResourceGroup myResourceGroup -Location westus -NamePrefix docproc
   ```

2. **Build and push images:**
   ```powershell
   pwsh .\doc-proc-deploy\BuildAndPushImages.ps1 -Registry myproject.azurecr.io -Tag latest
   ```

3. **Deploy applications:**
   ```powershell
   pwsh .\doc-proc-deploy\DeployApps.ps1 -ResourceGroup myResourceGroup
   ```

### Option 2: Azure Cloud Deployment (Bash)

1. **Deploy infrastructure:**
   ```bash
   ./doc-proc-deploy/deploy-azure-infra.sh -r myResourceGroup -l westus -a westus -p docproc
   ```

2. **Build and push images:**
   ```bash
   ./doc-proc-deploy/build-and-push-images.sh -r myResourceGroup -t latest
   ```

3. **Deploy applications:**
   ```bash
   ./doc-proc-deploy/deploy-apps.sh -r myResourceGroup -p myProject
   ```

### Option 3: 🔧 Local Development (after deployment to Azure)
Once the Azure resources are deployed, you can run the solution services locally for development:

**Start all services locally:**
```powershell
cd doc-proc-solution-accelerator

# Configure environment variables for each service
# Copy .env.example to .env and update with your Azure resource endpoints
cp doc-proc-api\.env.example doc-proc-api\.env
cp doc-proc-worker\.env.example doc-proc-worker\.env
cp doc-proc-web\.env.example doc-proc-web\.env

# Edit the .env files with your Azure resource information:
# doc-proc-api\.env - Add Azure App Configuration endpoint
# doc-proc-worker\.env - Add Azure App Configuration endpoint
# doc-proc-web\.env - Update API base URL if different from http://localhost:8090

# Start all services locally with auto-reload
.\doc-proc-deploy\StartServicesLocally.ps1
```

**Access the application:**
   - Frontend: http://localhost:8080 (Vite dev server)
   - Backend API: http://localhost:8090

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `DeployAzureInfra.ps1` or `deploy-azure-infra.sh` | Deploy Azure infrastructure |
| `BuildAndPushImages.ps1` or `build-and-push-images.sh` | Build and push Docker images |
| `DeployApps.ps1` or `deploy-apps.sh` | Deploy applications to Azure |

### Script Parameters

#### `DeployAzureInfra.ps1`
```powershell
# Required
-ResourceGroup         # Azure Resource Group name

# Optional  
-Location              # Azure region (default: westus)
-AIFoundryLocation     # Azure AI Foundry Location (default: westus)
-NamePrefix            # Resource name prefix (default: docproc)
-Environment           # Environment name (default: dev)
-Help                  # Show detailed help
```

#### `BuildAndPushImages.ps1`
```powershell
# Required
-Registry       # Azure Container Registry login server

# Optional
-Tag           # Image tag (default: latest)
-Api           # Build only API component
-Worker        # Build only Worker component  
-Crawler       # Build only Crawler component
-Web           # Build only Web component
-Help          # Show detailed help
```

#### `DeployApps.ps1`
```powershell
# Required (one of these)
-ResourceGroup  # Resource group name

# Optional
-NamePrefix    # Resource name prefix
-Environment   # Environment name (default: dev)
-Tag           # Image tag (default: latest)
-App           # Deploy API and WEB apps
-Worker        # Deploy only Worker component
-Crawler       # Deploy only Crawler component
-Help          # Show detailed help
```

## 📚 Additional Resources

- [Project README](../README.md)
