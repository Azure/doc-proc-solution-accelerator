#!/bin/bash

# Doc Processing Solution - Auto-Setup Pipeline Script
# This script fetches configuration from a deployed Azure resource group
# and runs the setup-pipeline.py script with the correct parameters

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RESOURCE_GROUP=""

# Function to show usage
usage() {
    echo "Usage: $0 -g <resource-group> [options]"
    echo ""
    echo "Required:"
    echo "  -g, --resource-group   Azure Resource Group"
    echo ""
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -g my-resource-group"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [ -z "$RESOURCE_GROUP" ]; then
    echo -e "${RED}❌ Error: Resource group is required${NC}"
    usage
fi

echo -e "${BLUE}🚀 Auto-Setup Pipeline Configuration${NC}"
echo ""


# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️ You are not logged in to Azure. Please login first.${NC}"
    az login
fi

echo ""
echo -e "${YELLOW}📋 Current Azure subscription:${NC}"
az account show --output table
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHON_SCRIPT="${SCRIPT_DIR}/setup-pipeline.py"
PYTHON_REQUIREMENTS="${SCRIPT_DIR}/requirements.txt"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}📁 Moving to Project Root: $PROJECT_ROOT${NC}"
# Change to project root
cd "$PROJECT_ROOT"

# install the required Python packages
echo ""
echo -e "${BLUE}Installing required Python packages...${NC}"
pip install -r "$PYTHON_REQUIREMENTS"

echo ""
echo -e "${BLUE}Retrieving required parameters for setup...${NC}"
echo "------------------"


echo -e "${BLUE}Retrieving App Configuration - (1/3)...${NC}"
# retrieve the App Configuration endpoint from the infra deployment
APP_CONFIG_STORE="$(az appconfig show --name $(az deployment group show --resource-group $RESOURCE_GROUP --name $(az deployment group list --resource-group $RESOURCE_GROUP --query "[?contains(name, 'doc-proc-infra')].name | [0]" --output tsv) --query "properties.outputs.appConfigStoreName.value" --output tsv) --query name --output tsv)"
if [ -z "$APP_CONFIG_STORE" ]; then
    echo -e "${RED}❌ App Configuration Store not found. Please run deploy-azure-infra.sh first.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ App Configuration Store: $APP_CONFIG_STORE${NC}"
fi

echo ""
echo -e "${BLUE}Retrieving API URL - (2/3)...${NC}"
API_APP_NAME=$(az containerapp list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, 'api')].name | [0]" --output tsv)
if [[ -n "$API_APP_NAME" ]]; then
    API_URL=$(az containerapp show \
                --name "$API_APP_NAME" \
                --resource-group "$RESOURCE_GROUP" \
                --query "properties.configuration.ingress.fqdn" \
                --output tsv)
    
    if [[ -n "$API_URL" ]]; then
        echo -e "${GREEN}✅ API URL: https://$API_URL${NC}"
    else
        echo -e "${RED}❌ API URL not found. Please check your deployment.${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ API App Name not found. Please check your deployment.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Retrieving Storage Account - (3/3)...${NC}"
STORAGE_ACCOUNT_NAME=$(az appconfig kv show --name "$APP_CONFIG_STORE" --key "doc-proc.api.BLOB_STORAGE_ACCOUNT_NAME" --query "value" --output tsv)
if [[ -n "$STORAGE_ACCOUNT_NAME" ]]; then
    echo -e "${GREEN}✅ Storage Account Name: $STORAGE_ACCOUNT_NAME${NC}"
else
    echo -e "${RED}❌ Storage Account Name not found in App Configuration. Please check your deployment.${NC}"
    exit 1
fi

echo "------------------"
echo ""
echo -e "${BLUE}Running setup-pipeline.py with retrieved parameters...${NC}"
echo ""

# Run the Python script with the retrieved parameters
python3 "$PYTHON_SCRIPT" \
    --api-url "https://$API_URL" \
    --storage-account "$STORAGE_ACCOUNT_NAME"