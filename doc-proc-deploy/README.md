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


## Infrastructure Deployment

### Azure Bicep Infrastructure as Code

The document processing solution uses Azure Bicep for Infrastructure as Code (IaC) deployment. The main deployment template is located at `/doc-proc-deploy/infra/bicep/main.bicep` and orchestrates the provisioning of all required Azure resources for the complete solution.

#### Main Bicep Template Overview

The `main.bicep` template deploys a comprehensive, enterprise-ready document processing infrastructure with the following Azure services:

**Core Infrastructure Components:**
- **User Assigned Managed Identity** - Provides secure, passwordless authentication between services
- **Log Analytics Workspace** - Centralized logging and monitoring for all components
- **Application Insights** - Application performance monitoring and telemetry
- **Container Apps Environment** - Serverless container hosting platform for scalable workloads

**Data & Storage Services:**
- **Azure Cosmos DB** - NoSQL database with multiple containers for pipelines, catalogs, executions, and document metadata
- **Azure Storage Account** - Blob storage for documents and queues for asynchronous processing
- **Azure Container Registry** - Private container image registry for application deployments

**AI & Configuration Services:**
- **Azure AI Foundry** - AI/ML services integration for document processing capabilities
- **App Configuration Store** - Centralized configuration management with environment-specific settings

#### Deployment Parameters

The template accepts the following key parameters for customization:

**Environment Configuration:**
```bicep
@description('Name prefix for all resources')
param namePrefix string = 'docproc'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location
```

**Document Processing Configuration:**
```bicep
@description('Cosmos DB database name')
param cosmosDbName string = 'docproc'

@description('Name of the blob storage container for vault documents')
param vaultsContainerName string = 'vaults'

@description('Name of the storage queue for document processing requests')
param docprocExecutionsQueueName string = 'docproc-execution-requests'
```

**AI Services Configuration:**
```bicep
@description('Location for AI Foundry resources')
param aiFoundryLocation string = resourceGroup().location
```

#### Cosmos DB Container Structure

The template automatically provisions the following Cosmos DB containers with optimized partition keys:

- `pipelines` - Document processing pipeline definitions
- `service_catalog` - Available processing services registry
- `service_instances` - Active service instance configurations  
- `step_catalog` - Pipeline step definitions and metadata
- `step_instances` - Runtime step instance configurations
- `source_catalog` - Document source type definitions
- `source_instances` - Active document source configurations
- `vaults` - Document vault metadata and settings
- `vault_documents` - Individual document records and metadata
- `batch_executions` - Batch processing execution tracking
- `pipeline_executions` - Individual pipeline execution records
- `crawl_leases` - Distributed crawler coordination locks
- `crawl_executions` - Crawler execution history and metrics

#### Application Configuration

The deployment automatically configures environment-specific settings through Azure App Configuration:

**API Service Configuration:**
- Debug mode settings
- Blob storage integration parameters
- Container and account configurations

**Worker Service Configuration:**
- Worker pool size and scaling settings
- Shutdown timeout and restart policies
- Health check intervals and thresholds

**Crawler Service Configuration:**
- Maximum concurrent worker limits
- Discovery polling intervals
- Lease duration and renewal settings

**Shared Configuration:**
- Cosmos DB connection endpoints
- Storage queue URLs and connection strings
- Application Insights instrumentation keys

#### Deployment Outputs

The template provides essential outputs for integration with application deployments:

```bicep
// Identity and Security
output userAssignedIdentityName string
output userAssignedIdentityPrincipalId string
output userAssignedIdentityClientId string

// Container Infrastructure  
output containerRegistryName string
output containerRegistryLoginServer string
output containerAppsEnvironmentId string

// Data Services
output storageAccountName string
output cosmosAccountName string

// Configuration
output appConfigStoreName string
output appConfigStoreEndpoint string

// AI Services
output aiProjectName string
output aiServicesName string
```

#### Environment-Specific Features

The template includes environment-aware configurations:

- **Production Environment**: Enables zone redundancy for Cosmos DB for high availability
- **Development/Staging**: Uses cost-optimized configurations with single-region deployment
- **Resource Naming**: Generates unique resource names using resource group ID hashing
- **Tagging Strategy**: Consistent tagging for environment identification and cost tracking


## 📚 Additional Resources

- [Project README](../README.md)
