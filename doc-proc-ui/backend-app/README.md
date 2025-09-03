# Backend API (FastAPI + Cosmos DB)

FastAPI backend exposing CRUD endpoints for services, steps, and pipelines stored in Azure Cosmos DB. Includes Dockerfile and Bicep templates for deploying to Azure Container Apps.

## Endpoints
- GET /health
- Services: GET /api/services, GET /api/services/{id}, POST /api/services, PUT /api/services/{id}
- Steps: GET /api/steps, GET /api/steps/{id}, POST /api/steps, PUT /api/steps/{id}
- Pipelines: GET /api/pipelines, GET /api/pipelines/{id}, POST /api/pipelines, PUT /api/pipelines/{id}

## Environment variables
- COSMOS_ENDPOINT (or COSMOS_URI)
- COSMOS_KEY
- COSMOS_DB_NAME (default: docproc)
- COSMOS_CONTAINER_SERVICES (default: services)
- COSMOS_CONTAINER_STEPS (default: steps)
- COSMOS_CONTAINER_PIPELINES (default: pipelines)
- ALLOW_ORIGINS (comma-separated for CORS, default: *)

## Local run
```bash
# 1) Create venv and install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) Set env vars (replace with your Cosmos details)
export COSMOS_ENDPOINT="https://<your-account>.documents.azure.com:443/"
export COSMOS_KEY="<key>"
export COSMOS_DB_NAME="docproc"

# 3) Run
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker
```bash
# Build
docker build -t doc-proc-backend:latest .
# Run
docker run -p 8000:8000 \
	-e COSMOS_ENDPOINT \
	-e COSMOS_KEY \
	-e COSMOS_DB_NAME=docproc \
	doc-proc-backend:latest
```

## Deploy to Azure Container Apps via Bicep
```bash
# Optional: set defaults
RESOURCE_GROUP="docproc-rg"
LOCATION="westeurope"
APP_IMAGE="ghcr.io/<org>/doc-proc-backend:latest"  # or other registry image

# Create RG
az group create -n "$RESOURCE_GROUP" -l "$LOCATION"

# Deploy
az deployment group create \
	-g "$RESOURCE_GROUP" \
	-f infra/bicep/main.bicep \
	-p location="$LOCATION" containerImage="$APP_IMAGE" namePrefix="docproc" cosmosDbName="docproc"

# After deploy, find the Container App URL
az containerapp show -n docproc-backend -g "$RESOURCE_GROUP" --query properties.configuration.ingress.fqdn -o tsv
```

Notes:
- The template creates a Cosmos DB account with a SQL database and three containers (`services`, `steps`, `pipelines`) using `/id` as the partition key for simplicity.
- For private registries, extend the Bicep to include registry credentials.
