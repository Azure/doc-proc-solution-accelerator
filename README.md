<p align="center">
    <picture>
    <img src="logo.svg" alt="doc-proc-solution-accelerator" style="width:600px;height:240px" />
    </picture>
</p>

# Document Processing Solution Accelerator

A comprehensive, enterprise-ready document processing solution built on Azure that enables organizations to rapidly deploy and scale document processing workflows. This accelerator combines the power of Azure AI services, cloud-native architecture, and modern development practices to provide a complete platform for document ingestion, processing, and analysis.

## 🚀 What is this Solution Accelerator?

This solution accelerator provides a production-ready foundation for building document processing applications on Azure. It includes:

- **Modular Processing Pipeline**: A flexible Python library for creating custom document processing workflows
- **Web-based Management UI**: React-based interface for managing pipelines, services, and monitoring executions
- **Scalable Worker Architecture**: Celery-based background processing with Azure Storage Queue integration
- **RESTful API Backend**: FastAPI-based service with Azure Cosmos DB for data persistence
- **Infrastructure as Code**: Bicep templates for automated Azure deployment
- **API Testing Suite**: Bruno collection for comprehensive API testing

## ✨ Key Benefits

- **🏃‍♂️ Rapid Development**: Get started with document processing in minutes, not months
- **🔧 Highly Configurable**: Modular architecture allows customization without core changes
- **☁️ Cloud-Native**: Built specifically for Azure with best practices and security in mind
- **📊 Production-Ready**: Includes monitoring, logging, error handling, and scalability features
- **🔌 Extensible**: Easy to integrate with existing systems and add custom processing steps
- **💰 Cost-Effective**: Optimized resource usage with serverless and managed services

## 🏗️ Architecture Overview

The solution follows a microservices architecture with clear separation of concerns:

```
    TODO: diagram
```

## 📦 Core Components

### 🔧 doc-proc-lib
**The Processing Engine** - A flexible Python library that serves as the heart of the document processing pipeline.

- **Modular Architecture**: Catalog-based configuration for services, steps, and pipelines
- **Azure Integration**: Built-in connectors for Blob Storage, AI Document Intelligence, OpenAI, and more
- **Async Processing**: High-performance asynchronous processing capabilities
- **Custom Components**: Easy framework for building custom processing steps and service integrations
- **Environment Management**: Comprehensive configuration management with environment-specific settings

📖 **[View detailed documentation →](./doc-proc-lib/README.md)**

### 🎨 doc-proc-ui
**The Management Interface** - A modern web application for managing and monitoring document processing workflows.

#### Web Application (`web-app/`)
- **Technology Stack**: React 18 + TypeScript + Vite
- **UI Framework**: Radix UI components with Tailwind CSS styling
- **Features**:
  - Pipeline configuration and management
  - Service and step catalog administration
  - Real-time execution monitoring
  - Interactive workflow designer
  - Responsive design for desktop and mobile

#### Backend API (`backend-app/`)
- **Technology Stack**: FastAPI + Python with Azure Cosmos DB
- **Features**:
  - RESTful API for all CRUD operations
  - Service catalog management
  - Step catalog management  
  - Pipeline configuration and execution
  - Health monitoring and diagnostics
  - CORS-enabled for web client integration

### ⚡ doc-proc-worker
**The Processing Engine** - Scalable background processing service for executing document processing jobs.

- **Technology Stack**: Celery + Redis/Azure Service Bus + Python
- **Features**:
  - Azure Storage Queue integration for job management
  - Distributed task processing with Celery
  - Auto-scaling worker processes
  - Comprehensive logging and error handling
  - Docker containerization for easy deployment
  - Health checks and monitoring endpoints

### 🚀 doc-proc-deploy
**Infrastructure as Code** - Automated deployment templates and scripts for Azure resources.

- **Bicep Templates**: Infrastructure as Code for repeatable deployments
- **Resource Provisioning**: Automated setup of Azure Container Apps, Cosmos DB, Storage Accounts
- **Configuration Management**: Environment-specific configuration templates
- **CI/CD Integration**: Scripts for automated deployment pipelines

### 🧪 Bruno API Collection
**API Testing Suite** - Comprehensive API testing collection for development and QA.

- **Complete Coverage**: Tests for all API endpoints (Services, Steps, Pipelines, Executions)
- **Environment Management**: Separate configurations for development, staging, and production
- **Health Checks**: Monitoring and diagnostic endpoints
- **Integration Testing**: End-to-end workflow validation

## 🚀 Getting Started

### Prerequisites

Before getting started, ensure you have the following:

**Development Environment:**
- Python 3.11+ with pip
- Node.js 18+ with npm
- Docker Desktop (optional, for containerized development)
- Git for version control

**Azure Resources:**
- Azure subscription with appropriate permissions
- Azure Cosmos DB account
- Azure Blob Storage account
- Azure AI Document Intelligence resource (optional)
- Azure OpenAI resource (optional)

### Quick Start Options

Choose the deployment method that best fits your needs:

#### 🔧 **Option 1: Local Development (Fastest)**
Perfect for development and testing:

```bash
# Start all services locally with auto-reload
./doc-proc-deploy/start-services-locally.sh
```

#### 🐳 **Option 2: Docker Compose (Recommended for Production)**  
Consistent environment with all dependencies:

```bash
# Build and start all services
./doc-proc-deploy/compose.sh up
```

#### ☁️ **Option 3: Azure Cloud Deployment**
Production-ready deployment on Azure:

```bash
# Deploy infrastructure
./doc-proc-deploy/deploy-azure-infra.sh -r myResourceGroup -l eastus -p myProject

# Build and push images
./doc-proc-deploy/build-and-push-images.sh -r myResourceGroup -p myProject

# Deploy applications
./doc-proc-deploy/deploy-apps.sh -r myResourceGroup -p myProject
```

💡 **For detailed instructions and additional options, see the [comprehensive deployment guide →](./doc-proc-deploy/README.md)**

### Manual Setup (Advanced Users)

If you prefer manual setup or need to customize the installation:

1. **Clone the repository**
   ```bash
   git clone https://github.com/Azure/doc-proc-solution-accelerator.git
   cd doc-proc-solution-accelerator
   ```

2. **Set up the core library**
   ```bash
   cd doc-proc-lib
   pip install -e .
   ```

3. **Start the backend API**
   ```bash
   cd ../doc-proc-ui/backend-app
   pip install -r requirements.txt
   
   # Configure environment variables
   export COSMOS_ENDPOINT="https://your-cosmos-account.documents.azure.com:443/"
   export COSMOS_KEY="your-cosmos-key"
   export COSMOS_DB_NAME="docproc"
   
   # Start the API server
   python main.py
   ```

4. **Start the web interface**
   ```bash
   cd ../web-app
   npm install
   npm run dev
   ```

5. **Start the worker service** (optional)
   ```bash
   cd ../../doc-proc-worker
   pip install -r requirements.txt
   
   # Configure Azure Storage Queue connection
   export AZURE_STORAGE_CONNECTION_STRING="your-storage-connection-string"
   
   # Start the worker
   python run_queue_worker.py
   ```

## 💡 Usage Examples and Scenarios

### Common Use Cases

#### 1. **Invoice Processing Workflow**
```python
# Example pipeline configuration for invoice processing
pipeline_config = {
    "name": "invoice_processing",
    "steps": [
        {"type": "blob_download", "input_container": "invoices"},
        {"type": "document_intelligence", "model": "prebuilt-invoice"},
        {"type": "data_extraction", "fields": ["vendor", "amount", "date"]},
        {"type": "validation", "rules": ["amount > 0", "date_format"]},
        {"type": "cosmos_store", "container": "processed_invoices"}
    ]
}
```

#### 2. **Document Classification System**
- Automatically classify incoming documents by type
- Route documents to appropriate processing pipelines
- Extract metadata and store in searchable index

#### 3. **Legal Document Analysis**
- Extract key clauses and terms from contracts
- Perform compliance checking against predefined rules
- Generate summaries and risk assessments

#### 4. **Medical Records Processing**
- Extract patient information and medical codes
- Anonymize sensitive data for research purposes
- Structure unstructured clinical notes

### Integration Patterns

#### **API-First Integration**
```javascript
// Integrate with existing systems via REST API
const response = await fetch('/api/pipelines/execute', {
  method: 'POST',
  body: JSON.stringify({
    pipeline_id: 'invoice_processing',
    input_data: { document_url: 'https://...' }
  })
});
```

#### **Event-Driven Processing**
```python
# React to Azure Storage events
@app.route('/webhook/blob-created', methods=['POST'])
def handle_blob_created(event):
    # Trigger document processing pipeline
    pipeline.execute_async(event.data.url)
```

## ⚙️ Deployment and Configuration

The solution provides multiple deployment options to suit different needs:

### 🚀 Automated Deployment Scripts

All deployment scripts are located in the `doc-proc-deploy/` directory:

- **Local Development**: `start-services-locally.sh` - Quick setup for development
- **Docker Compose**: `compose.sh` - Containerized environment  
- **Azure Cloud**: `deploy-azure-infra.sh`, `build-and-push-images.sh`, `deploy-apps.sh` - Complete Azure deployment

📚 **[View comprehensive deployment documentation →](./doc-proc-deploy/README.md)**

### Azure Cloud Deployment

Deploy to Azure using the provided Bicep templates and automation scripts:

```bash
# 1. Deploy Azure infrastructure
./doc-proc-deploy/deploy-azure-infra.sh -r myResourceGroup -l eastus -p myProject

# 2. Build and push container images
./doc-proc-deploy/build-and-push-images.sh -r myResourceGroup -p myProject  

# 3. Deploy applications
./doc-proc-deploy/deploy-apps.sh -r myResourceGroup -p myProject
```

This creates:
- **Container Registry** for storing Docker images
- **Container Apps Environment** for hosting containerized applications
- **Container Apps** (Backend API and Worker services)
- **Static Web App** for the frontend

### Configuration Options

#### Environment Variables

**Backend API:**
- `COSMOS_ENDPOINT` - Azure Cosmos DB endpoint
- `COSMOS_KEY` - Cosmos DB access key
- `COSMOS_DB_NAME` - Database name (default: docproc)
- `ALLOW_ORIGINS` - CORS allowed origins

**Worker Service:**
- `AZURE_STORAGE_CONNECTION_STRING` - Storage queue connection
- `CELERY_BROKER_URL` - Message broker URL
- `CELERY_RESULT_BACKEND` - Result storage backend

**Processing Library:**
- `AZURE_OPENAI_ENDPOINT` - OpenAI service endpoint
- `AZURE_OPENAI_API_KEY` - OpenAI access key
- `DOCUMENT_INTELLIGENCE_ENDPOINT` - AI Document Intelligence endpoint
- `BLOB_STORAGE_CONNECTION_STRING` - Blob storage connection

#### Scaling Configuration

Configure auto-scaling for Container Apps:

```bicep
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  properties: {
    configuration: {
      scaling: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling-rule'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}
```

## 🏷️ Repository Structure

```
doc-proc-solution-accelerator/
├── doc-proc-lib/           # Core processing library
├── doc-proc-ui/           
│   ├── web-app/           # React frontend application
│   └── backend-app/       # FastAPI backend service
├── doc-proc-worker/       # Celery background workers
├── doc-proc-deploy/       # Infrastructure as Code (Bicep)
├── Bruno/                 # API testing collection
└── README.md             # This file
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to:

- Submit bug reports and feature requests
- Set up your development environment
- Submit pull requests
- Follow our coding standards

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Detailed guides in each component's README
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Community discussions and Q&A in GitHub Discussions

## 🔮 Roadmap

- [ ] Enhanced AI model integration (GPT-4, custom models)
- [ ] Real-time processing dashboard
- [ ] Advanced workflow orchestration
- [ ] Enhanced security features
- [ ] Performance monitoring and analytics

---

⚡ **Ready to get started?** Follow the [Quick Start](#getting-started) guide above or dive deep into the [doc-proc-lib documentation](./doc-proc-lib/README.md).
