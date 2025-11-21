<p>
    <picture>
    <img src="../logo.svg" alt="doc-proc-solution-accelerator" style="width:200px;height:80px" />
    </picture>
</p>

# Doc-Proc-Lib: Document Processing Pipeline Library

A flexible, modular document processing pipeline library built with Python that serves as the core processing engine for the Document Processing Solution Accelerator. This library enables the creation of complex document processing workflows through configurable pipelines, steps, and services, and integrates seamlessly with the complete solution ecosystem including web UI, REST API, background workers, and distributed crawlers.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
  - [Service Catalog](#service-catalog)
  - [Step Catalog](#step-catalog)
  - [Source Catalog](#source-catalog)
  - [Pipeline Configuration](#pipeline-configuration)
- [Core Components](#core-components)
- [Creating Custom Components](#creating-custom-components)
  - [Custom Service](#custom-service)
  - [Custom Step](#custom-step)
  - [Custom Source](#custom-source)
- [Troubleshooting](#troubleshooting)

## Overview

Doc-Proc-Lib is the foundational processing engine that powers the entire Document Processing Solution Accelerator. It's designed to handle complex document processing workflows by breaking them down into modular, reusable components that can be orchestrated through a comprehensive ecosystem:

### Components
- **Services**: External integrations (Azure Blob Storage, AI Inference, Document Intelligence, AI Search, Cosmos DB)
- **Steps**: Processing units that transform data (PDF extraction, content retrieval, entity extraction, index writing)
- **Sources**: Data source connectors for distributed crawling and content ingestion (Azure Blob Storage, SharePoint Online, File Systems)
- **Pipelines**: Orchestrated sequences of steps with dependency management

The library supports:
- ✅ Asynchronous processing with high-performance execution
- ✅ Modular architecture with catalog-based configuration
- ✅ Complete Azure ecosystem integration
- ✅ AI-powered document processing (GPT-4, Document Intelligence, Computer Vision)
- ✅ Flexible pipeline orchestration with conditional execution
- ✅ Environment-based configuration with Azure Key Vault integration
- ✅ Comprehensive logging, monitoring, and error handling
- ✅ Distributed processing with lease-based coordination
- ✅ RESTful API exposure for web and mobile applications
- ✅ Real-time queue processing for scalable document ingestion

## Architecture

The Document Processing Solution follows a comprehensive microservices architecture with the `doc-proc-lib` serving as the core processing engine:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        Complete Document Processing Solution Architecture           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                  │
│  │  doc-proc-web   │    │  doc-proc-api   │    │ doc-proc-crawler│                  │
│  │  Management UI  │◄──►│  REST API       │◄──►│ Distributed     │                  │
│  │  (React/TS)     │    │  (FastAPI)      │    │ Source Crawler  │                  │
│  │  Port: 8080     │    │  Port: 8090     │    │ (Multi-node)    │                  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                  │
│           │                       │                       │                         │
│           │                       ▼                       ▼                         │
│           │              ┌─────────────────┐    ┌─────────────────┐                 │
│           │              │ Azure Cosmos DB │    │ Azure Storage   │                 │
│           │              │ Metadata Store  │    │ Queues & Blobs  │                 │
│           │              │ • Pipelines     │    │ • Processing    │                 │
│           │              │ • Executions    │    │ • File Storage  │                 │
│           │              │ • Configurations│    │ • Source Data   │                 │
│           │              └─────────────────┘    └─────────────────┘                 │
│           │                       │                       │                         │
│           │                       ▼                       ▼                         │
│           │              ┌─────────────────┐    ┌─────────────────┐                 │
│           └─────────────►│ doc-proc-worker │◄───│  doc-proc-lib   │                 │
│                          │ Queue Processor │    │ Pipeline Engine │                 │
│                          │ (Scalable)      │    │ Processing Core │                 │
│                          │ Background Jobs │    │                 │                 │
│                          └─────────────────┘    └─────────────────┘                 │
│                                   │                       │                         │
│                                   ▼                       ▼                         │
│                          ┌─────────────────────────────────────────┐                │
│                          │              Azure AI Services          │                │
│                          │  • Document Intelligence                │                │
│                          │  • OpenAI GPT-4 Inference               │                │
│                          │  • Computer Vision                      │                │
│                          │  • AI Search (Vector + Semantic)        │                │
│                          └─────────────────────────────────────────┘                │
│                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                              doc-proc-lib Core Architecture                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌────────────────────────┐           │
│  │ Service Catalog │    │  Step Catalog   │    │   Pipeline Config      │           │
│  │                 │    │                 │    │                        │           │
│  │ • Azure Blob    │    │ • PDF Extract   │    │ • Service Instances    │           │
│  │ • AI Inference  │    │ • Content Get   │    │ • Step Instances       │           │
│  │ • Doc Intel     │    │ • Entity Extract│    │ • Pipeline Definitions │           │
│  │ • AI Search     │    │ • Index Writer  │    │ • Source Configs       │           │
│  │ • Cosmos DB     │    │ • Custom Steps  │    │                        │           │
│  └─────────────────┘    └─────────────────┘    └────────────────────────┘           │
│           │                       │                       │                         │
│           └───────────────────────┼───────────────────────┘                         │
│                                   │                                                 │
│                          ┌─────────────────┐                                        │
│                          │    Pipeline     │                                        │
│                          │   Orchestrator  │                                        │
│                          │                 │                                        │
│                          │ ┌─────────────┐ │                                        │
│                          │ │Content Get  │ │                                        │
│                          │ └─────────────┘ │                                        │
│                          │        │        │                                        │
│                          │ ┌─────────────┐ │                                        │
│                          │ │Doc Type ID  │ │                                        │
│                          │ └─────────────┘ │                                        │
│                          │        │        │                                        │
│                          │ ┌─────────────┐ │                                        │
│                          │ │ AI Extract  │ │                                        │
│                          │ └─────────────┘ │                                        │
│                          │        │        │                                        │
│                          │ ┌─────────────┐ │                                        │
│                          │ │Index Writer │ │                                        │
│                          │ └─────────────┘ │                                        │
│                          └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────────────┘
```


## Getting Started

Getting started with Doc-Proc-Lib involves three main steps:

1. **Configure Services**: Define your external service connections (storage, AI services, databases) in `service_catalog.yaml`
2. **Configure Steps**: Define your processing steps (extractors, transformers, writers) in `step_catalog.yaml` 
3. **Configure Sources**: Define your data sources for crawling in `source_catalog.yaml`
4. **Create Pipeline**: Orchestrate services, sources and steps into a processing workflow in `pipeline_config.yaml`

The library loads these configurations at runtime and creates executable pipeline instances. Each pipeline can process documents through a sequence of configurable steps, with automatic error handling, retries, and monitoring.

## Configuration

The library uses four main configuration files that work together to define processing workflows:

### Service Catalog

The `service_catalog.yaml` defines reusable service templates that can be instantiated with different configurations. Services represent external integrations like cloud storage, AI services, or databases.

Each service definition includes:
- **Identification**: Unique ID, name, and description
- **Implementation**: Module path, class name, and version information  
- **Configuration Schema**: Required and optional settings with validation rules
- **UI Metadata**: Display information for dynamic form generation
- **Environment Integration**: Automatic environment variable substitution
- **Security Features**: Sensitive data marking and credential management

Services are organized by categories (Storage, AI Services, Search, Database) and support multiple authentication methods including Azure Default Credential and API key-based authentication.

**Key Features:**
- **Reusability**: Define once, use in multiple pipelines
- **Validation**: Schema-based configuration validation
- **Environment Integration**: Automatic environment variable substitution
- **Security**: Sensitive data marking and handling
- **UI Generation**: Metadata for dynamic form generation

### Step Catalog

The `step_catalog.yaml` defines reusable processing step templates. Steps are the building blocks that perform actual data processing tasks.

Each step definition includes:
- **Identification**: Unique ID, name, description, and categorization
- **Implementation**: Module path, class name, and version information
- **Configuration Schema**: Settings with validation rules, data types, and constraints
- **UI Metadata**: Icons, colors, and descriptions for dynamic UI generation
- **Categorization**: Organized by function (Input, Extractor, Processor, AI, Output)

Built-in step categories include:
- **Input Steps**: Content retrieval, file downloading, source ingestion
- **Extractor Steps**: Text extraction from PDFs, Word docs, PowerPoint, Excel
- **Processor Steps**: Document type identification, content transformation
- **AI Steps**: Custom prompts, entity extraction, content analysis
- **Output Steps**: Search index writing, blob storage output, data export

Each step supports conditional execution, error handling, retry logic, and timeout configuration.

**Key Features:**
- **Modularity**: Reusable processing units
- **Validation**: Input/output schema validation
- **UI Metadata**: For dynamic UI generation of step configuration

### Source Catalog

The `source_catalog.yaml` defines reusable data source connectors for distributed crawling and content ingestion. Sources represent various data repositories that can be crawled to discover and retrieve documents for processing.

Each source definition includes:
- **Identification**: Unique ID, name, description, and source type
- **Implementation**: Module path, class name, and version information
- **Configuration Schema**: Connection settings, authentication, and crawling parameters
- **UI Metadata**: Display information for source configuration interfaces
- **Authentication Support**: Multiple credential types and security configurations

Built-in source types include:
- **Azure Blob Storage**: Crawl documents from Azure Storage containers with support for various authentication methods
- **Azure Files**: Access documents from Azure File Shares with hierarchical directory support  
- **SharePoint Online**: Connect to SharePoint document libraries using Microsoft Graph API
- **File System Sources**: Local and network file system crawling capabilities

Sources support:
- **Flexible Authentication**: Azure Default Credential, API keys, and service principal authentication
- **Content Filtering**: File type filtering, path-based inclusion/exclusion rules
- **Metadata Extraction**: Automatic extraction of file properties, timestamps, and source information
- **Incremental Crawling**: Support for change detection and incremental updates
- **Error Handling**: Robust error handling with retry logic and connection testing

**Key Features:**
- **Extensibility**: Easy addition of new source types through modular architecture
- **Configuration Validation**: Schema-based validation of source settings
- **Environment Integration**: Support for environment variable substitution
- **UI Generation**: Metadata for dynamic source configuration forms

### Pipeline Configuration

The `pipeline_config.yaml` brings together services, sources, and steps to create executable workflows. It defines service instances, source instances, and pipeline execution sequences.

The configuration consists of three main sections:

**Service Instances**: References to service catalog entries with instance-specific configurations including connection strings, API keys, and custom settings. Each service instance provides a named service that can be referenced by pipeline steps.

**Source Instances**: References to source catalog entries with specific connection and crawling configurations. Source instances define where documents will be discovered and retrieved from during pipeline execution.

**Pipeline Definitions**: Complete workflow specifications that include:
- **Step Instances**: References to step catalog entries with custom settings and service dependencies
- **Execution Sequence**: Ordered list of steps to execute in the pipeline
- **Conditional Logic**: Step-level conditions that control when steps should run
- **Error Handling**: Configuration for retries, timeouts, and failure behavior
- **Service Bindings**: Assignment of service instances to specific steps
- **Global Settings**: Pipeline-level configuration for timeouts, concurrency, and execution control

Each step instance can be configured with:
- **Execution Control**: Enable/disable flags, timeout settings, retry configuration
- **Service Dependencies**: List of required service instances
- **Conditional Execution**: Expressions that determine when the step should run
- **Custom Settings**: Step-specific configuration parameters
- **Debug Mode**: Enhanced logging and debugging capabilities

**Key Features:**
- **Service Orchestration**: Manage multiple service instances
- **Step Sequencing**: Define execution order and dependencies
- **Configuration Override**: Instance-specific setting customization
- **Execution Control**: Pipeline-level execution settings

### How They Work Together

1. **Service Catalog** → **Service Instances**: Service templates are instantiated with specific configurations
2. **Step Catalog** → **Pipeline Steps**: Step templates are configured for specific use cases
3. **Source Catalog** → **Source Instances**: Source templates are configured for specific data repositories
4. **Pipeline Configuration**: Orchestrates all instances into executable workflows

The configuration flow follows this pattern:

**Service Catalog Templates** → **Configured Service Instances** → **Available to Pipeline Steps**

**Step Catalog Templates** → **Configured Step Instances** → **Executed in Pipeline Sequence**  

**Source Catalog Templates** → **Configured Source Instances** → **Used by Crawler and Content Retrieval**

**Pipeline Configuration** → **Complete Workflow** → **Executable Pipeline with Dependencies**

## Core Components

### StepBase

All processing steps inherit from the `StepBase` abstract class, which provides the foundation for implementing custom document processing logic. Steps receive input data, have access to configured services through the pipeline execution context, and return transformed output data. The base class handles error management, logging, timeout enforcement, and retry logic automatically.

View the [Step documentation](./doc/proc/step/README.md) for available steps and detailed implementation guidance.

### ServiceBase  

All external service integrations inherit from the `ServiceBase` abstract class, which standardizes service connectivity, credential management, and connection testing. Services provide reusable functionality that can be shared across multiple pipeline steps, such as cloud storage access, AI model inference, database operations, and search indexing.

View the [Service documentation](./doc/proc/service/README.md) for available services and detailed implementation guidance.

### SourceBase

All data source connectors inherit from the `SourceBase` abstract class, which provides the framework for crawling and retrieving documents from various repositories. Sources handle authentication, content discovery, metadata extraction, and incremental crawling capabilities with built-in error handling and retry logic.

View the [Source documentation](./doc/proc/source/README.md) for available sources and detailed implementation guidance.

### Pipeline Execution Context

The Pipeline Execution Context provides steps with access to configured services, execution state, logging infrastructure, and pipeline metadata. It serves as the communication bridge between pipeline orchestration and individual step implementations, ensuring proper resource management and execution coordination.



## Creating Custom Components

### Custom Service

Creating custom services involves implementing the `ServiceBase` abstract class and adding the service definition to the service catalog:

**Implementation Steps:**
1. **Create Service Class**: Inherit from `ServiceBase` and implement required methods including connection testing and service-specific functionality
2. **Configuration Schema**: Define settings schema with validation rules, data types, and UI metadata
3. **Catalog Registration**: Add the service definition to `service_catalog.yaml` with module path and configuration details
4. **Instance Creation**: Configure service instances in `pipeline_config.yaml` with specific settings

Custom services can integrate with any external API, database, or cloud service while maintaining consistent authentication, configuration, and error handling patterns.

View the [Service documentation](./doc/proc/service/README.md) for detailed implementation guidance.

### Custom Step

Creating custom processing steps involves implementing the `StepBase` abstract class and registering in the step catalog:

**Implementation Steps:**
1. **Create Step Class**: Inherit from `StepBase` and implement the `run` method with custom processing logic
2. **Service Integration**: Access configured services through the pipeline execution context
3. **Data Processing**: Transform input data and return structured output with summary metadata  
4. **Error Handling**: Implement proper exception handling and logging within the step
5. **Catalog Registration**: Add step definition to `step_catalog.yaml` with settings schema and UI metadata
6. **Pipeline Integration**: Configure step instances in pipelines with service dependencies and custom settings

Custom steps can implement any processing logic including external API calls, complex data transformations, machine learning inference, or custom business rules.

View the [Step documentation](./doc/proc/step/README.md) for comprehensive development guidance.

### Custom Source

Creating custom data source connectors involves implementing the `SourceBase` abstract class and registering in the source catalog:

**Implementation Steps:**
1. **Create Source Class**: Inherit from `SourceBase` and implement required methods including `test_connection`, `crawl`, and authentication handling
2. **Authentication Setup**: Implement proper credential handling for your data source including API keys, OAuth tokens, or connection strings
3. **Crawling Logic**: Develop efficient crawling algorithms with support for incremental updates, content filtering, and metadata extraction
4. **Error Handling**: Implement robust error handling for network issues, authentication failures, and data access problems
5. **Catalog Registration**: Add source definition to `source_catalog.yaml` with configuration schema and connection parameters
6. **Instance Configuration**: Configure source instances in `pipeline_config.yaml` with specific connection details and crawling settings

Custom sources can connect to any data repository including cloud storage, file systems, databases, web APIs, document management systems, or proprietary data sources while maintaining consistent authentication, configuration, and crawling patterns.

View the [Source documentation](./doc/proc/source/README.md) for detailed implementation guidance and examples.



## Troubleshooting

### Common Issues & Solutions

#### Configuration Loading Errors
**Issues**: Service configuration validation failures, YAML parsing errors, environment variable resolution problems.

**Solutions**: Check YAML syntax and indentation consistency, verify all required fields are present, ensure environment variables are accessible, validate schema compliance, and check for circular dependencies in service references.

#### Azure Service Connection Failures  
**Issues**: Authentication failures, service endpoint connectivity problems, credential validation errors.

**Solutions**: Verify Azure service credentials and endpoints in environment variables, check network connectivity and firewall settings, validate Azure service permissions and RBAC assignments, ensure Azure services are operational, test credentials using Azure CLI, and verify managed identity role assignments.

#### Pipeline Execution Errors
**Issues**: Step timeouts, pipeline execution failures, memory limit exceeded errors, dependency resolution problems.

**Solutions**: Increase timeout values in configurations, check input data format and document availability, review memory usage patterns, monitor Azure resource quotas, validate step dependencies, and enable debug logging for detailed error tracking.



### Debugging Techniques

#### Comprehensive Logging Setup
Configure detailed logging with appropriate levels, structured formats, and multiple output destinations. Enable specific logger debugging for doc-proc components while reducing noise from Azure SDK and HTTP libraries.

#### Service Connection Testing
Implement systematic testing of individual service connections using the service catalog configuration. Load service instances with default settings and validate connectivity before pipeline execution.

#### Pipeline Validation & Testing
Validate pipeline configurations before execution by loading and checking all references. Verify step catalog references, service dependencies, and configuration completeness to identify issues early.

#### Real-time Monitoring & Alerts
Monitor pipeline executions for health issues including failure rates, long-running executions, and system health status. Implement automated alerting for anomalous patterns and resource exhaustion.

### Performance Optimization

#### Pipeline Optimization
Configure optimal settings for step execution, appropriate timeouts, memory limits, temporary file cleanup, connection pooling, and batch processing to maximize throughput while maintaining resource efficiency.

#### Resource Monitoring
Monitor system resources during processing including CPU and memory usage, Azure resource consumption, and queue depth metrics to identify performance bottlenecks and capacity planning needs.

### Getting Help

**Diagnostic Steps**: Enable comprehensive logging, check service health endpoints, review Azure service quotas, test components in isolation, monitor resource usage, and check Azure service status pages.

**Support Resources**: Azure Support Documentation, GitHub Issues, Azure AI Services Troubleshooting guides, FastAPI Documentation, and React Troubleshooting guides provide additional assistance for complex issues.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request

