# Document Processing Worker

High-performance, cloud-native document processing worker service engineered for enterprise-scale document processing workloads. The worker implements a distributed, event-driven architecture that seamlessly scales from single-instance development environments to multi-node production clusters handling thousands of concurrent document processing operations.

## Core Worker Concepts

### Distributed Processing Architecture

The doc-proc-worker is built on a **message-driven, horizontally scalable** architecture that separates concerns between task coordination, execution orchestration, and processing logic. This design enables:

- **Fault Isolation**: Failed workers don't impact other processing units
- **Load Distribution**: Work is automatically distributed across available worker instances
- **Resource Optimization**: CPU, memory, and I/O resources are efficiently utilized across processing units

### Event-Driven Processing Model

The worker operates on an **asynchronous, event-driven processing model** where:

1. **Queue-Based Coordination**: Azure Storage Queues provide durable, distributed task coordination
2. **Message-Driven Execution**: Each processing unit is triggered by queue messages containing batch execution requests  
3. **State Management**: Azure Cosmos DB provides consistent, globally distributed state tracking
4. **Pipeline Orchestration**: Document processing flows through configurable, multi-stage pipelines

### Scaling Dimensions

#### Horizontal Scaling (Scale-Out)
- **Instance Scaling**: Deploy multiple worker containers across nodes
- **Queue Partitioning**: Distribute messages across multiple queues for parallel processing
- **Regional Distribution**: Deploy workers in multiple regions for global processing

#### Vertical Scaling (Scale-Up)  
- **Multiprocessing Pools**: Utilize multiple CPU cores within single instances
- **Memory Optimization**: Scale worker memory for large document processing
- **I/O Parallelization**: Concurrent file operations and network requests


## Overview

The doc-proc-worker serves as the **computational engine** of the document processing solution accelerator, designed to process large-scale document workloads with enterprise-grade reliability, performance, and observability. It integrates seamlessly with Azure cloud services to provide a fully managed, serverless-ready processing platform.

### Key Capabilities

- **Asynchronous Queue Processing**: High-throughput polling and processing of Azure Storage Queue messages
- **Pipeline Execution**: Executes configurable document processing pipelines with step-by-step orchestration  
- **Batch Processing**: Handles batch operations with progress tracking, error recovery, and results aggregation
- **Multiprocessing Support**: Scales to multiple concurrent worker processes for CPU-intensive workloads
- **Fault Tolerance**: Comprehensive error handling, retry mechanisms, and graceful degradation
- **Health Monitoring**: Real-time worker health checks with automatic restart capabilities
- **Graceful Shutdown**: Coordinated shutdown handling across all worker processes
- **Cloud-Native**: Built for Azure with native integration to Azure services

### Core Architecture Components

#### 1. Queue Worker (`QueueWorker`)
**Primary Message Processing Engine**

The Queue Worker is the **foundational processing unit** that implements the core message-driven processing loop:

- **Asynchronous Message Polling**: Continuously monitors Azure Storage Queues using efficient long-polling techniques
- **Message Deserialization**: Converts JSON queue messages into strongly-typed Python objects with validation
- **Processing Coordination**: Routes messages to appropriate handlers based on message type and priority
- **Error Recovery**: Implements exponential backoff, retry logic, and dead letter handling
- **Graceful Shutdown**: Supports coordinated shutdown across distributed worker instances

**Key Responsibilities:**
```python
# Message processing lifecycle
async def process_message(message: QueueMessage) -> ProcessingResult:
    1. Validate message format and authentication
    2. Route to appropriate execution handler  
    3. Track processing progress and metrics
    4. Handle errors and implement retry logic
    5. Clean up resources and update message visibility
```

#### 2. Execution Manager (`ExecutionManager`) 
**Batch Processing Orchestrator**

The Execution Manager provides **high-level orchestration** for document processing batches:

- **Batch Lifecycle Management**: Creates, tracks, and finalizes BatchExecution records in Cosmos DB
- **Pipeline Coordination**: Loads pipeline definitions and coordinates multi-step processing workflows
- **Progress Tracking**: Provides real-time progress updates and completion metrics
- **Result Aggregation**: Collects and consolidates results from individual document processing operations

**Processing Flow:**
```python
# Batch execution workflow
async def execute_batch(request: BatchExecutionRequest) -> BatchResult:
    1. Create BatchExecution record with SUBMITTED status
    2. Load and validate pipeline configuration
    3. Initialize pipeline with source documents
    4. Execute pipeline steps with progress tracking
    5. Aggregate results and update final status
    6. Store results and cleanup temporary resources
```

#### 3. Pipeline Manager (`PipelineManager`)
**Dynamic Pipeline Orchestration**

The Pipeline Manager provides **flexible, configurable document processing workflows**:

- **Dynamic Pipeline Loading**: Loads pipeline configurations from Cosmos DB with caching
- **Step Dependency Resolution**: Manages complex dependencies between pipeline steps
- **Step Instance Management**: Creates and configures individual step instances with parameters
- **Data Flow Management**: Handles data passing between pipeline steps with validation


#### 4. Worker Pool Manager (`WorkerPoolManager`)
**Multiprocessing Coordination**

The Worker Pool Manager enables **horizontal scaling within single instances**:

- **Process Pool Management**: Creates, monitors, and manages multiple worker processes
- **Health Monitoring**: Continuously monitors worker process health and performance
- **Automatic Recovery**: Automatically restarts failed worker processes with configurable strategies
- **Load Balancing**: Distributes work across available worker processes efficiently
- **Graceful Shutdown Coordination**: Orchestrates coordinated shutdown across all worker processes
- **Resource Isolation**: Provides process-level isolation for fault tolerance


## Processing Flow

### Message Processing Lifecycle

1. **Queue Polling**: Workers continuously poll Azure Storage Queue for new messages
2. **Message Deserialization**: JSON messages are parsed into typed request objects  
3. **Message Validation**: Request validation and type checking
4. **Batch Execution**:
   - Create BatchExecution record in Cosmos DB
   - Load pipeline configuration and steps
   - Process documents through pipeline stages
   - Track progress and collect results
   - Update batch status and completion metrics
5. **Result Storage**: Store execution results and statistics in Cosmos DB
6. **Queue Cleanup**: Delete successfully processed messages from queue

### Supported Message Types

- **BATCH_EXECUTION_REQUEST**: Primary message type for initiating document processing batches

### Pipeline Execution

The worker integrates with the doc-proc-lib pipeline framework:

- Loads pipeline configurations dynamically  
- Executes step-by-step document processing
- Handles step dependencies and data flow
- Provides error isolation and recovery
- Aggregates step outputs into batch results

## Scaling Architecture & Patterns

### Processing Models & Scaling Strategies

#### Single Worker Mode
**Ideal for: Development, Testing, Low-Volume Processing**

- **Architecture**: Single asyncio event loop with sequential message processing
- **Scaling Characteristics**: 
  - Vertical scaling only (CPU/memory within single process)
  - Predictable resource consumption patterns
  - Linear performance scaling with queue depth
- **Benefits**: 
  - Simplified deployment and debugging
  - Lower memory footprint
  - Deterministic execution order
  - Easier troubleshooting and monitoring
- **Limitations**: 
  - Cannot utilize multi-core processors effectively
  - Single point of failure within instance
  - Limited throughput ceiling
  - CPU-bound operations block other processing

#### Multiprocessing Pool Mode
**Ideal for: Production Workloads, High-Throughput, CPU-Intensive Processing**

- **Architecture**: Multiple independent worker processes with shared coordination
- **Scaling Characteristics**:
  - Horizontal scaling within single VM/container instance  
  - Linear performance scaling with CPU core count
  - Independent failure domains per worker process
  - Concurrent message processing across processes
- **Advanced Features**:
  - **Dynamic Process Management**: Automatic worker process creation/termination
  - **Load Balancing**: Intelligent work distribution across available processes
  - **Health Monitoring**: Per-process health tracking with automatic recovery
  - **Resource Isolation**: Memory and CPU isolation prevents resource contention
  - **Graceful Degradation**: Continues operating with reduced capacity during failures

### Horizontal Scaling Patterns

#### Container-Level Scaling
**Multi-Instance Deployment**

- **Azure Container Apps**: Auto-scale based on queue depth, CPU, memory metrics
- **Kubernetes**: HPA (Horizontal Pod Autoscaler) with custom queue metrics  
- **Benefits**: 
  - Independent failure domains across instances
  - Geographic distribution capabilities
  - Resource isolation at infrastructure level
  - Platform-managed scaling policies

### Vertical Scaling Optimizations

#### CPU Scaling
**Processor Utilization Strategies**

- **CPU-Intensive Workloads**: Scale worker processes to match CPU core count
- **I/O-Intensive Workloads**: Over-subscribe CPUs (2x-4x core count) for better utilization
- **Mixed Workloads**: Dynamic process adjustment based on workload characteristics

#### I/O Scaling
**Network and Storage Optimization**

- **Connection Pooling**: Optimize Azure service connections per worker
- **Batch Operations**: Aggregate multiple operations for improved throughput
- **Async I/O**: Non-blocking I/O operations across all Azure service interactions
- **Caching Strategies**: Multi-level caching for pipeline configurations and metadata


For detailed information about multiprocessing architecture and patterns, see [MULTIPROCESSING.md](MULTIPROCESSING.md).

## Worker Infrastructure Deployment

### Worker-Specific Bicep Template

The doc-proc-worker has its own dedicated Bicep template at `infra/bicep/main.bicep` that focuses exclusively on deploying the worker container application. This template is designed to be lightweight and assumes that the core infrastructure (storage, databases, identity) has already been deployed by the main solution template.

#### Worker Bicep Template Overview

The worker's `main.bicep` template deploys a single, focused component:

**Worker Container Application:**
- **Azure Container App** - Serverless, scalable worker container that processes document batches from storage queues
- **Managed Identity Integration** - Uses existing user-assigned identity for secure access to Azure services
- **Environment Variable Configuration** - Connects to Azure App Configuration for runtime settings
- **Container Registry Integration** - Pulls worker container images from the shared registry

#### Worker Deployment Parameters

The worker template accepts focused parameters for container-specific configuration:

**Basic Configuration:**
```bicep
@description('Name prefix for worker resources')
param namePrefix string = 'docproc'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'
```

**Container Infrastructure References:**
```bicep
@description('Container Apps Environment resource name where the container apps will be deployed')
param containerAppsEnvironment string

@description('Container Registry Server')
param containerRegistryServer string

@description('Container image for the backend app')
param containerImage string
```

**Resource Allocation:**
```bicep
@description('CPU cores for the container')
param cpuCores string = '1.0'

@description('Memory in GB for the container')
param memoryInGB string = '2Gi'
```

**Security and Configuration:**
```bicep
@description('User Assigned Identity Resource Name used as identity for the api app')
param userAssignedIdentityName string

@description('App Configuration Store resource endpoint')
param appConfigStoreEndpoint string

@description('Additional environment variables')
param additionalEnvironmentVariables array = []
```

#### Worker Container Configuration

The template configures the worker container with the following key characteristics:

**Runtime Configuration:**
- **No External Ingress** - Worker operates as a background service without HTTP endpoints
- **Managed Identity Authentication** - Uses user-assigned identity for passwordless Azure service access
- **Environment Variables** - Configures Azure App Configuration connection and client identity

**Container Settings:**
```bicep
containers: [
  {
    name: appName
    image: containerImage
    resources: {
      cpu: cpuCores      // Default: 1.0 cores
      memory: memoryInGB // Default: 2Gi RAM
    }
    env: environmentVariables
  }
]
```

**Security Configuration:**
- **System-Assigned Identity**: Disabled (uses user-assigned identity instead)
- **User-Assigned Identity**: References existing identity from infrastructure deployment
- **Container Registry Access**: Authenticated using managed identity

#### Environment Variables

The template automatically configures essential environment variables:

```bicep
var environmentVariables = [
  {
    name: 'AZURE_APP_CONFIG_CONNECTION_STRING'
    value: ''  // Empty - uses managed identity instead
  }
  {
    name: 'AZURE_APP_CONFIG_ENDPOINT'
    value: appConfigStoreEndpoint
  }
  {
    name: 'AZURE_CLIENT_ID'
    value: userAssignedIdentity.properties.clientId
  }
  // Plus any additionalEnvironmentVariables passed as parameters
]
```

#### Deployment Dependencies

The worker template assumes these resources already exist:
- **Container Apps Environment** - Shared hosting environment for all container apps
- **User Assigned Identity** - Pre-created identity with appropriate Azure service permissions
- **Container Registry** - Repository containing the worker container image
- **App Configuration Store** - Centralized configuration service with worker settings

#### Template Outputs

The worker template provides a single, focused output:

```bicep
output containerAppName string = workerApp.outputs.name
```

This output can be used for:
- Monitoring and logging integrations
- Scaling policy configurations
- Health check implementations
- CI/CD pipeline validations

#### Scaling Considerations

The worker template supports both vertical and horizontal scaling:

**Vertical Scaling:**
- Adjust `cpuCores` parameter (0.25 to 4.0 cores)
- Modify `memoryInGB` parameter (0.5Gi to 8Gi)

**Horizontal Scaling:**
- Container Apps Environment handles automatic scaling
- Multiple worker instances can be deployed across availability zones
- Each worker operates independently with shared queue processing

## References

- [Doc-Proc-Lib Pipeline Framework](../doc-proc-lib/README.md)
- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Azure Cosmos DB Best Practices](https://docs.microsoft.com/en-us/azure/cosmos-db/best-practices)
- [Azure Storage Queue Documentation](https://docs.microsoft.com/en-us/azure/storage/queues/)
- [Python Multiprocessing Guide](https://docs.python.org/3/library/multiprocessing.html)
- [Azure Bicep Documentation](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Infrastructure as Code Best Practices](https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/best-practices)
