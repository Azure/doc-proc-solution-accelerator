#!/bin/bash

# Complete Deployment Example
# This script demonstrates the full deployment process using local source files

set -e

# Configuration - Update these values for your deployment
RESOURCE_GROUP="rg-docproc-dev"
LOCATION="eastus"
NAME_PREFIX="docproc"
ENVIRONMENT="dev"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Complete Deployment: Document Processing Solution${NC}"
echo -e "${BLUE}Using local source files for container builds${NC}"
echo ""

# Step 1: Deploy Azure Infrastructure
echo -e "${YELLOW}Step 1: Deploying Azure Infrastructure...${NC}"
./deploy-azure-infra.sh \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --name-prefix "$NAME_PREFIX" \
    --environment "$ENVIRONMENT"

if [ $? -ne 0 ]; then
    echo "❌ Infrastructure deployment failed"
    exit 1
fi

# Get deployment outputs
echo -e "${YELLOW}Retrieving deployment information...${NC}"
REGISTRY_NAME=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[0].name" --output tsv)
BACKEND_APP_NAME=$(az containerapp list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, 'backend')].name" --output tsv)

echo "Registry: $REGISTRY_NAME"
echo "Backend App: $BACKEND_APP_NAME"

# Step 2: Build and Deploy Backend
echo -e "${YELLOW}Step 2: Building and Deploying Backend...${NC}"
export RESOURCE_GROUP_NAME="$RESOURCE_GROUP"
export REGISTRY_NAME="$REGISTRY_NAME"
export BACKEND_APP_NAME="$BACKEND_APP_NAME"

./build-backend.sh

# Step 3: Optional - Deploy Worker (if needed)
echo -e "${YELLOW}Step 3: Building Worker (Optional)...${NC}"
echo "To deploy the worker, run:"
echo "cd ../doc-proc-worker"
echo "az acr build --registry $REGISTRY_NAME --image doc-proc-worker:latest ."

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}Your application is now deployed:${NC}"

# Get backend URL
BACKEND_URL=$(az containerapp show --name "$BACKEND_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" --output tsv)
if [ -n "$BACKEND_URL" ]; then
    echo -e "${GREEN}Backend API: https://$BACKEND_URL${NC}"
    echo -e "${GREEN}Health Check: https://$BACKEND_URL/health${NC}"
    echo -e "${GREEN}API Documentation: https://$BACKEND_URL/docs${NC}"
fi

echo ""
echo -e "${BLUE}To redeploy the backend after code changes:${NC}"
echo "export RESOURCE_GROUP_NAME=\"$RESOURCE_GROUP\""
echo "export REGISTRY_NAME=\"$REGISTRY_NAME\""  
echo "export BACKEND_APP_NAME=\"$BACKEND_APP_NAME\""
echo "./build-backend.sh"