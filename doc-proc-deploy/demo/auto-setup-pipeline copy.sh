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
SUBSCRIPTION=""
INPUT_CONTAINER="documents"
OUTPUT_CONTAINER="output"
DRY_RUN="false"
DEBUG="false"

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/setup-pipeline.py"

# Print functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

print_header() {
    echo -e "${BLUE}🚀 Auto-Setup Pipeline Configuration${NC}"
}

# Function to show usage
usage() {
    echo "Usage: $0 -g <resource-group> [options]"
    echo ""
    echo "Required:"
    echo "  -g, --resource-group    Azure Resource Group name"
    echo ""
    echo "Optional:"
    echo "  -s, --subscription      Azure subscription ID"
    echo "  --input-container       Input container name (default: documents)"
    echo "  --output-container      Output container name (default: output)"
    echo "  --dry-run              Show configuration without executing setup"
    echo "  -d, --debug            Enable debug logging"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -g rg-pwsh-02"
    echo "  $0 -g rg-pwsh-02 -s 12345678-1234-1234-1234-123456789012"
    echo "  $0 -g rg-pwsh-02 --input-container documents --output-container processed --dry-run"
    echo ""
    exit 1
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI (az) is not installed or not in PATH"
        echo "Please install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    # Check if jq is installed (needed for JSON parsing)
    if ! command -v jq &> /dev/null; then
        print_error "jq is not installed or not in PATH"
        echo "Please install jq for JSON parsing: https://stedolan.github.io/jq/download/"
        exit 1
    fi
    
    # Check if curl is installed (needed for API health check)
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed or not in PATH"
        echo "Please install curl for API connectivity testing"
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        echo "Please install Python 3: https://www.python.org/downloads/"
        exit 1
    fi
    
    # Check if setup-pipeline.py exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "setup-pipeline.py not found at: $PYTHON_SCRIPT"
        echo "Make sure the Python script is in the same directory as this script"
        exit 1
    fi
    
    # Check if logged into Azure
    if ! az account show &> /dev/null; then
        print_error "Not logged into Azure CLI"
        echo "Please run: az login"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to get API URL from Container App
get_api_url() {
    local resource_group="$1"
    local subscription="$2"
    
    echo -e "${BLUE}Retrieving API URL from Container App - (1/3)...${NC}"
    
    local az_cmd="az containerapp list --resource-group $resource_group --output json"
    if [[ -n "$subscription" ]]; then
        az_cmd="$az_cmd --subscription $subscription"
    fi
    
    local API_RETRY_COUNT=0
    local API_MAX_RETRIES=3
    local container_apps=""
    
    while [ $API_RETRY_COUNT -lt $API_MAX_RETRIES ] && [ -z "$container_apps" ]; do
        API_RETRY_COUNT=$((API_RETRY_COUNT + 1))
        echo -e "${BLUE}Attempt $API_RETRY_COUNT/$API_MAX_RETRIES: Fetching Container Apps...${NC}"
        
        container_apps=$(eval "$az_cmd" 2>/dev/null)
        
        if [[ -z "$container_apps" || "$container_apps" == "[]" ]] && [ $API_RETRY_COUNT -lt $API_MAX_RETRIES ]; then
            echo -e "${YELLOW}⚠️ No container apps found - could be a connectivity issue, retrying in 5 seconds...${NC}"
            sleep 5
            container_apps=""
        fi
    done
    
    if [[ -z "$container_apps" || "$container_apps" == "[]" ]]; then
        print_error "No container apps found in resource group after $API_MAX_RETRIES attempts: $resource_group"
        return 1
    fi
    
    # Look for the API container app (typically contains 'api' in the name)
    local api_fqdn=$(echo "$container_apps" | jq -r '.[] | select(.name | contains("api")) | .properties.configuration.ingress.fqdn' | head -n 1)
    
    if [[ -z "$api_fqdn" || "$api_fqdn" == "null" ]]; then
        # Fallback: get the first container app with ingress enabled
        api_fqdn=$(echo "$container_apps" | jq -r '.[] | select(.properties.configuration.ingress != null) | .properties.configuration.ingress.fqdn' | head -n 1)
    fi
    
    if [[ -z "$api_fqdn" || "$api_fqdn" == "null" ]]; then
        print_error "Could not find API container app with ingress enabled"
        print_info "Available container apps:"
        echo "$container_apps" | jq -r '.[].name'
        return 1
    fi
    
    local api_url="https://$api_fqdn"
    echo -e "${GREEN}✅ API URL: $api_url${NC}"
    echo "$api_url"
}

# Function to get storage account details
get_storage_config() {
    local resource_group="$1"
    local subscription="$2"
    
    echo -e "${BLUE}Retrieving Storage Account configuration - (2/3)...${NC}"
    
    local az_cmd="az storage account list --resource-group $resource_group --output json"
    if [[ -n "$subscription" ]]; then
        az_cmd="$az_cmd --subscription $subscription"
    fi
    
    local STORAGE_RETRY_COUNT=0
    local STORAGE_MAX_RETRIES=3
    local storage_accounts=""
    
    while [ $STORAGE_RETRY_COUNT -lt $STORAGE_MAX_RETRIES ] && [ -z "$storage_accounts" ]; do
        STORAGE_RETRY_COUNT=$((STORAGE_RETRY_COUNT + 1))
        echo -e "${BLUE}Attempt $STORAGE_RETRY_COUNT/$STORAGE_MAX_RETRIES: Fetching Storage Accounts...${NC}"
        
        storage_accounts=$(eval "$az_cmd" 2>/dev/null)
        
        if [[ -z "$storage_accounts" || "$storage_accounts" == "[]" ]] && [ $STORAGE_RETRY_COUNT -lt $STORAGE_MAX_RETRIES ]; then
            echo -e "${YELLOW}⚠️ No storage accounts found - could be a connectivity issue, retrying in 5 seconds...${NC}"
            sleep 5
            storage_accounts=""
        fi
    done
    
    if [[ -z "$storage_accounts" || "$storage_accounts" == "[]" ]]; then
        print_error "No storage accounts found in resource group after $STORAGE_MAX_RETRIES attempts: $resource_group"
        return 1
    fi
    
    # Get the first storage account (or look for one with 'docproc' in the name)
    local storage_account_name=$(echo "$storage_accounts" | jq -r '.[] | select(.name | contains("docproc")) | .name' | head -n 1)
    
    if [[ -z "$storage_account_name" || "$storage_account_name" == "null" ]]; then
        # Fallback: get the first storage account
        storage_account_name=$(echo "$storage_accounts" | jq -r '.[0].name')
    fi
    
    if [[ -z "$storage_account_name" || "$storage_account_name" == "null" ]]; then
        print_error "Could not find storage account"
        return 1
    fi
    
    echo -e "${GREEN}✅ Storage Account: $storage_account_name${NC}"
    
    # Get storage account key with retry logic
    echo -e "${BLUE}Fetching Storage Account key...${NC}"
    
    local key_cmd="az storage account keys list --account-name $storage_account_name --resource-group $resource_group --output json"
    if [[ -n "$subscription" ]]; then
        key_cmd="$key_cmd --subscription $subscription"
    fi
    
    local KEY_RETRY_COUNT=0
    local KEY_MAX_RETRIES=3
    local storage_key=""
    
    while [ $KEY_RETRY_COUNT -lt $KEY_MAX_RETRIES ] && [ -z "$storage_key" ]; do
        KEY_RETRY_COUNT=$((KEY_RETRY_COUNT + 1))
        
        storage_key=$(eval "$key_cmd" 2>/dev/null | jq -r '.[0].value' 2>/dev/null)
        
        if [[ -z "$storage_key" || "$storage_key" == "null" ]] && [ $KEY_RETRY_COUNT -lt $KEY_MAX_RETRIES ]; then
            echo -e "${YELLOW}⚠️ Failed to retrieve storage key, retrying in 3 seconds...${NC}"
            sleep 3
            storage_key=""
        fi
    done
    
    if [[ -z "$storage_key" || "$storage_key" == "null" ]]; then
        print_error "Could not retrieve storage account key after $KEY_MAX_RETRIES attempts"
        return 1
    fi
    
    echo -e "${GREEN}✅ Retrieved Storage Account key${NC}"
    
    # Return both account name and key
    echo "$storage_account_name"
    echo "$storage_key"
}

# Function to test API connectivity
test_api_connectivity() {
    local api_url="$1"
    
    echo -e "${BLUE}Testing API connectivity at $api_url - (3/3)...${NC}"
    
    if curl -s -f "$api_url/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is accessible at $api_url${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ API health check failed, but continuing (API might still be starting up)${NC}"
        return 1
    fi
}

# Main function
main() {
    print_header
    echo -e "${BLUE}Resource Group: $RESOURCE_GROUP${NC}"
    if [[ -n "$SUBSCRIPTION" ]]; then
        echo -e "${BLUE}Subscription: $SUBSCRIPTION${NC}"
    fi
    echo -e "${BLUE}Input Container: $INPUT_CONTAINER${NC}"
    echo -e "${BLUE}Output Container: $OUTPUT_CONTAINER${NC}"
    echo ""
    
    # Check if user is logged in to Azure
    if ! az account show &> /dev/null; then
        echo -e "${YELLOW}⚠️ You are not logged in to Azure. Please login first.${NC}"
        az login
    fi

    echo ""
    echo -e "${YELLOW}📋 Current Azure subscription:${NC}"
    az account show --output table
    echo ""
    
    # Check prerequisites
    check_prerequisites
    echo ""
    
    echo -e "${BLUE}Retrieving required parameters for pipeline setup...${NC}"
    echo "------------------"
    
    # Get API URL
    API_URL=$(get_api_url "$RESOURCE_GROUP" "$SUBSCRIPTION")
    if [[ $? -ne 0 ]]; then
        exit 1
    fi
    
    # wait for a few seconds to let connections settle
    sleep 2
    
    # Get storage configuration
    storage_config=$(get_storage_config "$RESOURCE_GROUP" "$SUBSCRIPTION")
    if [[ $? -ne 0 ]]; then
        exit 1
    fi
    
    # Parse storage configuration (account name and key are on separate lines)
    STORAGE_ACCOUNT_NAME=$(echo "$storage_config" | sed -n '1p')
    STORAGE_ACCOUNT_KEY=$(echo "$storage_config" | sed -n '2p')
    
    # wait for a few seconds to let connections settle
    sleep 2
    
    # # Test API connectivity
    # test_api_connectivity "$API_URL"
    
    echo ""
    echo -e "${BLUE} Waiting for some seconds to let connections settle...${NC}"
    sleep 3
    
    echo ""
    echo -e "${BLUE}📊 Configuration Retrieved Successfully:${NC}"
    echo "------------------"
    echo -e "  ${GREEN}• API URL:${NC} $API_URL"
    echo -e "  ${GREEN}• Storage Account:${NC} $STORAGE_ACCOUNT_NAME"
    echo -e "  ${GREEN}• Storage Key:${NC} ${STORAGE_ACCOUNT_KEY:0:8}...${STORAGE_ACCOUNT_KEY: -4}"
    echo -e "  ${GREEN}• Input Container:${NC} $INPUT_CONTAINER"
    echo -e "  ${GREEN}• Output Container:${NC} $OUTPUT_CONTAINER"
    echo ""
    
    # Prepare Python script arguments
    PYTHON_ARGS=(
        "--api-url" "$API_URL"
        "--storage-account" "$STORAGE_ACCOUNT_NAME" 
        "--storage-key" "$STORAGE_ACCOUNT_KEY"
        "--input-container" "$INPUT_CONTAINER"
        "--output-container" "$OUTPUT_CONTAINER"
    )
    
    if [[ "$DRY_RUN" == "true" ]]; then
        PYTHON_ARGS+=(--dry-run)
    fi
    
    if [[ "$DEBUG" == "true" ]]; then
        PYTHON_ARGS+=(--debug)
    fi
    
    # Determine Python command
    PYTHON_CMD="python3"
    if ! command -v python3 &> /dev/null; then
        PYTHON_CMD="python"
    fi
    
    # Run the Python setup script
    echo -e "${BLUE}🚀 Running pipeline setup script...${NC}"
    echo "------------------"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}⚠️ DRY RUN MODE - Would execute:${NC}"
        echo "$PYTHON_CMD $PYTHON_SCRIPT ${PYTHON_ARGS[*]}"
        echo ""
        echo -e "${GREEN}✅ Dry run completed successfully${NC}"
        echo ""
        echo -e "${BLUE}🔧 To execute the pipeline setup, run without --dry-run:${NC}"
        echo "$0 -g $RESOURCE_GROUP $([ -n "$SUBSCRIPTION" ] && echo "-s $SUBSCRIPTION") $([ "$INPUT_CONTAINER" != "documents" ] && echo "--input-container $INPUT_CONTAINER") $([ "$OUTPUT_CONTAINER" != "output" ] && echo "--output-container $OUTPUT_CONTAINER")"
        exit 0
    fi
    
    # Execute the Python script
    echo "Executing: $PYTHON_CMD $PYTHON_SCRIPT ${PYTHON_ARGS[*]}"
    echo ""
    exec "$PYTHON_CMD" "$PYTHON_SCRIPT" "${PYTHON_ARGS[@]}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -s|--subscription)
            SUBSCRIPTION="$2"
            shift 2
            ;;
        --input-container)
            INPUT_CONTAINER="$2"
            shift 2
            ;;
        --output-container)
            OUTPUT_CONTAINER="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        -d|--debug)
            DEBUG="true"
            shift
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
    echo -e "${RED}❌ Error: Resource Group is required${NC}"
    usage
fi

# Run main function
main