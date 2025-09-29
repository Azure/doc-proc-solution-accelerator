#!/bin/bash

# Doc Processing Solution - Deploy Applications to Azure
# This script deploys api, web and worker applications to Azure

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RESOURCE_GROUP=""
NAME_PREFIX="docproc"
ENVIRONMENT="dev"
LOCATION="westus2"
TAG="latest"
DEPLOY_API="false"
DEPLOY_WEB="false"
DEPLOY_WORKER="false"
DEPLOY_ALL="true"
DEBUG="false"

# Function to show usage
usage() {
    echo "Usage: $0 -g <resource-group> -r <registry> [options]"
    echo ""
    echo "Required:"
    echo "  -g, --resource-group    Azure Resource Group name"
    echo ""
    echo "Optional:"
    echo "  -p, --name-prefix      Resource name prefix (default: docproc)"
    echo "  -e, --environment      Environment name (default: dev)"
    echo "  -l, --location         Azure location (default: westus2)"
    echo "  -t, --tag              Image tag (default: latest)"
    echo "  --api                  Deploy API app. If specified, only API app will be deployed."
    echo "  --web                  Deploy frontend web app. If specified, only frontend app will be deployed."
    echo "  --worker               Deploy worker app. If specified, only worker app will be deployed."
    echo "  -d, --debug            Enable debug logging"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -g my-rg"
    echo "  $0 -g my-rg -e prod -l swedencentral -t v1.0.0"
    echo "  $0 -g my-rg -e prod -l swedencentral -t v1.0.0 --api --web"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -p|--name-prefix)
            NAME_PREFIX="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        --api)
             DEPLOY_API="true"
             DEPLOY_ALL="false"
            shift 1
            ;;
        --web)
             DEPLOY_WEB="true"
             DEPLOY_ALL="false"
            shift 1
            ;;
        --worker)
             DEPLOY_WORKER="true"
             DEPLOY_ALL="false"
            shift 1
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

echo -e "${BLUE}🚀 Deploying applications to Azure${NC}"
echo -e "${BLUE}Resource Group: $RESOURCE_GROUP${NC}"
echo -e "${BLUE}Registry: $REGISTRY${NC}"
echo -e "${BLUE}Name Prefix: $NAME_PREFIX${NC}"
echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"
echo -e "${BLUE}Image Tag: $TAG${NC}"
echo -e "${BLUE}Location: $LOCATION${NC}"
echo ""

    # Output what will be built
if [ "$DEPLOY_ALL" = "true" ]; then
    echo -e "${BLUE}⚙️  Deploying all apps (api, worker, web)${NC}"
    echo ""
else
    echo -e "${BLUE}⚙️  Deploying selected apps:${NC}"
    [ "$DEPLOY_API" = "true" ] && echo -e "${BLUE}✔️ API${NC}"
    [ "$DEPLOY_WEB" = "true" ] && echo -e "${BLUE}✔️ Web${NC}"
    [ "$DEPLOY_WORKER" = "true" ] && echo -e "${BLUE}✔️ Worker${NC}"
    echo ""
fi

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
echo -e "${BLUE}📁 Moving to Project Root: $PROJECT_ROOT${NC}"
cd "$PROJECT_ROOT"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    exit 1
fi


echo ""
echo -e "${BLUE}Retrieving required parameters for deployment (${ENVIRONMENT})...${NC}"
echo "------------------"
echo -e "${BLUE}Retrieving Container Registry Login Server - (1/5)...${NC}"
# retrieve the ACR login server from the infra deployment
REGISTRY="$(az deployment group show --resource-group $RESOURCE_GROUP --name \
               $(az deployment group list \
               --resource-group $RESOURCE_GROUP \
               --query "[?contains(name, 'doc-proc-infra')].name | [0]" \
               --output tsv) \
             --query "properties.outputs.containerRegistryLoginServer.value" \
             --output tsv)"
if [ -z "$REGISTRY" ]; then
    echo -e "${RED}❌ Container Registry not found. Please run deploy-azure-infra.sh first.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Container Registry: $REGISTRY${NC}"
fi

# wait for a few seconds to let connections settle
sleep 2

echo -e "${BLUE}Retrieving App Configuration endpoint - (2/5)...${NC}"
# retrieve the App Configuration endpoint from the infra deployment
APP_CONFIG_STORE_ENDPOINT="$(az appconfig show --name $(az deployment group show --resource-group $RESOURCE_GROUP --name $(az deployment group list --resource-group $RESOURCE_GROUP --query "[?contains(name, 'doc-proc-infra')].name | [0]" --output tsv) --query "properties.outputs.appConfigStoreName.value" --output tsv) --query endpoint --output tsv)"
if [ -z "$APP_CONFIG_STORE_ENDPOINT" ]; then
    echo -e "${RED}❌ App Configuration Endpoint not found. Please run deploy-azure-infra.sh first.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ App Configuration Endpoint: $APP_CONFIG_STORE_ENDPOINT${NC}"
fi

# wait for a few seconds to let connections settle
sleep 2

# retrieve the User Assigned Identity Client ID from the infra deployment
echo -e "${BLUE}Retrieving User Assigned Identity Client ID - (3/5)...${NC}"
USER_ASSIGNED_IDENTITY_CLIENT_ID="$(az deployment group show --resource-group $RESOURCE_GROUP --name $(az deployment group list --resource-group $RESOURCE_GROUP --query "[?contains(name, 'doc-proc-infra')].name | [0]" --output tsv) --query "properties.outputs.userAssignedIdentityClientId.value" --output tsv)"
if [ -z "$USER_ASSIGNED_IDENTITY_CLIENT_ID" ]; then
    echo -e "${RED}❌ User Assigned Identity Client ID not found. Please run deploy-azure-infra.sh first.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ User Assigned Identity Client ID: $USER_ASSIGNED_IDENTITY_CLIENT_ID${NC}"
fi

# wait for a few seconds to let connections settle
sleep 2

# retrieve the User Assigned Identity Resource ID from the infra deployment
echo -e "${BLUE}Retrieving User Assigned Identity Resource ID - (4/5)...${NC}"
USER_ASSIGNED_IDENTITY_RESOURCE_ID="$(az deployment group show --resource-group $RESOURCE_GROUP --name $(az deployment group list --resource-group $RESOURCE_GROUP --query "[?contains(name, 'doc-proc-infra')].name | [0]" --output tsv) --query "properties.outputs.userAssignedIdentityResourceId.value" --output tsv)"
if [ -z "$USER_ASSIGNED_IDENTITY_RESOURCE_ID" ]; then
    echo -e "${RED}❌ User Assigned Identity Resource ID not found. Please run deploy-azure-infra.sh first.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ User Assigned Identity Resource ID: $USER_ASSIGNED_IDENTITY_RESOURCE_ID${NC}"
fi

# wait for a few seconds to let connections settle
sleep 2


# Get Container Apps Environment ID from infrastructure deployment
echo -e "${BLUE}Retrieving Container Apps Environment ID - (5/5)...${NC}"
CONTAINER_APPS_ENV_ID=""
RETRY_COUNT=0
MAX_RETRIES=3

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ -z "$CONTAINER_APPS_ENV_ID" ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${BLUE}Attempt $RETRY_COUNT/$MAX_RETRIES: Retrieving Container Apps Environment ID...${NC}"

    CONTAINER_APPS_ENV_ID=$(az containerapp env list --resource-group "$RESOURCE_GROUP" --query "[?contains(name, '$NAME_PREFIX')].id | [0]" --output tsv 2>/dev/null)

    if [ -z "$CONTAINER_APPS_ENV_ID" ] && [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo -e "${YELLOW}⚠️ Container Apps Environment not found - could be a connectivity issue, retrying in 5 seconds...${NC}"
        sleep 5
    fi
done

if [ -z "$CONTAINER_APPS_ENV_ID" ]; then
    echo -e "${RED}❌ Container Apps Environment not found after $MAX_RETRIES attempts. Please run deploy-azure-infra.sh first.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Container Apps Environment ID: $CONTAINER_APPS_ENV_ID${NC}"
fi

echo ""
echo -e "${BLUE} Waiting for some seconds to let connections settle...${NC}"
sleep 5


echo ""
# Deploy app using Container Apps template
echo -e "${BLUE}🌐 Deploying Solution Apps...${NC}"
echo "------------------"
optional_args=()
if [ "$DEBUG" == "true" ]; then
  optional_args+=("--debug")
fi


######################################################################
######################################################################
## API APP DEPLOYMENT

if [ "$DEPLOY_ALL" == "true" ] || [ "$DEPLOY_API" == "true" ]; then
    # Deploy API
    echo -e "${BLUE}👷 Deploying API App...${NC}"
    API_DEPLOYMENT_NAME="doc-proc-apps-api-$(date +%s)"

    echo -e "${BLUE}Deploying API App with Bicep template...${NC}"

    # Retry logic for API deployment
    API_RETRY_COUNT=0
    API_MAX_RETRIES=3
    API_SUCCESS=false

    while [ $API_RETRY_COUNT -lt $API_MAX_RETRIES ] && [ "$API_SUCCESS" = false ]; do
        API_RETRY_COUNT=$((API_RETRY_COUNT + 1))
        echo -e "${BLUE}Attempt $API_RETRY_COUNT/$API_MAX_RETRIES: Deploying API App...${NC}"

        if az deployment group create \
            --resource-group "$RESOURCE_GROUP" \
            --template-file "doc-proc-ui/backend-app/infra/bicep/main.bicep" \
            --parameters \
                location="$LOCATION" \
                environment="$ENVIRONMENT" \
                namePrefix="$NAME_PREFIX" \
                containerImage="$REGISTRY/doc-proc-api:$TAG" \
                containerAppsEnvironmentId="$CONTAINER_APPS_ENV_ID" \
                containerRegistryServer="$REGISTRY" \
                appConfigStoreEndpoint="$APP_CONFIG_STORE_ENDPOINT" \
                userAssignedIdentityClientId="$USER_ASSIGNED_IDENTITY_CLIENT_ID" \
                userAssignedIdentityResourceId="$USER_ASSIGNED_IDENTITY_RESOURCE_ID" \
            --name "$API_DEPLOYMENT_NAME" \
            --output table ${optional_args[@]}; then

            echo -e "${GREEN}✅ API App deployed successfully${NC}"

            # Get the Container App name from the deployment outputs
            API_APP_NAME=$(az deployment group show \
                --resource-group "$RESOURCE_GROUP" \
                --name "$API_DEPLOYMENT_NAME" \
                --query "properties.outputs.containerAppName.value" \
                --output tsv)

            # Get the Container App FQDN
            API_URL=$(az containerapp show \
                --name "$API_APP_NAME" \
                --resource-group "$RESOURCE_GROUP" \
                --query "properties.configuration.ingress.fqdn" \
                --output tsv)

            # Force a new app revision to ensure the latest image is pulled
            echo -e "${BLUE}Forcing a new revision to pull the latest image...${NC}"
            az containerapp update \
                --name "${API_APP_NAME}" \
                --resource-group "$RESOURCE_GROUP" \
                --image "${REGISTRY}/doc-proc-api:${TAG}" \
                --output none
            echo -e "${GREEN}✅ Updated Container App to pull latest image${NC}"

            if [ -n "$API_URL" ]; then
                API_URL="https://$API_URL"
                echo -e "${GREEN}API URL: $API_URL${NC}"
            else
                echo -e "${YELLOW}⚠️ Could not retrieve API URL${NC}"
            fi

            API_SUCCESS=true
        else
            echo -e "${RED}❌ API deployment failed (attempt $API_RETRY_COUNT/$API_MAX_RETRIES)${NC}"
            if [ $API_RETRY_COUNT -lt $API_MAX_RETRIES ]; then
                echo -e "${YELLOW}⚠️ Retrying API deployment in 5 seconds...${NC}"
                sleep 5
            fi
        fi
    done

    if [ "$API_SUCCESS" = false ]; then
        echo -e "${RED}❌ API deployment failed after $API_MAX_RETRIES attempts${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️ Skipping API deployment${NC}"
    echo ""
fi


######################################################################
######################################################################
## WEB APP DEPLOYMENT

if [ "$DEPLOY_ALL" == "true" ] || [ "$DEPLOY_WEB" == "true" ]; then
    # Deploy Web App (Frontend)
    echo -e "${BLUE}🌐 Deploying Web App (Frontend)...${NC}"
    WEB_DEPLOYMENT_NAME="doc-proc-apps-web-$(date +%s)"

    WEB_SUCCESS=false
    WEB_RETRY_COUNT=0
    WEB_MAX_RETRIES=3

    while [ $WEB_RETRY_COUNT -lt $WEB_MAX_RETRIES ] && [ "$WEB_SUCCESS" = false ]; do
        WEB_RETRY_COUNT=$((WEB_RETRY_COUNT + 1))
        echo -e "${BLUE}Attempt $WEB_RETRY_COUNT/$WEB_MAX_RETRIES: Deploying Web App...${NC}"

        # Deploy Web App using Bicep template
        if az deployment group create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$WEB_DEPLOYMENT_NAME" \
            --template-file "doc-proc-ui/web-app/infra/bicep/main.bicep" \
            --parameters namePrefix="$NAME_PREFIX" \
                        environment="$ENVIRONMENT" \
                        location="$LOCATION" \
                        containerRegistryServer="$REGISTRY" \
                        containerImage="$REGISTRY/doc-proc-web:$TAG" \
                        backendApiUrl="$API_URL" \
                        containerAppsEnvironmentId="$CONTAINER_APPS_ENV_ID" \
                        userAssignedIdentityResourceId="$USER_ASSIGNED_IDENTITY_RESOURCE_ID" \
            "${optional_args[@]}" \
            --output none; then

            echo -e "${GREEN}✅ Web App deployed successfully${NC}"

            # Get the Container App name from the deployment outputs
            WEB_APP_NAME=$(az deployment group show \
                --resource-group "$RESOURCE_GROUP" \
                --name "$WEB_DEPLOYMENT_NAME" \
                --query "properties.outputs.containerAppName.value" \
                --output tsv)

            # Get Web App URL
            WEB_URL=$(az containerapp show \
                --name "${WEB_APP_NAME}" \
                --resource-group "$RESOURCE_GROUP" \
                --query "properties.configuration.ingress.fqdn" \
                --output tsv 2>/dev/null)

            # Force a new app revision to ensure the latest image is pulled
            echo -e "${BLUE}Forcing a new revision to pull the latest image...${NC}"
            az containerapp update \
                --name "${WEB_APP_NAME}" \
                --resource-group "$RESOURCE_GROUP" \
                --image "${REGISTRY}/doc-proc-web:${TAG}" \
                --output none
            echo -e "${GREEN}✅ Updated Container App to pull latest image${NC}"

            if [ -n "$WEB_URL" ]; then
                WEB_URL="https://$WEB_URL"
                echo -e "${GREEN}Web App URL: $WEB_URL${NC}"
            else
                echo -e "${YELLOW}⚠️ Could not retrieve Web App URL${NC}"
            fi

            WEB_SUCCESS=true
        else
            echo -e "${RED}❌ Web App deployment failed (attempt $WEB_RETRY_COUNT/$WEB_MAX_RETRIES)${NC}"
            if [ $WEB_RETRY_COUNT -lt $WEB_MAX_RETRIES ]; then
                echo -e "${YELLOW}⚠️ Retrying Web App deployment in 5 seconds...${NC}"
                sleep 5
            fi
        fi
    done

    if [ "$WEB_SUCCESS" = false ]; then
        echo -e "${RED}❌ Web App deployment failed after $WEB_MAX_RETRIES attempts${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️ Skipping Web App deployment${NC}"
    echo ""
fi


######################################################################
######################################################################
## WORKER APP DEPLOYMENT

if [ "$DEPLOY_ALL" == "true" ] || [ "$DEPLOY_WORKER" == "true" ]; then
    # Deploy Worker
    echo -e "${BLUE}👷 Deploying Worker App...${NC}"
    WORKER_DEPLOYMENT_NAME="doc-proc-apps-worker-$(date +%s)"

    echo -e "${BLUE}Deploying Worker App with Bicep template...${NC}"

    # Retry logic for API deployment
    WORKER_RETRY_COUNT=0
    WORKER_MAX_RETRIES=3
    WORKER_SUCCESS=false

    while [ $WORKER_RETRY_COUNT -lt $WORKER_MAX_RETRIES ] && [ "$WORKER_SUCCESS" = false ]; do
        WORKER_RETRY_COUNT=$((WORKER_RETRY_COUNT + 1))
        echo -e "${BLUE}Attempt $WORKER_RETRY_COUNT/$WORKER_MAX_RETRIES: Deploying Worker App...${NC}"

        if az deployment group create \
            --resource-group "$RESOURCE_GROUP" \
            --template-file "doc-proc-worker/infra/bicep/main.bicep" \
            --parameters \
                location="$LOCATION" \
                environment="$ENVIRONMENT" \
                namePrefix="$NAME_PREFIX" \
                containerImage="$REGISTRY/doc-proc-worker:$TAG" \
                containerAppsEnvironmentId="$CONTAINER_APPS_ENV_ID" \
                containerRegistryServer="$REGISTRY" \
                appConfigStoreEndpoint="$APP_CONFIG_STORE_ENDPOINT" \
                userAssignedIdentityClientId="$USER_ASSIGNED_IDENTITY_CLIENT_ID" \
                userAssignedIdentityResourceId="$USER_ASSIGNED_IDENTITY_RESOURCE_ID" \
            --name "$WORKER_DEPLOYMENT_NAME" \
            --output table ${optional_args[@]}; then

            echo -e "${GREEN}✅ Worker App deployed successfully${NC}"

            WORKER_APP_NAME=$(az deployment group show \
                --resource-group "$RESOURCE_GROUP" \
                --name "$WORKER_DEPLOYMENT_NAME" \
                --query "properties.outputs.containerAppName.value" \
                --output tsv)

            # Force a new app revision to ensure the latest image is pulled
            echo -e "${BLUE}Forcing a new revision to pull the latest image...${NC}"
            az containerapp update \
                --name "${WORKER_APP_NAME}" \
                --resource-group "$RESOURCE_GROUP" \
                --image "${REGISTRY}/doc-proc-worker:${TAG}" \
                --output none
            echo -e "${GREEN}✅ Restarted Container App to pull latest image${NC}"

            WORKER_SUCCESS=true
            echo -e "${GREEN}✅ Worker App deployed successfully${NC}"

        else
            echo -e "${RED}❌ Worker deployment failed (attempt $WORKER_RETRY_COUNT/$WORKER_MAX_RETRIES)${NC}"
            if [ $WORKER_RETRY_COUNT -lt $WORKER_MAX_RETRIES ]; then
                echo -e "${YELLOW}⚠️ Retrying Worker deployment in 5 seconds...${NC}"
                sleep 5
            fi
        fi
    done

    if [ "$WORKER_SUCCESS" = false ]; then
        echo -e "${RED}❌ Worker deployment failed after $WORKER_MAX_RETRIES attempts${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️ Skipping Worker deployment${NC}"
    echo ""
fi


echo ""
echo -e "${GREEN}🎉 Application deployment completed!${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Summary:${NC}"
if [ "$API_SUCCESS" = true ]; then
    echo -e "${GREEN}✅ API App: $API_URL${NC}"
    echo -e "${GREEN}   Health Check: $API_URL/api/health${NC}"
    echo -e "${GREEN}   API Docs: $API_URL/docs${NC}"
fi
if [ "$WEB_SUCCESS" = true ]; then
    echo -e "${GREEN}✅ Web App: $WEB_URL${NC}"
fi
if [ "$WORKER_SUCCESS" = true ]; then
echo -e "${GREEN}✅ Worker: Container App deployed${NC}"
fi
echo ""
echo ""
echo -e "${BLUE}🔧 Next Steps (if needed):${NC}"
echo "1. Update environment variables for your applications"
echo "2. Set up custom domains and SSL certificates"
echo "3. Configure monitoring and logging"
echo ""