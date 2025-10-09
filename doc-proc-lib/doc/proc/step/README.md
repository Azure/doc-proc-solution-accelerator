# Document Processing Library - Steps Documentation

This document provides comprehensive documentation for creating, configuring, and managing steps in the document processing pipeline system.

## Table of Contents

1. [Overview](#overview)
2. [Step Architecture](#step-architecture)
3. [Creating a Custom Step](#creating-a-custom-step)
4. [Step Configuration](#step-configuration)
5. [Step Catalog YAML Reference](#step-catalog-yaml-reference)
6. [Built-in Steps](#built-in-steps)
7. [Document Data Model](#document-data-model)
8. [Conditional Step Execution](#conditional-step-execution)
9. [Service Integration](#service-integration)
10. [Best Practices](#best-practices)
11. [Examples](#examples)
12. [Troubleshooting](#troubleshooting)

## Overview

The document processing system uses a modular step-based architecture where each processing operation is encapsulated in a reusable step. Steps can be chained together to create complex document processing pipelines.

### Key Features

- **Modular Design**: Each step is self-contained and reusable
- **Configuration-Driven**: Steps are configured through YAML files
- **UI Integration**: Automatic form generation for step configuration
- **Error Handling**: Built-in retry mechanisms and error propagation
- **Type Safety**: Pydantic-based validation for all configurations
- **Service Integration**: Support for external services (Azure AI, Storage, etc.)
- **Conditional Execution**: Steps can have conditions that define when the step runs based on document property

## Step Architecture

### Core Components

1. **StepBase**: Abstract base class that all steps must inherit from
2. **StepInstanceConfig**: Pydantic model for step instance configuration
3. **Document**: Data structure for step input/output
4. **Step Catalog**: YAML file containing reusable step definitions
5. **StepExecutionError**: Custom exception for step execution errors

### Step Lifecycle

```
Pipeline Start → Document → Step Execution → Document → Next Step
```

Each step receives:
- Input data from the previous step (via Document)
- Configuration settings (via StepInstanceConfig)
- Pipeline execution context (for accessing services and logging)


## Creating a Custom Step

### 1. Implement the Step Class

Create a new Python file in the `doc/proc/step/` directory:

```python
from typing import TYPE_CHECKING
from doc.proc.step.step_base import StepBase, StepInputOutput, StepInstanceConfig

if TYPE_CHECKING:
    from doc.proc.pipeline.pipeline_base import PipelineExecutionContext

class MyCustomStep(StepBase):
    
    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)

    async def run(self, document: Document, 
                  context: "PipelineExecutionContext", 
                  **kwargs) -> Document:
        """
        Implement your step logic here.
        
        Args:
            document: Data from the previous step
            context: Pipeline execution context
            **kwargs: Additional runtime parameters
            
        Returns:
            Document: Processed data for the next step
        """
        # Access settings from instance config
        my_setting = self.settings.get("my_setting", "default_value")
        
        # Process the input data
        self.process_data(document.data, my_setting)
        
        # Return updated document
        document
    
    def process_data(self, data: dict, setting: str):
        """Custom processing logic"""
        # Implement your processing logic here
        
        data['new_field'] = 'some value'
```

### 2. Add Step to Catalog

Add your step definition to `step_catalog.yaml`:

```yaml
step_catalog:
  - id: my_custom_step
    name: "My Custom Step"
    description: "Custom step for specific processing needs"
    type: script
    module_name: my_custom_step
    module_path: ./doc/proc/step/my_custom_step.py
    class_name: MyCustomStep
    tags: [custom, processing]
    category: "Custom Processing"
    version: "1.0"
    
    settings_schema:
      my_setting:
        type: string
        title: "My Setting"
        description: "Configuration parameter for the step"
        default: "default_value"
        required: true
    
    ui_metadata:
      icon: "cog"
      color: "#3B82F6"
      description_short: "Performs custom processing operations."
      description_long: "A custom step that processes documents according to specific business requirements."
```

## Step Configuration

### Required Fields

- **id**: Unique identifier for the step
- **name**: Human-readable name
- **type**: Step type (currently "script")
- **module_name**: Python module name
- **module_path**: Path to the Python file
- **class_name**: Name of the step class

### Optional Fields

- **description**: Step description
- **tags**: List of tags for categorization
- **category**: Category for grouping steps
- **version**: Step version
- **settings_schema**: Schema for step configuration parameters
- **ui_metadata**: UI display information

## Step Catalog YAML Reference

The `step_catalog.yaml` file defines reusable step configurations that can be referenced in pipelines. This file serves as the central registry for all available steps in your document processing system.

### File Location and Structure

The step catalog is located at: `doc-proc-lib/step_catalog.yaml`

```yaml
# step_catalog.yaml - Reusable step definitions

step_catalog:
  # Each step definition follows this structure
  - id: step_identifier                    # Unique identifier for the step
    name: "Human Readable Name"            # Display name for UI
    description: "Step description"        # Detailed description
    type: script                           # Currently only 'script' is supported
    module_name: module_name               # Python module name (without .py)
    module_path: ./path/to/module.py       # Relative path to Python file
    class_name: ClassName                  # Exact Python class name
    tags: [tag1, tag2, tag3]               # Optional tags for filtering/categorization
    category: "Category Name"              # Grouping category (Input/Processor/Extractor/Output/AI)
    version: "1.0"                         # Version for tracking changes
    
    # Configuration parameters schema
    settings_schema:
      parameter_name:
        type: string|integer|number|boolean|array|object
        title: "Display Name"
        description: "Parameter description"
        default: "default_value"          # Default value
        required: true|false              # Whether parameter is required
        # ... additional validation properties
    
    # UI display information
    ui_metadata:
      icon: "icon_name"                   # Icon identifier for UI
      color: "#HEX_COLOR"                 # Color theme for UI
      description_short: "Brief description (1-2 sentences)"
      description_long: "Detailed description with usage information"
```

### Complete Step Definition Example

Here's a comprehensive example showing all possible fields:

```yaml
step_catalog:
  - id: advanced_text_processor
    name: "Advanced Text Processor"
    description: "Processes documents with advanced AI-powered text analysis and enhancement"
    type: script
    module_name: advanced_text_processor
    module_path: ./doc/proc/step/advanced_text_processor.py
    class_name: AdvancedTextProcessorStep
    tags: [ai, text, processing, nlp, enhancement]
    category: "AI Processing"
    version: "2.1"
    
    settings_schema:
      # Service integration
      ai_service:
        type: string
        title: "AI Service"
        description: "AI service instance for text processing"
        required: true
        ui_component: "service_selector"
        service_type: "azure_ai_inference"
      
      # Text processing options
      processing_mode:
        type: string
        title: "Processing Mode"
        description: "How to process the text content"
        default: "enhanced"
        enum: ["basic", "enhanced", "comprehensive"]
        ui_component: "select"
      
      # Numeric parameters
      chunk_size:
        type: integer
        title: "Chunk Size"
        description: "Maximum characters per processing chunk"
        default: 4000
        min: 1000
        max: 10000
        multipleOf: 500
        ui_component: "input"
      
      confidence_threshold:
        type: number
        title: "Confidence Threshold"
        description: "Minimum confidence score for processing results"
        default: 0.8
        min: 0.0
        max: 1.0
        multipleOf: 0.1
        ui_component: "slider"
      
      # Boolean flags
      enable_summarization:
        type: boolean
        title: "Enable Summarization"
        description: "Generate document summaries during processing"
        default: true
        ui_component: "checkbox"
      
      # Text areas for prompts
      custom_prompt:
        type: string
        title: "Custom Processing Prompt"
        description: "Custom prompt for AI processing (leave empty for default)"
        default: ""
        ui_component: "textarea"
        pattern: "^[\\s\\S]{0,1000}$"  # Regex for validation
      
      # Array parameters
      output_formats:
        type: array
        title: "Output Formats"
        description: "Formats to generate for processed content"
        items:
          type: string
          enum: ["markdown", "html", "json", "plain_text"]
        default: ["markdown", "json"]
        ui_component: "multiselect"
      
      # Object parameters for complex configurations
      ai_parameters:
        type: object
        title: "AI Parameters"
        description: "Advanced AI model parameters"
        properties:
          temperature:
            type: number
            default: 0.7
            min: 0.0
            max: 2.0
          max_tokens:
            type: integer
            default: 2000
            min: 100
            max: 8000
          top_p:
            type: number
            default: 0.9
            min: 0.1
            max: 1.0
        default:
          temperature: 0.7
          max_tokens: 2000
          top_p: 0.9
    
    ui_metadata:
      icon: "brain-circuit"
      color: "#8B5CF6"
      description_short: "Advanced AI-powered text processing with customizable parameters."
      description_long: "This step provides comprehensive text processing using AI services with support for summarization, enhancement, and multiple output formats. Ideal for document intelligence workflows requiring high-quality text analysis and transformation."
```

### Field Descriptions

#### Core Fields (Required)
- **`id`**: Unique identifier used in pipeline configurations. Use snake_case.
- **`name`**: Human-readable name displayed in UI. Use Title Case.
- **`type`**: Step type. Currently only `"script"` is supported.
- **`module_name`**: Python module name without `.py` extension.
- **`module_path`**: Relative path from the catalog file to the Python module.
- **`class_name`**: Exact name of the Python class implementing the step.

#### Optional Metadata Fields  
- **`description`**: Detailed explanation of what the step does.
- **`tags`**: Array of tags for filtering and categorization.
- **`category`**: High-level grouping (Input, Processor, Extractor, Output, AI).
- **`version`**: Version string for tracking changes and compatibility.

#### Schema and UI Fields
- **`settings_schema`**: JSON Schema defining configuration parameters.
- **`ui_metadata`**: Display information for user interfaces.

### Category Guidelines

Use these standard categories for consistency:

- **Input**: Steps that retrieve or load content (file downloaders, content retrievers)
- **Processor**: Steps that analyze or transform data (document type identification, format conversion)
- **Extractor**: Steps that extract information from documents (text extraction, metadata extraction)
- **AI**: Steps that use artificial intelligence (custom prompts, entity extraction, summarization)
- **Output**: Steps that write or store results (index writers, file uploaders)
- **Development**: Steps for testing and development purposes

### Tags Best Practices

Use consistent, descriptive tags:

```yaml
# Good tags
tags: [pdf, text, extraction, ai, ocr]
tags: [azure, storage, upload, output]
tags: [entity, nlp, relationships, ai]

# Avoid generic or redundant tags
tags: [step, processor, good]  # Too generic
```


## Built-in Steps

### Individual Step Documentation

The following table provides links to detailed documentation for each individual step:

| Step ID | Step Name | Category | Description | Documentation |
|---------|-----------|----------|-------------|---------------|
| `sample_step` | Sample Development Step | Development | A sample step that shows a simple example of how to develop custom steps | [sample.py](./sample.py) |
| `content_retriever` | Content Retriever | Input | Retrieves content from various sources including Azure Blob Storage | [content_retriever.py](./content_retriever.py) |
| `file_downloader` | File Downloader | Input | Downloads files from Azure Blob Storage to local temporary directory | [file_downloader.md](./file_downloader.md) |
| `document_type_identifier` | Document Type Identifier | Processor | Automatically identifies and categorizes document types using magic bytes detection and file extension analysis | [document_type_identifier.md](./document_type_identifier.md) |
| `ai_pdf_text_extractor` | AI PDF Text Extractor | Extractor | Extracts text and metadata from PDF documents using AI-powered OCR and image analysis | [ai_pdf_text_extractor.md](./ai_pdf_text_extractor.md) |
| `ai_word_text_extractor` | AI Word Text Extractor | Extractor | Extracts text content, tables, and images from Microsoft Word documents (.docx format) with intelligent chunking | [ai_word_text_extractor.md](./ai_word_text_extractor.md) |
| `ai_pptx_text_extractor` | AI PowerPoint Text Extractor | Extractor | Extracts text content, tables, and images from Microsoft PowerPoint presentations (.pptx format) | [ai_pptx_text_extractor.md](./ai_pptx_text_extractor.md) |
| `excel_text_extractor` | Excel Text Extractor | Extractor | Extracts text content, images, and charts from Microsoft Excel spreadsheets (.xlsx, .xls, .xlsm, .xlsb formats) | [excel_text_extractor.md](./excel_text_extractor.md) |
| `azure_document_intelligence_extractor` | Azure Document Intelligence Extractor | Extractor | Extract structured content from documents using Azure Document Intelligence service | [azure_document_intelligence_extractor.md](./azure_document_intelligence_extractor.md) |
| `custom_ai_prompt` | Custom AI Prompt | AI | Applies custom AI prompts to document content for specialized analysis, transformation, and enhancement | [custom_ai_prompt.md](./custom_ai_prompt.md) |
| `entity_extractor` | Entity Extractor | Extractor | Extracts named entities and relationships from document content using AI-powered NLP for advanced text analysis | [entity_extractor.md](./entity_extractor.md) |
| `ai_search_index_writer` | AI Search Index Writer | Output | Writes processed document data to Azure AI Search indexes with configurable field mappings | [ai_search_index_writer.md](./ai_search_index_writer.md) |
| `blob_store_output` | Blob Store Output | Output | Writes the pipeline processing output to Azure Blob Storage | [blob_store_output.py](./blob_store_output.py) |


## Document Data Model

The document processing pipeline uses a standardized data model for passing information between steps. Understanding this model is crucial for developing effective steps.

**📖 Comprehensive Models Documentation**: 

For detailed information about the `Document`, `ContentIdentifier`, and `PipelineInput` models, including usage patterns and examples, see the [Models Documentation](../models/README.md).

### Document Structure

Each step receives and returns a `Document` object with the following structure:

```python
from pydantic import BaseModel
from typing import Dict, Any, Optional

class Document(BaseModel):
    id: ContentIdentifier = None
    summary_data: Dict[str, Any] = {}
    data: Dict[str, Any] = {}
```

#### Key Fields Explanation

- **`id`**: Identifier of the document for tracking the data through the pipeline
- **`summary_data`**: High-level metadata about the processing (e.g., counts, status, timing)
- **`data`**: The main payload containing document content and processing results


### Accessing Data in Steps

```python
async def run(self, document: Document, 
              context: "PipelineExecutionContext", 
              **kwargs) -> Document:
    
    file_path = document.data.get("file_path")
    chunks = document.data.get("chunks", [])
        
    # Process chunks
    for chunk in chunks:
      text = chunk.get("text", "")
      # Process text...
      chunk["processed_text"] = processed_result
    
    # Update summary data
    document.summary_data[f"{self.name}_processed"] = len(chunks)
    
    return document
```

## Conditional Step Execution

Steps can be configured to execute only when certain conditions are met, enabling dynamic pipeline behavior based on document properties or processing results.

### Condition Syntax

Conditions are specified using Python expressions that are evaluated against the document data:

```yaml
steps:
  - name: pdf_processor
    step_catalog_id: ai_pdf_text_extractor
    condition: "document_type.primary_type == 'pdf'"
    
  - name: large_file_processor
    step_catalog_id: custom_processor
    condition: "file_size > 10485760"  # 10MB
    
  - name: multi_condition_step
    step_catalog_id: advanced_processor
    condition: "document_type.primary_type in ['pdf', 'word'] and file_size < 5242880"
```

### Available Variables in Conditions

When evaluating conditions, the following variables are available from the document context:

- **Document Properties**: `file_path`, `file_name`, `file_size`, `content_type`
- **Document Type**: `document_type.primary_type`, `document_type.mime_type`, `document_type.confidence`
- **Custom Fields**: Any fields added by previous steps

### Complex Condition Examples

```yaml
# Process only English PDFs larger than 1MB
condition: "document_type.primary_type == 'pdf' and file_size > 1048576 and language == 'en'"

# Process documents that failed previous extraction
condition: "extraction_status == 'failed' or extraction_confidence < 0.7"

# Process based on file name patterns
condition: "file_name.endswith('.pdf') and 'contract' in file_name.lower()"

# Process based on chunk count
condition: "len(chunks) > 5"
```

### Conditional Processing Best Practices

1. **Use Simple Conditions**: Keep conditions readable and maintainable
2. **Handle Missing Fields**: Use `.get()` method or check field existence
3. **Document Conditions**: Comment complex conditions for clarity
4. **Test Conditions**: Verify conditions work with sample data

## Service Integration

Steps can integrate with external services through the service configuration system. This enables secure, reusable connections to cloud services.

### Using Services in Steps

#### Service Selection in Pipeline Configuration
```yaml
steps:
  - name: pdf_extractor
    step_catalog_id: ai_pdf_text_extractor
    services: [ai_service, primary_storage]  # Reference services by name
    settings:
      ...
```

#### Accessing Services in Step Code
```python
async def run(self, document: Document, 
              context: "PipelineExecutionContext", 
              **kwargs) -> Document:
    
    # Get service instance
    ai_service = context.get_service_instance("ai_service")
    storage_service = context.get_service_instance("primary_storage")
    
    # Use services
    if ai_service:
        response = await ai_service.make_request(prompt_data)
    
    if storage_service:
        await storage_service.upload_blob(file_data)
    
    return document
```

### Service Configuration Schema

#### In Step Catalog
```yaml
settings_schema:
  ai_model_inference_service:
    type: string
    title: "AI Inference Service"
    description: "Reference to the AI service instance to use"
    required: true
    ui_component: "service_selector"
    service_type: "azure_ai_inference"
```

#### Service Selector UI Component

The `service_selector` UI component automatically populates with available services of the specified type:

- `azure_blob_storage`: Azure Blob Storage services
- `azure_ai_inference`: Azure AI/OpenAI services  
- `azure_ai_search`: Azure AI Search services
- `azure_document_intelligence`: Azure Document Intelligence services
- `other_service`: Other custom service

## Best Practices

### Step Development

1. **Inherit from StepBase**: Always extend the `StepBase` class
2. **Handle Errors Gracefully**: Use try-catch blocks and meaningful error messages
3. **Validate Input**: Check required input parameters before processing
4. **Log Operations**: Use appropriate logging for debugging and monitoring
5. **Return Consistent Output**: Always return a `Document` object

### Configuration Design

1. **Provide Defaults**: Set sensible default values for optional parameters
2. **Use Descriptive Names**: Choose clear, self-explanatory parameter names
3. **Add Validation**: Use type constraints, ranges, and patterns
4. **Document Everything**: Provide clear descriptions for all parameters
5. **Group Related Settings**: Use logical parameter organization

### Error Handling

```python
async def run(self, document: Document, 
              context: "PipelineExecutionContext", 
              **kwargs) -> Document:
    try:
        # Step logic here
        self.process_data(document.data)
        return document
    except Exception as e:
        # Log the error
        logger.error(f"Step {self.name} failed: {str(e)}")
        # Re-raise as StepExecutionError if needed
        raise StepExecutionError(f"Failed to process data: {str(e)}")
```

## Examples

This section provides comprehensive examples showing how to configure and use various steps in the document processing pipeline.

### Complete Pipeline Configuration Example

Here's a complete example showing how to configure multiple steps in a pipeline:

```yaml
# pipeline_config.yaml - Complete pipeline example
service_instances:
  - name: primary_blob_storage
    service_catalog_id: azure_storage_01
    settings:
      account_name: ${AZURE_STORAGE_SERVICE_ACCOUNT_NAME}
      credential_type: ${AZURE_STORAGE_SERVICE_CREDENTIAL_TYPE}
      credential_key: ${AZURE_STORAGE_SERVICE_ACCOUNT_KEY}

  - name: primary_ai_inference_service
    service_catalog_id: azure_ai_inference_service_01
    settings:
      endpoint: ${AZURE_AI_INFERENCE_SERVICE_ENDPOINT}
      credential_type: ${AZURE_AI_INFERENCE_SERVICE_CREDENTIAL_TYPE}
      api_key: ${AZURE_AI_INFERENCE_SERVICE_API_KEY}

pipelines:
  - name: document_processing_pipeline
    description: 'Complete document processing pipeline with conditional steps'
    version: '1.0'
    
    steps:
      # Step 1: Identify document types
      - name: document_type_identifier_1
        step_catalog_id: document_type_identifier
        enabled: true
        fail_pipeline_on_error: true
        settings:
          identification_methods: "magic_bytes, file_extension"
      
      # Step 2: Process PDF documents
      - name: pdf_text_extractor_1
        step_catalog_id: pdf_text_extractor
        enabled: true
        services: [primary_blob_storage, primary_ai_inference_service]
        condition: "document_type.primary_type == 'pdf'"
        settings:
          png_output_folder: "./output/png"
          num_pages: -1
          prompts:
            system: "Extract text from PDF pages as markdown"
            user: "Convert this page image to markdown text"
          max_completion_tokens: 4000
      
      # Step 3: Process Word documents
      - name: word_text_extractor_1
        step_catalog_id: word_text_extractor
        enabled: true
        services: [primary_ai_inference_service]
        condition: "document_type.primary_type == 'word_document'"
        settings:
          png_output_folder: "./output/png"
          extract_images: true
          extract_tables: true
          max_chunk_size: 4000
      
      # Step 4: Extract entities from all documents
      - name: entity_extractor_1
        step_catalog_id: entity_extractor
        enabled: true
        services: [primary_ai_inference_service]
        settings:
          chunk_field_to_extract_entities_from: "text"
          output_field_name: "extracted_entities"
          extract_people: true
          extract_organizations: true
          extract_locations: true
          extract_relationships: true
    
    execution_sequence: [document_type_identifier_1, pdf_text_extractor_1, word_text_extractor_1, entity_extractor_1]
```


### Advanced Configuration Examples

#### Conditional Processing Based on Document Properties

```yaml
# Process only large PDF files differently
- name: large_pdf_processor
  step_catalog_id: pdf_text_extractor
  enabled: true
  condition: "document_type.primary_type == 'pdf' and file_size > 10485760"  # 10MB
  settings:
    num_pages: 5  # Limit pages for large files
    
# Process small documents with full extraction
- name: small_doc_processor
  step_catalog_id: pdf_text_extractor
  enabled: true
  condition: "document_type.primary_type == 'pdf' and file_size <= 10485760"
  settings:
    num_pages: -1  # Process all pages for smaller files
```

#### Multi-Service Integration

```yaml
- name: comprehensive_processor
  step_catalog_id: word_text_extractor
  enabled: true
  services: [azure_ai_service, azure_blob_storage]  # Multiple services
  settings:
    extract_images: true
    extract_tables: true
    # Service-specific configurations can be handled by the step implementation
```

---

## Troubleshooting

This section covers common issues and solutions when working with steps.

### Common Issues

#### Step Not Found Error
```
Error: Step 'my_custom_step' not found in catalog
```
**Solution**: Ensure the step is properly defined in `step_catalog.yaml` and the module path is correct.

#### Import Errors
```
ImportError: cannot import name 'MyCustomStep' from 'my_custom_step'
```
**Solutions**:
1. Verify the `class_name` in the step catalog matches your Python class name
2. Check that the `module_path` points to the correct file
3. Ensure your step class is properly defined and inherits from `StepBase`

#### Service Not Available
```
Error: Service 'ai_service' not found or not configured
```
**Solutions**:
1. Verify the service is defined in the pipeline configuration
2. Check that the service name matches exactly (case-sensitive)
3. Ensure the service is included in the step's `services` list

#### Condition Evaluation Errors
```
Error evaluating condition: 'document_type' is not defined
```
**Solutions**:
1. Ensure the field exists in the document data before using it in conditions
2. Use safe access: `getattr(document, 'field', None)`
3. Check that previous steps have populated the required fields

#### Schema Validation Errors
```
ValidationError: field required (type=value_error.missing)
```
**Solutions**:
1. Check that all required settings are provided in the step configuration
2. Verify the settings schema matches the step's expectations
3. Provide default values for optional settings

### Debugging Steps

#### Enable Debug Mode
Add debug logging to your steps:

```python
async def run(self, document: Document, 
              context: "PipelineExecutionContext", 
              **kwargs) -> Document:
    
    if self.debug_mode:
        logger.debug(f"Step {self.name} input: {document}")
    
    # Your step logic here
    
    if self.debug_mode:
        logger.debug(f"Step {self.name} output: {result}")
    
    return result
```

#### Use Pipeline Debug Configuration
```yaml
pipeline:
  
  steps:
    - name: my_step
      debug_mode: true  # Enable debug for specific steps
```

### Performance Issues

#### Memory Usage
- **Issue**: Steps consuming too much memory with large documents
- **Solution**: Process documents in chunks, use streaming where possible

```python
# Process large files in chunks
async def process_large_document(self, document):
    chunk_size = self.settings.get("chunk_size", 1000000)  # 1MB chunks
    
    with open(document["file_path"], "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield self.process_chunk(chunk)
```

#### Slow Processing
- **Issue**: Steps taking too long to process
- **Solutions**:
  - Use async/await for I/O operations
  - Implement parallel processing for independent tasks
  - Add caching for repeated operations

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def run(self, step_input: StepInputOutput, context, **kwargs):
    documents = step_input.data.get("documents", [])
    
    # Process documents in parallel
    semaphore = asyncio.Semaphore(5)  # Limit concurrency
    
    async def process_with_semaphore(doc):
        async with semaphore:
            return await self.process_document(doc)
    
    tasks = [process_with_semaphore(doc) for doc in documents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return step_input
```

## Support

For questions or issues with step development:

1. Check the existing step implementations in `doc/proc/step/`
2. Review the step catalog configuration in `step_catalog.yaml`
3. Refer to the base classes in `step_base.py` and `step_config.py`

## Contributing

When contributing new steps:

1. Follow the naming conventions
2. Include comprehensive settings schema
3. Add appropriate UI metadata
4. Write unit tests for your step
5. Update this documentation if needed
