# Document Processing Library - Steps Documentation

This document provides comprehensive documentation for creating, configuring, and managing steps in the document processing pipeline system.

## Table of Contents

1. [Overview](#overview)
2. [Step Architecture](#step-architecture)
3. [Creating a Custom Step](#creating-a-custom-step)
4. [Step Configuration](#step-configuration)
5. [Step Catalog YAML Reference](#step-catalog-yaml-reference)
6. [Settings Schema Reference](#settings-schema-reference)
7. [UI Metadata Reference](#ui-metadata-reference)
8. [Built-in Steps](#built-in-steps)
9. [Best Practices](#best-practices)
10. [Examples](#examples)

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
3. **StepInputOutput**: Data structure for step input/output
4. **Step Catalog**: YAML file containing reusable step definitions
5. **StepExecutionError**: Custom exception for step execution errors

### Step Lifecycle

```
Pipeline Start → Step Input → Step Execution → Step Output → Next Step
```

Each step receives:
- Input data from the previous step (via StepInputOutput)
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

    async def run(self, step_input: StepInputOutput, 
                  context: "PipelineExecutionContext", 
                  **kwargs) -> StepInputOutput:
        """
        Implement your step logic here.
        
        Args:
            step_input: Data from the previous step
            context: Pipeline execution context
            **kwargs: Additional runtime parameters
            
        Returns:
            StepInputOutput: Processed data for the next step
        """
        # Access settings from instance config
        my_setting = self.settings.get("my_setting", "default_value")
        
        # Process the input data
        processed_data = self.process_data(step_input.data, my_setting)
        
        # Return updated output
        return StepInputOutput(
            summary_data={**step_input.summary_data, "step_completed": True},
            data={**step_input.data, **processed_data}
        )
    
    def process_data(self, data: dict, setting: str) -> dict:
        """Custom processing logic"""
        # Implement your processing logic here
        return {"processed": True, "setting_used": setting}
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

The `step_catalog.yaml` file defines reusable step configurations that can be referenced in pipelines.

### Structure

```yaml
step_catalog:
  - id: step_identifier
    name: "Human Readable Name"
    description: "Step description"
    type: script  # Currently only 'script' is supported
    module_name: module_name  # Python module name
    module_path: ./path/to/module.py  # Relative path to Python file
    class_name: ClassName  # Python class name
    tags: [tag1, tag2, tag3]  # Optional tags for filtering
    category: "Category Name"  # Optional category
    version: "1.0"  # Optional version
    
    # Configuration schema
    settings_schema:
      parameter_name:
        type: string|integer|number|boolean
        title: "Display Name"
        description: "Parameter description"
        # ... additional schema properties
    
    # UI metadata
    ui_metadata:
      icon: "icon_name"
      color: "#HEX_COLOR"
      description_short: "Brief description"
      description_long: "Detailed description"
```

## Settings Schema Reference

The `settings_schema` section defines the configuration parameters for each step, enabling automatic UI generation and validation.

### Supported Types

#### String Parameters

```yaml
string_param:
  type: string
  title: "String Parameter"
  description: "A text input parameter"
  default: "default_value"
  required: true
  pattern: "^[a-zA-Z0-9]+$"  # Regex validation
  enum: ["option1", "option2", "option3"]  # Dropdown options
  ui_component: "input|textarea|service_selector"
  service_type: "azure_blob|azure_ai_inference"  # For service selectors
```

#### Numeric Parameters

```yaml
integer_param:
  type: integer
  title: "Integer Parameter"
  description: "A whole number parameter"
  default: 10
  min: 0
  max: 100
  multipleOf: 5  # Step size

number_param:
  type: number
  title: "Number Parameter"
  description: "A decimal number parameter"
  default: 1.5
  min: 0.0
  max: 10.0
  multipleOf: 0.1
```

#### Boolean Parameters

```yaml
boolean_param:
  type: boolean
  title: "Boolean Parameter"
  description: "A true/false parameter"
  default: true
```

### UI Components

- **input**: Standard text input (default for strings)
- **textarea**: Multi-line text input
- **service_selector**: Dropdown for selecting configured services

### Service Types

When using `ui_component: "service_selector"`, specify the service type:

- **azure_blob**: Azure Blob Storage services
- **azure_ai_inference**: Azure AI Inference services

## UI Metadata Reference

The `ui_metadata` section provides information for displaying steps in the UI.

```yaml
ui_metadata:
  icon: "icon_name"              # Icon identifier
  color: "#HEX_COLOR"            # Color in hex format
  description_short: "Brief description (1-2 sentences)"
  description_long: "Detailed description with usage information"
```

### Common Icons

- `gear`: Configuration/settings
- `image`: Image processing
- `brain`: AI/ML processing
- `file`: File operations
- `database`: Data operations
- `cloud`: Cloud services

## Built-in Steps

### Individual Step Documentation

The following table provides links to detailed documentation for each individual step:

| Step Name | Description | Documentation |
|-----------|-------------|---------------|
| Sample Development Step | A development and testing step that processes documents with configurable key-value pairs | [sample](./sample.py) |
| Document Type Identifier | Automatically identifies and categorizes document types using magic bytes detection and file extension analysis | [document_type_identifier](./document_type_identifier.md) |
| PDF Text Extractor | Extracts text and metadata from PDF documents using AI-powered OCR and image analysis | [pdf_text_extractor](./pdf_text_extractor.md) |
| Word Text Extractor | Extracts text content, tables, and images from Microsoft Word documents (.docx format) with intelligent chunking | [word_text_extractor](./word_text_extractor.md) |
| PowerPoint Text Extractor | Extracts text content, tables, and images from Microsoft PowerPoint presentations (.pptx format) | [pptx_text_extractor](./pptx_text_extractor.md) |
| Excel Text Extractor | Extracts text content, images, and charts from Microsoft Excel spreadsheets (.xlsx, .xls, .xlsm, .xlsb formats) | [excel_text_extractor](./excel_text_extractor.md) |
| Custom AI Prompt | Applies custom AI prompts to document content for specialized analysis, transformation, and enhancement | [custom_ai_prompt](./custom_ai_prompt.md) |
| AI Search Index Writer | Writes processed document data to Azure AI Search indexes with configurable field mappings | [ai_search_index_writer](./ai_search_index_writer.md) |
| Entity Extractor | Extracts named entities and relationships from document content using AI-powered NLP for advanced text analysis | [entity_extractor](./entity_extractor.md) |


## Best Practices

### Step Development

1. **Inherit from StepBase**: Always extend the `StepBase` class
2. **Handle Errors Gracefully**: Use try-catch blocks and meaningful error messages
3. **Validate Input**: Check required input parameters before processing
4. **Log Operations**: Use appropriate logging for debugging and monitoring
5. **Return Consistent Output**: Always return a `StepInputOutput` object

### Configuration Design

1. **Provide Defaults**: Set sensible default values for optional parameters
2. **Use Descriptive Names**: Choose clear, self-explanatory parameter names
3. **Add Validation**: Use type constraints, ranges, and patterns
4. **Document Everything**: Provide clear descriptions for all parameters
5. **Group Related Settings**: Use logical parameter organization

### Error Handling

```python
async def run(self, step_input: StepInputOutput, 
              context: "PipelineExecutionContext", 
              **kwargs) -> StepInputOutput:
    try:
        # Step logic here
        result = self.process_data(step_input.data)
        return StepInputOutput(
            summary_data=step_input.summary_data,
            data=result
        )
    except Exception as e:
        # Log the error
        context.logger.error(f"Step {self.name} failed: {str(e)}")
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
      account_name: ${STORAGE_ACCOUNT_NAME}
      credential_type: ${STORAGE_ACCOUNT_CREDENTIAL_TYPE}
      credential_key: ${STORAGE_ACCOUNT_KEY}

  - name: primary_ai_inference_service
    service_catalog_id: azure_ai_inference_service_01
    settings:
      endpoint: ${AZURE_AI_INFERENCE_SERVICE_ENDPOINT}
      credential_type: ${AZURE_AI_INFERENCE_SERVICE_CREDENTIAL_TYPE}
      api_key: ${AZURE_AI_INFERENCE_SERVICE_APIKEY}

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

### Individual Step Configuration Examples

#### 1. Document Type Identifier Configuration

```yaml
- name: document_type_identifier_main
  step_catalog_id: document_type_identifier
  enabled: true
  fail_pipeline_on_error: true
  settings:
    identification_methods: "magic_bytes, file_extension"
```

#### 2. PDF Text Extractor Configuration

```yaml
- name: pdf_extractor_advanced
  step_catalog_id: pdf_text_extractor
  enabled: true
  services: [azure_blob_storage, azure_ai_service]
  condition: "document_type.primary_type == 'pdf'"
  settings:
    png_output_folder: "./output/pdf_images"
    num_pages: 10  # Process first 10 pages only
    prompts:
      system: "You are an expert at extracting text from document images."
      user: |
        Extract all text from this document page image. 
        Format as markdown and include image descriptions.
        
        ==Extracted-Text==
        {text content here}
        ==End-Extracted-Text==
        
        ==Image-Descriptions==
        {image descriptions here}
        ==End-Image-Descriptions==
    max_completion_tokens: 8000
    temperature: 0.1
    top_p: 0.9
```

#### 3. Word Document Processing Configuration

```yaml
- name: word_processor_detailed
  step_catalog_id: word_text_extractor
  enabled: true
  services: [azure_ai_service]
  condition: "document_type.primary_type == 'word_document'"
  fail_step_on_document_error: false
  debug_mode: true
  settings:
    png_output_folder: "./output/word_images"
    extract_images: true
    extract_image_descriptions: true
    extract_tables: true
    max_chunk_size: 2000  # Smaller chunks for better processing
    prompts:
      system: "Extract text and describe images from Word document images."
      user: "Convert this image to markdown, preserving formatting and describing any images."
    max_completion_tokens: 4000
    temperature: 0.3
```

#### 4. Entity Extraction Configuration

```yaml
- name: comprehensive_entity_extractor
  step_catalog_id: entity_extractor
  enabled: true
  services: [azure_ai_service]
  settings:
    chunk_field_to_extract_entities_from: "markdown_text"
    output_field_name: "comprehensive_entities"
    extract_people: true
    extract_places: true
    extract_locations: true
    extract_organizations: true
    extract_relationships: true
    custom_entity_types: "contracts, dates, financial_amounts, legal_terms"
    output_format: "structured"
    include_confidence: true
    include_context: true
    prompts:
      system: "Extract entities and relationships with high precision."
      user: |
        Analyze the following text and extract:
        1. People (names, titles, roles)
        2. Organizations (companies, institutions)
        3. Locations (cities, countries, addresses)
        4. Custom entities: {custom_entity_types}
        5. Relationships between entities
        
        Text: {chunk_content}
```

#### 5. Custom AI Prompt Configuration

```yaml
- name: document_summarizer
  step_catalog_id: custom_ai_prompt
  enabled: true
  services: [azure_ai_service]
  settings:
    chunk_field_to_apply_prompt_on: "text"
    output_field_name: "document_summary"
    prompts:
      system: "You are an expert document summarizer."
      user: |
        Summarize the following document content in 3-5 sentences.
        Focus on key facts, main topics, and important conclusions.
        
        Document content: {chunk_content}
    max_completion_tokens: 500
    temperature: 0.3
```

#### 6. AI Search Index Writer Configuration

```yaml
- name: search_indexer
  step_catalog_id: ai_search_index_writer
  enabled: true
  services: [azure_ai_search_service]
  settings:
    index_name: "processed_documents"
    index_field_mappings: |
      {
        "chunk_id": "id",
        "input_file_path": "source_file",
        "text": "content",
        "markdown_text": "markdown_content",
        "extracted_entities": "entities",
        "document_summary": "summary",
        "chunk_type": "content_type"
      }
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

### Programming Examples

#### Custom Step Implementation

```python
from typing import TYPE_CHECKING
import asyncio
from doc.proc.step.step_base import StepBase, StepInputOutput, StepInstanceConfig, StepExecutionError

if TYPE_CHECKING:
    from doc.proc.pipeline.pipeline_base import PipelineExecutionContext

class DocumentAnalyzerStep(StepBase):
    """
    Custom step for advanced document analysis
    """
    
    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with validation
        self.analysis_type = self.settings.get("analysis_type", "basic")
        self.confidence_threshold = self.settings.get("confidence_threshold", 0.8)
        self.max_concurrent_documents = self.settings.get("max_concurrent_documents", 5)
        
    async def run(self, step_input: StepInputOutput, 
                  context: "PipelineExecutionContext", 
                  **kwargs) -> StepInputOutput:
        """
        Process documents with advanced analysis
        """
        
        documents = step_input.data.get("documents", [])
        if not documents:
            return step_input
            
        # Process documents concurrently with semaphore
        semaphore = asyncio.Semaphore(self.max_concurrent_documents)
        
        async def process_document(doc):
            async with semaphore:
                return await self._analyze_document(doc, context)
        
        # Run analysis tasks concurrently
        tasks = [process_document(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results and exceptions
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                context.logger.error(f"Failed to process document {i}: {result}")
                if self.fail_step_on_document_error:
                    raise StepExecutionError(f"Document analysis failed: {result}")
            else:
                successful_results.append(result)
        
        # Update documents with analysis results
        for doc, analysis in zip(documents, successful_results):
            if analysis:
                doc.update(analysis)
        
        return StepInputOutput(
            summary_data={
                **step_input.summary_data,
                f"{self.name}_processed": len(successful_results),
                f"{self.name}_failed": len([r for r in results if isinstance(r, Exception)])
            },
            data=step_input.data
        )
    
    async def _analyze_document(self, document: dict, context) -> dict:
        """
        Perform document analysis based on configuration
        """
        try:
            analysis_result = {
                "analysis_type": self.analysis_type,
                "confidence_score": 0.95,  # Example score
                "analysis_timestamp": context.get_current_timestamp(),
                "metadata": {
                    "analyzer_version": "1.0",
                    "processing_time_ms": 150
                }
            }
            
            # Perform different analysis based on type
            if self.analysis_type == "advanced":
                analysis_result["detailed_metrics"] = await self._perform_advanced_analysis(document)
            
            return analysis_result
            
        except Exception as e:
            context.logger.error(f"Analysis failed for document {document.get('file_path', 'unknown')}: {e}")
            raise StepExecutionError(f"Document analysis error: {e}")
    
    async def _perform_advanced_analysis(self, document: dict) -> dict:
        """
        Perform advanced document analysis
        """
        # Simulate advanced analysis
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "complexity_score": 0.75,
            "content_quality": 0.85,
            "processing_recommendations": ["extract_tables", "analyze_images"]
        }
```

#### Step Catalog Entry for Custom Step

```yaml
- id: document_analyzer
  name: "Advanced Document Analyzer"
  description: "Performs advanced analysis on documents with configurable parameters"
  type: script
  module_name: document_analyzer
  module_path: ./doc/proc/step/document_analyzer.py
  class_name: DocumentAnalyzerStep
  tags: [analysis, advanced, custom]
  category: "Advanced Processing"
  version: "1.0"
  
  settings_schema:
    analysis_type:
      type: string
      title: "Analysis Type"
      description: "Type of analysis to perform"
      default: "basic"
      enum: ["basic", "advanced", "comprehensive"]
      
    confidence_threshold:
      type: number
      title: "Confidence Threshold"
      description: "Minimum confidence score for results"
      default: 0.8
      min: 0.0
      max: 1.0
      multipleOf: 0.1
      
    max_concurrent_documents:
      type: integer
      title: "Max Concurrent Documents"
      description: "Maximum number of documents to process simultaneously"
      default: 5
      min: 1
      max: 20
  
  ui_metadata:
    icon: "analytics"
    color: "#8B5CF6"
    description_short: "Advanced document analysis with configurable parameters."
    description_long: "Performs comprehensive document analysis including complexity scoring, content quality assessment, and processing recommendations."
```

### File Processing Step

```python
import os
from pathlib import Path

class FileProcessorStep(StepBase):
    async def run(self, step_input: StepInputOutput, 
                  context: "PipelineExecutionContext", 
                  **kwargs) -> StepInputOutput:
        
        input_file = self.settings.get("input_file")
        output_directory = self.settings.get("output_directory", "./output")
        
        # Ensure output directory exists
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        
        # Process the file
        processed_files = self.process_file(input_file, output_directory)
        
        return StepInputOutput(
            summary_data={
                **step_input.summary_data,
                "files_processed": len(processed_files)
            },
            data={
                **step_input.data,
                "processed_files": processed_files
            }
        )
```

### API Integration Step

```python
import aiohttp

class APIIntegrationStep(StepBase):
    async def run(self, step_input: StepInputOutput, 
                  context: "PipelineExecutionContext", 
                  **kwargs) -> StepInputOutput:
        
        api_endpoint = self.settings.get("api_endpoint")
        api_key = self.settings.get("api_key")
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}"}
            
            async with session.post(api_endpoint, 
                                  json=step_input.data, 
                                  headers=headers) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return StepInputOutput(
                        summary_data=step_input.summary_data,
                        data=result
                    )
                else:
                    raise StepExecutionError(f"API call failed: {response.status}")
```

---

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
