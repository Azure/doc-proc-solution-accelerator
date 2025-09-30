# Doc Processing Solution - Deployment Scripts

This directory contains all the deployment scripts and configuration files for the Document Processing Solution. The solution can be deployed using Docker containers, run locally for development, or deployed to Microsoft Azure.

## 🏗️ Architecture

The solution consists of three main components:

- **doc-proc-backend**: FastAPI backend service (port 8090) - Built and deployed via Azure Container Registry tasks
- **doc-proc-worker**: Background worker for async processing
- **doc-proc-frontend**: React frontend application (port 8080)

## 📁 Project Structure

```
doc-proc-solution-accelerator/
├── doc-proc-deploy/           # 👈 All deployment scripts are here
│   ├── build-images.sh        # Build all Docker images
│   ├── build-component.sh     # Build individual component
│   ├── run-containers.sh      # Manage individual containers
│   ├── compose.sh            # Docker Compose management
│   ├── docker-compose.yml    # Docker Compose configuration
│   ├── start-services-local.sh # Start services locally for development
│   ├── deploy-azure-infra.sh  # Deploy Azure infrastructure
│   ├── build-and-push-images.sh # Build and push images to Azure Container Registry
│   ├── deploy-apps.sh         # Deploy applications to Azure
│   ├── infra/
│   │   └── bicep/             # Azure Bicep templates
│   └── README.md             # This file
├── Dockerfile.backend         # Backend service Dockerfile
├── Dockerfile.worker          # Worker service Dockerfile  
├── Dockerfile.frontend        # Frontend service Dockerfile
└── ...
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended for Production)

1. **Build and start all services:**
   ```bash
   ./doc-proc-deploy/compose.sh up
   ```

2. **Access the application:**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8090

3. **Stop services:**
   ```bash
   ./doc-proc-deploy/compose.sh down
   ```

### Option 2: Azure Cloud Deployment

1. **Deploy infrastructure:**
   ```bash
   ./doc-proc-deploy/deploy-azure-infra.sh -r myResourceGroup -l eastus -p myProject
   ```

2. **Build and push images:**
   ```bash
   ./doc-proc-deploy/build-and-push-images.sh -r myResourceGroup -p myProject
   ```

3. **Deploy applications:**
   ```bash
   ./doc-proc-deploy/deploy-apps.sh -r myResourceGroup -p myProject
   ```

### Option 3: Individual Container Management

1. **Build all images:**
   ```bash
   ./doc-proc-deploy/build-images.sh
   ```

2. **Run all containers:**
   ```bash
   ./doc-proc-deploy/run-containers.sh start
   ```

3. **Stop all containers:**
   ```bash
   ./doc-proc-deploy/run-containers.sh stop
   ```

### Option 4: Local Development

For local development without Docker:

1. **Start all services locally:**
   ```bash
   ./doc-proc-deploy/start-services-locally.sh
   ```

2. **Start frontend separately:**
   ```bash
   cd doc-proc-ui/web-app
   npm install
   npm run dev
   ```

3. **Access the application:**
   - Frontend: http://localhost:8080 (Vite dev server)
   - Backend API: http://localhost:8090

## 📋 Available Scripts

### `build-images.sh`
Builds all Docker images for the solution.

```bash
# Build with default 'latest' tag
./build-images.sh

# Build with custom tag
./build-images.sh dev
```

### `build-component.sh`
Builds a specific component image.

```bash
# Build specific component
./build-component.sh backend
./build-component.sh worker dev
```

**Available components:** `backend`, `worker`, `frontend`

### `run-containers.sh`
Manages individual Docker containers.

```bash
# Start all services
./run-containers.sh start

# Stop all services
./run-containers.sh stop

# Restart all services
./run-containers.sh restart

# Check status
./run-containers.sh status

# View logs
./run-containers.sh logs backend
```

### `start-services-local.sh`
Starts all services locally for development (without Docker).

```bash
# Start backend and worker locally
./start-services-local.sh
```

**Features:**
- Creates and manages Python virtual environment
- Installs dependencies automatically  
- Starts backend API on port 8090
- Starts worker in background
- Auto-reload enabled for development

### `compose.sh`
Docker Compose management script.

```bash
# Start all services (build if needed)
./compose.sh up

# Stop and remove all services
./compose.sh down

# Build all images
./compose.sh build

# View logs
./compose.sh logs
./compose.sh logs backend

# Open shell in container
./compose.sh shell worker

# Start specific services
./compose.sh up-backend
./compose.sh up-worker
./compose.sh up-frontend
```

## ☁️ Azure Deployment Scripts

### Prerequisites

Before deploying to Azure, ensure you have:

1. **Azure CLI installed and logged in:**
   ```bash
   az login
   az account set --subscription "your-subscription-id"
   ```

2. **Required Azure providers registered:**
   ```bash
   az provider register --namespace Microsoft.ContainerRegistry
   az provider register --namespace Microsoft.Web
   az provider register --namespace Microsoft.ContainerInstance
   ```

### `deploy-azure-infra.sh`
Deploys the complete Azure infrastructure using Bicep templates.

```bash
# Basic deployment
./deploy-azure-infra.sh -r myResourceGroup -l eastus -p myProject

# With custom app service plan SKU
./deploy-azure-infra.sh -r myResourceGroup -l eastus -p myProject -s B1

# With custom frontend repository (for Static Web App)
./deploy-azure-infra.sh -r myResourceGroup -l eastus -p myProject --frontend-repo "https://github.com/user/repo"
```

**Parameters:**
- `-r, --resource-group`: Resource group name (required)
- `-l, --location`: Azure region (required)
- `-p, --project-name`: Project name prefix (required)
- `-s, --sku`: App Service Plan SKU (default: B1)
- `--frontend-repo`: Frontend repository URL for Static Web App

**Creates:**
- Container Registry
- Container Apps Environment (with Log Analytics)
- Container Apps (Backend API and Worker)
- Static Web App (Frontend)

### `build-and-push-images.sh`
Builds Docker images and pushes them to Azure Container Registry.

```bash
# Build and push all images
./build-and-push-images.sh -r myResourceGroup -p myProject

# Build and push specific component
./build-and-push-images.sh -r myResourceGroup -p myProject -c backend

# With custom tag
./build-and-push-images.sh -r myResourceGroup -p myProject -t v1.0.0
```

**Parameters:**
- `-r, --resource-group`: Resource group name (required)
- `-p, --project-name`: Project name prefix (required)
- `-c, --component`: Specific component (backend, worker, frontend)
- `-t, --tag`: Image tag (default: latest)

### `deploy-apps.sh`
Deploys applications to the Azure infrastructure.

```bash
# Deploy all applications
./deploy-apps.sh -r myResourceGroup -p myProject

# Deploy specific component
./deploy-apps.sh -r myResourceGroup -p myProject -c backend

# With custom image tag
./deploy-apps.sh -r myResourceGroup -p myProject -t v1.0.0
```

**Parameters:**
- `-r, --resource-group`: Resource group name (required)
- `-p, --project-name`: Project name prefix (required)  
- `-c, --component`: Specific component (backend, worker)
- `-t, --tag`: Image tag (default: latest)

**Deploys:**
- Backend API to Container Apps
- Worker to Container Apps
- Frontend gets deployed automatically via Static Web App CI/CD

## 🔧 Configuration

### Environment Variables

You can customize the deployment using environment variables:

```bash
# Custom image tag
export TAG=dev
./compose.sh up
```

### Azure Configuration

For Azure deployments, you can customize:

```bash
# Azure-specific environment variables
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"

# Custom Azure resource configuration  
export AZURE_LOCATION="eastus"
export APP_SERVICE_SKU="B1"
export PROJECT_NAME="myproject"
```

The Azure deployment scripts will automatically:
- Create resource group if it doesn't exist
- Generate unique resource names using project prefix
- Configure appropriate SKUs and settings for each service
- Set up monitoring and logging

## 🏥 Health Checks

All services include health checks:

- **Backend**: `curl -f http://localhost:8090/health`
- **Frontend**: `curl -f http://localhost:8080`
- **Worker**: Python-based health check

Check health status:
```bash
./compose.sh status
```

## 📊 Monitoring & Debugging

### View Logs

```bash
# All services
./compose.sh logs

# Specific service
./compose.sh logs backend
./run-containers.sh logs worker
```

### Access Container Shell

```bash
# Docker Compose
./compose.sh shell backend

# Individual containers
docker exec -it doc-proc-backend /bin/bash
```

### Service Status

```bash
# Docker Compose
./compose.sh status

# Individual containers
./run-containers.sh status
```

## 🔄 Development Workflow

### 1. Build and Test Changes

```bash
# Build specific component after changes
./build-component.sh backend

# Restart specific service
./compose.sh restart backend
```

### 2. Debug Issues

```bash
# View logs
./compose.sh logs backend

# Access container for debugging
./compose.sh shell backend

# Check service health
./compose.sh status
```

### 3. Full Rebuild

```bash
# Stop everything
./compose.sh down

# Build fresh images
./compose.sh build

# Start services
./compose.sh up
```

## 🐳 Docker Image Tags

All images follow the naming convention:
- `doc-proc-backend:TAG`
- `doc-proc-worker:TAG`
- `doc-proc-frontend:TAG`

Default tag is `latest`. Use custom tags for different environments:

```bash
# Development
TAG=dev ./compose.sh build

# Production
TAG=prod ./compose.sh build
```

## 🌐 Network Configuration

All services run on a custom Docker network `doc-proc-network` for:
- Service discovery
- Internal communication
- Isolation from other applications

## 📦 Volumes

- **Redis data**: Persisted in `redis_data` volume
- **Temporary files**: Mounted from `./tmp` directory

## ⚡ Performance Tips

1. **Use Docker Compose** for development (faster startup)
2. **Build in parallel**: `./compose.sh build` uses parallel building
3. **Use specific tags** for different environments
4. **Monitor logs** for performance issues

## 🔒 Security Notes

- Services communicate internally on Docker network
- Only necessary ports are exposed to host
- Environment variables for sensitive configuration
- Regular base image updates recommended

## 🆘 Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports 8080 or 8090 are in use
2. **Build failures**: Ensure Docker has enough memory allocated
3. **Service not starting**: Check logs with `./compose.sh logs <service>`
4. **Network issues**: Restart Docker daemon if network creation fails

### Reset Everything

```bash
# Stop and remove everything
./compose.sh down

# Remove all doc-proc images
docker images | grep doc-proc | awk '{print $3}' | xargs docker rmi -f

# Remove network (if needed)
docker network rm doc-proc-network

# Start fresh
./compose.sh up
```

### Azure Troubleshooting

1. **Authentication issues**: Ensure `az login` was successful
2. **Resource naming conflicts**: Use unique project names
3. **Deployment failures**: Check Azure activity log in portal
4. **Container Registry access**: Verify registry is created and accessible
5. **Static Web App deployment**: Check GitHub integration and build logs

```bash
# Check Azure resources
az resource list --resource-group myResourceGroup --output table

# Check container registry
az acr list --resource-group myResourceGroup --output table

# Check app service logs  
az webapp log tail --name myproject-backend --resource-group myResourceGroup
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Project README](../README.md)