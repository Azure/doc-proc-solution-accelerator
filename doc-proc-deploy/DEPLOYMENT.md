# Deployment Guide

This guide walks you through deploying the Document Processing Solution Accelerator using Azure Container Apps and Azure Verified Modules (AVM).

## Prerequisites

- Azure CLI installed and logged in
- Azure subscription with necessary permissions
- GitHub repository with your code
- Optional: GitHub Personal Access Token for ACR build triggers

## Architecture Overview

The solution uses a modern container-based architecture:

- **Azure Container Apps Environment**: Managed hosting platform for all containers
- **Azure Container Registry**: Stores container images and handles automated builds
- **Azure Static Web Apps**: Hosts the React frontend application
- **Azure Cosmos DB**: Document storage
- **Azure App Configuration**: Runtime configuration management
- **Azure Storage Account**: Blob storage for documents
- **Azure Log Analytics**: Centralized logging
- **Azure Application Insights**: Application monitoring

## Deployment Steps

### 1. Prepare Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd doc-proc-solution-accelerator/doc-proc-deploy

# Login to Azure
az login

# Set subscription (optional)
az account set --subscription <subscription-id>
```

### 2. Configure Parameters

Edit the `infra/main.parameters.json` file with your specific values:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "applicationName": {
      "value": "your-app-name"
    },
    "environment": {
      "value": "dev"
    },
    "location": {
      "value": "eastus"
    },
    "containerRegistryAdminEnabled": {
      "value": true
    },
    "gitHubRepoUrl": {
      "value": "https://github.com/your-username/your-repo"
    },
    "gitHubToken": {
      "value": "ghp_your_token_here"
    }
  }
}
```

### 3. Deploy Infrastructure

Run the deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Create a resource group
2. Deploy the main Bicep template
3. Set up all Azure resources
4. Configure Container Apps Environment
5. Create ACR build tasks for the backend

### 4. Verify Deployment

Check the deployment status:

```bash
# List resources in the resource group
az resource list --resource-group rg-your-app-name-dev --output table

# Check Container Apps status
az containerapp list --resource-group rg-your-app-name-dev --output table

# Check ACR build tasks
az acr task list --registry your-app-name-dev-acr --output table
```

## Container Image Building

### Backend Service (Local Source Build)

The backend service now uses local source files for building images. Here are the two main approaches:

#### Option 1: Manual ACR Build (Recommended)
Build and deploy the backend directly from local source:

```bash
# Set environment variables
export RESOURCE_GROUP_NAME="rg-your-app-name-dev"
export REGISTRY_NAME="your-app-name-dev-acr"
export BACKEND_APP_NAME="ca-your-app-name-dev-backend"

# Build and deploy using the provided script
./build-backend.sh
```

#### Option 2: Direct ACR Build Command
Build the image manually using Azure CLI:

```bash
# Build image using ACR
az acr build \
  --registry your-app-name-dev-acr \
  --image doc-proc-backend:latest \
  --file ../doc-proc-ui/backend-app/Dockerfile \
  ../doc-proc-ui/backend-app

# Update the Container App with new image
az containerapp update \
  --name ca-your-app-name-dev-backend \
  --resource-group rg-your-app-name-dev \
  --image your-app-name-dev-acr.azurecr.io/doc-proc-backend:latest
```

### Worker Service

Deploy the worker service manually:

```bash
# Build and push worker image
cd ../doc-proc-worker
az acr build --registry your-app-name-dev-acr --image doc-proc-worker:latest .

# Update the worker Container App with the new image
az containerapp update \
  --name ca-your-app-name-dev-worker \
  --resource-group rg-your-app-name-dev \
  --image your-app-name-dev-acr.azurecr.io/doc-proc-worker:latest
```

## Application Configuration

After deployment, configure your applications:

1. **Backend Configuration**: Set environment variables in the Container App
2. **Frontend Configuration**: Update API endpoints in the Static Web App
3. **Database Setup**: Initialize Cosmos DB containers if needed

## Monitoring and Troubleshooting

### View Logs

```bash
# Container App logs
az containerapp logs show \
  --name ca-your-app-name-dev-backend \
  --resource-group rg-your-app-name-dev \
  --follow

# ACR task logs
az acr task logs --name backend-build-task --registry your-app-name-dev-acr
```

### Common Issues

1. **Container App not starting**: Check image availability and configuration
2. **Build failures**: Verify Dockerfile and source code structure
3. **Authentication issues**: Ensure managed identity permissions are correct

## Scaling and Updates

### Scale Container Apps

```bash
# Scale backend service
az containerapp update \
  --name ca-your-app-name-dev-backend \
  --resource-group rg-your-app-name-dev \
  --min-replicas 1 \
  --max-replicas 5
```

### Update Images

Use ACR tasks for continuous deployment or manually trigger builds as needed.

## Clean Up

To remove all resources:

```bash
az group delete --name rg-your-app-name-dev --yes --no-wait
```

## Next Steps

- Set up monitoring alerts
- Configure custom domains
- Implement CI/CD pipelines
- Add security scanning
- Configure backup strategies

For more information, see the main README.md file.