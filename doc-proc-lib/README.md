<p>
    <picture>
    <img src="../logo.svg" alt="doc-proc-solution-accelerator" style="width:200px;height:80px" />
    </picture>
</p>

# Doc-Proc-Lib: Document Processing Pipeline Library

A flexible, modular document processing pipeline library built with Python that enables the creation of complex document processing workflows through configurable pipelines, steps, and services.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [Service Catalog](#service-catalog)
  - [Step Catalog](#step-catalog)
  - [Pipeline Configuration](#pipeline-configuration)
- [Core Components](#core-components)
- [Usage Examples](#usage-examples)
- [Built-in Services](#built-in-services)
- [Built-in Steps](#built-in-steps)
- [Creating Custom Components](#creating-custom-components)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

## Overview

Doc-Proc-Lib is designed to handle complex document processing workflows by breaking them down into modular, reusable components:

- **Services**: External integrations (Azure Blob Storage, AI services, databases)
- **Steps**: Processing units that transform data
- **Pipelines**: Orchestrated sequences of steps

The library supports:
- ✅ Asynchronous processing
- ✅ Modular architecture with catalog-based configuration
- ✅ Azure cloud services integration
- ✅ AI-powered document processing
- ✅ Flexible pipeline orchestration
- ✅ Environment-based configuration
- ✅ Comprehensive logging and error handling

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Service Catalog │    │  Step Catalog   │    │Pipeline Config  │
│                 │    │                 │    │                 │
│ - Azure Blob    │    │ - DOC to MD     │    │ - Service       │
│ - Azure AI      │    │ - MD to Index   │    │   Instances     │
│ - AI SEARCH     │    │ - Custom Steps  │    │ - Pipeline      │
│ - COSMOS        │    │                 │    │   Definition    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │    Pipeline     │
                    │   Orchestrator  │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │   Step 1    │ │
                    │ └─────────────┘ │
                    │        │        │
                    │ ┌─────────────┐ │
                    │ │   Step 2    │ │
                    │ └─────────────┘ │
                    │        │        │
                    │ ┌─────────────┐ │
                    │ │   Step N    │ │
                    │ └─────────────┘ │
                    └─────────────────┘
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd doc-proc-solution-accelerator/doc-proc-lib
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Quick Start

Here's a simple example to get you started:

```python
import asyncio
from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.pipeline.pipeline_config import PipelineConfig
from doc.proc.step.step_base import StepInputOutput
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_config import ServiceConfig

async def main():
    # Load configurations
    service_catalog = ServiceConfig.from_file('service_catalog.yaml')
    step_catalog = StepConfig.from_file('step_catalog.yaml')
    pipeline_config = PipelineConfig.from_file('pipeline_config.yaml')
    
    # Create pipeline from the first pipeline defined in the config
    pipeline = await Pipeline.create(
        pipeline_config=pipeline_config[0],
        step_catalog_config=step_catalog,
        service_catalog_config=service_catalog
    )
    
    # Run pipeline
    input_data = StepInputOutput(
        summary_data={},
        data={"input_pdf_file": "/path/to/document.pdf"}
    )
    
    result = await pipeline.run(input_data=input_data)
    print(f"Pipeline completed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The library uses three main configuration files that work together to define processing workflows:

### Service Catalog

The `service_catalog.yaml` defines reusable service templates that can be instantiated with different configurations. Services represent external integrations like cloud storage, AI services, or databases.

**Structure:**
```yaml
# Sample service configuration
## 
services_catalog:
  - id: azure_storage_01                             # Unique service identifier
    name: "Azure Blob Storage - Primary"             # Human-readable name
    description: "Primary storage account"           # Service description
    type: azure_blob                                 # Service type
    module_name: blob_service                        # Python module name
    module_path: ./doc/proc/service/blob_service.py  # Module file path
    class_name: BlobService                          # Service class name
    test_connection: true                            # Test connection on startup
    category: "Storage"                              # Logical grouping
    version: "1.0"                                   # Service version
    tags: [azure, storage, blob]                     # Search/filter tags
    
    # Configuration schema for validation and UI generation
    settings_schema:  
      account_name:
        type: string
        title: "Storage Account Name"
        description: "Name of the Azure Blob Storage account"
        required: true
        env_var: "AZURE_STORAGE_SERVICE_ACCOUNT_NAME"
        default: ${AZURE_STORAGE_SERVICE_ACCOUNT_NAME}
      credential_type:
        type: string
        title: "Credential Type"
        description: "Type of credential used for authentication"
        default: "azure_key_credential"
        enum: ["azure_key_credential", "default_azure_credential"]
        env_var: "AZURE_STORAGE_SERVICE_CREDENTIAL_TYPE"
        default: ${AZURE_STORAGE_SERVICE_CREDENTIAL_TYPE}
      credential_key:
        type: string
        title: "Account Key"
        description: "Account key for Azure Blob Storage authentication"
        required: false
        sensitive: true
        env_var: "AZURE_STORAGE_SERVICE_ACCOUNT_KEY"
        default: ${AZURE_STORAGE_SERVICE_ACCOUNT_KEY}
    
    # UI metadata for frontend display
    ui_metadata:
      icon: "database"
      color: "#0078D4"
      description_short: "Azure Blob Storage for documents"
      description_long: "Azure Blob Storage service for storing and retrieving documents, images, and other unstructured data."
```

**Key Features:**
- **Reusability**: Define once, use in multiple pipelines
- **Validation**: Schema-based configuration validation
- **Environment Integration**: Automatic environment variable substitution
- **Security**: Sensitive data marking and handling
- **UI Generation**: Metadata for dynamic form generation

### Step Catalog

The `step_catalog.yaml` defines reusable processing step templates. Steps are the building blocks that perform actual data processing tasks.

**Structure:**
```yaml
step_catalog:
  - id: sample_01                                    # Unique step identifier
    name: "Sample Step"                              # Human-readable name
    description: "Sample Step Configuration"
    type: script                                     # Step type
    module_name: sample                              # Python module name
    module_path: ./doc/proc/step/sample.py
    class_name: SampleStep                           # Step class name
    tags: [sample]                                   # Search/filter tags
    category: "Sample".                              # Logical grouping
    version: "1.0"                                   # Version
    
    # Error handling configuration
    fail_pipeline_on_error: false                    # Stop pipeline on error
    retry_on_failure: false                          # Retry failed steps
    retries: 0                                       # Number of retries
    timeout: 600                                     # Timeout in seconds
    
    # Configuration schema
    settings_schema:
      setting_1:
        type: string
        title: "Sample setting 01"
        description: "Sample setting 01"
        default: "sample value"
        required: true
        pattern: "^\\.\\/.*"               
      
      setting_2:
        type: integer
        title: "Sample integer setting"
        description: "Sample integer setting"
        default: 10
        min: 0
        max: 1000
    
    # UI metadata
    ui_metadata:
      icon: "image"
      color: "#10B981"
      description_short: "Sample Step"
      description_long: "Sample Step"
```

**Key Features:**
- **Modularity**: Reusable processing units
- **Error Handling**: Configurable retry and failure policies
- **Validation**: Input/output schema validation
- **Timeouts**: Step-level timeout configuration
- **Dependencies**: Service dependency specification

### Pipeline Configuration

The `pipeline_config.yaml` brings together services and steps to create executable workflows. It defines service instances and pipeline execution sequences.

**Structure:**
```yaml
# Service instances - configured services for this pipeline
service_instances:
  - name: primary_blob_storage              # Instance name
    service_catalog_id: azure_storage_01    # Reference to catalog
    settings:                              # Instance-specific settings
      account_name: ${AZURE_STORAGE_ACCOUNT_NAME}
      credential_key: ${AZURE_STORAGE_ACCOUNT_KEY}
  
  - name: ai_inference_service
    service_catalog_id: azure_ai_inference_service_01
    settings:
      endpoint: ${AZURE_AI_ENDPOINT}
      api_key: ${AZURE_AI_API_KEY}
      model_name: "gpt-4o"
      max_tokens: 4000
  
  - name: ai_search_service
    service_catalog_id: azure_ai_search_service_01
    settings:
      account_name: ${AZURE_AI_SEARCH_SERVICE_ACCOUNT_NAME}
      credential_type: ${AZURE_AI_SEARCH_SERVICE_CREDENTIAL_TYPE}
      api_key: ${AZURE_AI_SEARCH_SERVICE_API_KEY}
      api_version: "2024-07-01"
      index_name: "documents_index"

# Pipeline definitions
pipelines:
  - name: document_processing_pipeline
    description: "Extract and process PDF documents"
    version: "1.0"
    
    # Pipeline steps
    steps:
      - name: extract_and_process_pdf        # Step instance name
        step_catalog_id: pdf_text_extractor  # Reference to catalog
        enabled: true                        # Enable/disable step
        services: [primary_blob_storage, ai_inference_service]  # Required services
        settings:                           # Step-specific settings
          png_output_folder: "./output/png"
          num_pages: 10
          dpi: 300
          prompts:
            system: "You are an AI assistant that helps convert images of pages of a pdf document to markdown text. Only output valid markdown."
            user: "Extract the text from the following image into markdown and provide descriptions of images..."
          max_completion_tokens: 4000
          temperature: 1.0
      
      - name: write_to_search_index
        step_catalog_id: ai_search_index_writer
        enabled: true
        services: [ai_search_service]
        settings:
          index_name: "documents_index"
          chunks_iterator_field: "data.chunks_data"
          index_field_mappings: |
            {
              "page_id": "id",
              "input_file_path": "file_name",
              "page_num": "page_num",
              "markdown": "markdown",
              "summary": "summary",
              "page_image_base64": "page_image"
            }
    
    # Execution order
    execution_sequence: [extract_and_process_pdf, write_to_search_index]
    
    # Pipeline settings
    settings:
      enabled: true
      retry_delay: 5
      timeout: 300
      max_concurrent_runs: 5
```

**Key Features:**
- **Service Orchestration**: Manage multiple service instances
- **Step Sequencing**: Define execution order and dependencies
- **Configuration Override**: Instance-specific setting customization
- **Execution Control**: Pipeline-level execution settings

### How They Work Together

1. **Service Catalog** → **Service Instances**: Templates are instantiated with specific configurations
2. **Step Catalog** → **Pipeline Steps**: Step templates are configured for specific use cases
3. **Pipeline Configuration**: Orchestrates service instances and steps into executable workflows

```
Service Catalog (Template)     →     Service Instance (Configured)
     ↓                                        ↓
"azure_storage_01"             →     "primary_blob_storage"
                                              ↓
Step Catalog (Template)        →     Pipeline Step (Configured)
     ↓                                        ↓
"pdf_to_png"                   →     "extract_pdf_pages"
                                              ↓
                                      Pipeline Execution
```

## Core Components

### StepBase

All processing steps inherit from `StepBase`:

```python
from doc.proc.step.step_base import StepBase, StepInputOutput
from doc.proc.pipeline.pipeline_base import PipelineExecutionContext

class CustomStep(StepBase):
    async def run(self, input_data: StepInputOutput, 
                  context: PipelineExecutionContext, 
                  **kwargs) -> StepInputOutput:
        # Process data
        processed_data = self.process(input_data.data)
        
        # Return results
        return StepInputOutput(
            summary_data={**input_data.summary_data, "step_completed": True},
            data={**input_data.data, **processed_data}
        )
```

### ServiceBase

All services inherit from `ServiceBase`:

```python
from doc.proc.service.service_base import ServiceBase

class CustomService(ServiceBase):
    async def test_connection(self) -> bool:
        # Test service connectivity
        return True
    
    async def process_document(self, document_data):
        # Service-specific processing
        pass
```

### Pipeline Execution Context

Provides access to services and execution state:

```python
# In a step's run method
async def run(self, input_data: StepInputOutput, 
              context: PipelineExecutionContext, **kwargs):
    # Access services
    storage_service = context.get_service("primary_blob_storage")
    ai_service = context.get_service("ai_inference_service")
    
    # Use services
    document = await storage_service.download_file("document.pdf")
    result = await ai_service.process(document)
    
    return StepInputOutput(data={"result": result})
```

## Usage Examples

### Example 1: Basic Document Processing

```python
# main.py
import asyncio
from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.step.step_base import StepInputOutput

async def process_document():
    # Load configurations (as shown in quick start)
    pipeline = await create_pipeline()
    
    # Process a single document
    input_data = StepInputOutput(
        summary_data={},
        data={
            "input_pdf_file": "/path/to/document.pdf",
            "output_format": "markdown"
        }
    )
    
    result = await pipeline.run(input_data=input_data)
    
    # Access results
    markdown_content = result.data.get("markdown_content")
    summary = result.summary_data
    
    print(f"Processing complete. Summary: {summary}")
    return markdown_content

asyncio.run(process_document())
```

### Example 2: Batch Processing

```python
async def batch_process_documents(file_list):
    pipeline = await create_pipeline()
    results = []
    
    for pdf_file in file_list:
        input_data = StepInputOutput(
            summary_data={"batch_id": "batch_001"},
            data={"input_pdf_file": pdf_file}
        )
        
        try:
            result = await pipeline.run(input_data=input_data)
            results.append({
                "file": pdf_file,
                "status": "success",
                "data": result.data
            })
        except Exception as e:
            results.append({
                "file": pdf_file,
                "status": "error",
                "error": str(e)
            })
    
    return results
```

### Example 3: Custom Step with Service Integration

```python
from doc.proc.step.step_base import StepBase, StepInputOutput

class CustomAnalysisStep(StepBase):
    async def run(self, input_data: StepInputOutput, 
                  context, **kwargs) -> StepInputOutput:
        
        # Get required services
        storage = context.get_service("primary_blob_storage")
        ai_service = context.get_service("ai_inference_service")
        
        # Process input
        document_path = input_data.data.get("document_path")
        
        # Download document from storage
        document_content = await storage.download_file(document_path)
        
        # Analyze with AI service
        analysis_prompt = "Analyze this document for key insights..."
        analysis_result = await ai_service.complete(
            messages=[
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": document_content}
            ]
        )
        
        # Update summary and data
        updated_summary = {
            **input_data.summary_data,
            "analysis_completed": True,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        updated_data = {
            **input_data.data,
            "analysis_result": analysis_result,
            "key_insights": self.extract_insights(analysis_result)
        }
        
        return StepInputOutput(
            summary_data=updated_summary,
            data=updated_data
        )
    
    def extract_insights(self, analysis_text):
        # Custom insight extraction logic
        return ["insight1", "insight2", "insight3"]
```

## Built-in Services

### Azure Blob Storage Service
- **Purpose**: Document storage and retrieval
- **Configuration**: Account name, access key, containers
- **Usage**: Upload, download, list files

### Azure AI Inference Service  
- **Purpose**: AI-powered document processing
- **Models**: GPT-4, GPT-3.5, custom models
- **Usage**: Text extraction, analysis, summarization

### Azure Cosmos DB Service
- **Purpose**: Metadata and results storage
- **Configuration**: Endpoint, key, database/container
- **Usage**: Store processing results, metadata

### Azure AI Search Service
- **Purpose**: Document indexing and search
- **Configuration**: Service name, API key, index name, API version
- **Usage**: Full-text search, semantic search, vector search, document indexing

## Built-in Steps

| Step Name                  | Description                        | Documentation Link                                                        |
|----------------------------|------------------------------------|---------------------------------------------------------------------------|
| PDF Text Extractor Step    | Extracts text from PDF documents   | [PDF Text Extractor Step Documentation](./doc/proc/step/pdf_text_extractor.md) |
| Custom AI Prompt Step      | Runs custom AI prompt processing   | [Custom AI Prompt Step Documentation](./doc/proc/step/custom_ai_prompt.md)     |
| Document Type Identifier Step      | Automatically identifies document types   | [Document Type Identifier Step Documentation](./doc/proc/step/document_type_identifier.md)     |
| AI Search Index Writer Step| Writes data to AI search index     | [AI Search Index Writer Step Documentation](./doc/proc/step/ai_search_index_writer.md) |



## Creating Custom Components

### Custom Service

1. **Create service class:**
```python
# doc/proc/service/my_custom_service.py
from doc.proc.service.service_base import ServiceBase

class MyCustomService(ServiceBase):
    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        super().__init__(name, type, settings, **kwargs)
        self.api_key = settings.get("api_key")
        self.endpoint = settings.get("endpoint")
    
    async def test_connection(self) -> bool:
        # Implement connection test
        return True
    
    async def process_data(self, data):
        # Implement custom processing
        return processed_data
```

2. **Add to service catalog:**
```yaml
services_catalog:
  - id: my_custom_service_01
    name: "My Custom Service"
    type: custom_service
    module_name: my_custom_service
    module_path: ./doc/proc/service/my_custom_service.py
    class_name: MyCustomService
    settings_schema:
      api_key:
        type: string
        required: true
        sensitive: true
      endpoint:
        type: string
        required: true
```

View the [Service documentation](SERVICE_README.md) for more details on how to create and use services.

### Custom Step

1. **Create step class:**
```python
# doc/proc/step/my_custom_step.py
from doc.proc.step.step_base import StepBase, StepInputOutput

class MyCustomStep(StepBase):
    async def run(self, input_data: StepInputOutput, 
                  context, **kwargs) -> StepInputOutput:
        
        # Get step settings
        setting1 = self.settings.get("setting1", "default_value")
        
        # Get services if needed
        service = context.get_service("my_service_instance")
        
        # Process data
        result = await self.process_logic(input_data.data, setting1)
        
        # Return updated data
        return StepInputOutput(
            summary_data={
                **input_data.summary_data,
                "custom_step_completed": True
            },
            data={
                **input_data.data,
                "custom_result": result
            }
        )
    
    async def process_logic(self, data, setting):
        # Implement custom processing logic
        return {"processed": True, "setting_used": setting}
```

2. **Add to step catalog:**
```yaml
step_catalog:
  - id: my_custom_step
    name: "My Custom Step"
    type: script
    module_name: my_custom_step
    module_path: ./doc/proc/step/my_custom_step.py
    class_name: MyCustomStep
    settings_schema:
      setting1:
        type: string
        title: "Custom Setting"
        default: "default_value"
```

3. **Use in pipeline:**
```yaml
steps:
  - name: my_custom_processing
    step_catalog_id: my_custom_step
    enabled: true
    services: [my_service_instance]
    settings:
      setting1: "custom_value"
```

#### View the [Step documentation](STEP_README.md) for more details on how to create steps and use them in pipelines.


## Environment Variables

Create a `.env` file with your configuration:

```bash
# Azure Storage
AZURE_STORAGE_SERVICE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_SERVICE_CREDENTIAL_TYPE=azure_key_credential
AZURE_STORAGE_SERVICE_ACCOUNT_KEY=your_storage_key

# Azure AI Services
AZURE_AI_INFERENCE_SERVICE_ENDPOINT=https://your-ai-service.openai.azure.com/
AZURE_AI_INFERENCE_SERVICE_CREDENTIAL_TYPE=azure_key_credential
AZURE_AI_INFERENCE_SERVICE_API_KEY=your_api_key

# Azure AI Search
AZURE_AI_SEARCH_SERVICE_ACCOUNT_NAME=your_search_service_account_name
AZURE_AI_SEARCH_SERVICE_CREDENTIAL_TYPE=azure_key_credential
AZURE_AI_SEARCH_SERVICE_API_KEY=your_search_api_key

# Azure Cosmos DB
AZURE_COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
AZURE_COSMOS_DB_KEY=your_cosmos_key

# Logging
LOG_LEVEL=DEBUG
```

## Troubleshooting

### Common Issues

1. **Configuration Loading Errors**
   ```
   Error: Service configuration validation failed
   ```
   - Check YAML syntax and indentation
   - Verify all required fields are present
   - Ensure environment variables are set

2. **Service Connection Failures**
   ```
   Error: Failed to connect to Azure service
   ```
   - Verify credentials and endpoints
   - Check network connectivity
   - Validate service permissions

3. **Step Execution Errors**
   ```
   Error: Step failed with timeout
   ```
   - Increase timeout values in step configuration
   - Check input data format and availability
   - Review step-specific logs

4. **Module Import Errors**
   ```
   Error: Cannot import module 'custom_step'
   ```
   - Verify module paths in catalog configuration - paths should be relative to the location the executable code is running from
   - Check Python path and module structure
   - Ensure all dependencies are installed

### Debugging Tips

1. **Enable Debug Logging:**
   ```python
   import logging
   logging.getLogger("doc.proc").setLevel(logging.DEBUG)
   ```

2. **Test Services Individually:**
   ```python
   service = await context.get_service("service_name")
   connection_ok = await service.test_connection()
   ```

3. **Validate Configuration:**
   ```python
   # Test configuration loading
   try:
       config = ServiceConfig.from_file("service_catalog.yaml")
       print("Configuration loaded successfully")
   except Exception as e:
       print(f"Configuration error: {e}")
   ```

### Performance Optimization

1. **Async Processing**: Use `asyncio.gather()` for parallel step execution
2. **Connection Pooling**: Reuse service connections across steps
3. **Memory Management**: Process large documents in chunks
4. **Caching**: Cache intermediate results for repeated processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

