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
9. [Step Input/Output Data Model](#step-inputoutput-data-model)
10. [Conditional Step Execution](#conditional-step-execution)
11. [Service Integration](#service-integration)
12. [Best Practices](#best-practices)
13. [Examples](#examples)
14. [Troubleshooting](#troubleshooting)

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
    type: script                          # Currently only 'script' is supported
    module_name: module_name              # Python module name (without .py)
    module_path: ./path/to/module.py      # Relative path to Python file
    class_name: ClassName                 # Exact Python class name
    tags: [tag1, tag2, tag3]             # Optional tags for filtering/categorization
    category: "Category Name"             # Grouping category (Input/Processor/Extractor/Output/AI)
    version: "1.0"                       # Version for tracking changes
    
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

## Settings Schema Reference

The `settings_schema` section defines the configuration parameters for each step, enabling automatic UI generation and validation.

### Supported Data Types

The settings schema supports JSON Schema data types with additional UI hints for form generation.

#### String Parameters

```yaml
# Basic text input
text_input:
  type: string
  title: "Text Input"
  description: "Single line text input"
  default: "default_value"
  required: true
  ui_component: "input"
  
# Multi-line text area
description_text:
  type: string
  title: "Description"
  description: "Multi-line text description"
  default: ""
  ui_component: "textarea"
  
# Pattern validation
username:
  type: string
  title: "Username"
  description: "Alphanumeric username only"
  pattern: "^[a-zA-Z0-9_]{3,20}$"
  ui_component: "input"
  
# Dropdown selection
processing_mode:
  type: string
  title: "Processing Mode"
  description: "Select processing strategy"
  default: "standard"
  enum: ["fast", "standard", "thorough", "custom"]
  ui_component: "select"
  
# Service selector (special component)
ai_service:
  type: string
  title: "AI Service"
  description: "AI service instance to use"
  required: true
  ui_component: "service_selector"
  service_type: "azure_ai_inference"
  
# File path with validation
output_folder:
  type: string
  title: "Output Folder"
  description: "Path to output directory"
  default: "./tmp/output"
  pattern: "^\\.\\/.*"  # Must start with ./
  ui_component: "input"
```

#### Numeric Parameters

```yaml
# Integer with range
page_count:
  type: integer
  title: "Page Count"
  description: "Number of pages to process (-1 for all)"
  default: -1
  min: -1
  max: 1000
  ui_component: "input"
  
# Integer with step size
batch_size:
  type: integer
  title: "Batch Size"
  description: "Documents per batch"
  default: 10
  min: 1
  max: 100
  multipleOf: 5  # Must be multiple of 5
  ui_component: "input"
  
# Decimal number
confidence_score:
  type: number
  title: "Confidence Threshold"
  description: "Minimum confidence (0.0-1.0)"
  default: 0.8
  min: 0.0
  max: 1.0
  multipleOf: 0.01  # Two decimal places
  ui_component: "slider"
  
# Temperature parameter for AI
temperature:
  type: number
  title: "Temperature"
  description: "Randomness in AI responses"
  default: 0.7
  min: 0.0
  max: 2.0
  multipleOf: 0.1
  ui_component: "input"
```

#### Boolean Parameters

```yaml
# Simple checkbox
extract_images:
  type: boolean
  title: "Extract Images"
  description: "Whether to extract images from document"
  default: true
  ui_component: "checkbox"
  
# Feature flag
enable_debug:
  type: boolean
  title: "Debug Mode"
  description: "Enable detailed logging and debugging"
  default: false
  ui_component: "checkbox"
```

#### Array Parameters

```yaml
# String array with predefined options
output_formats:
  type: array
  title: "Output Formats"
  description: "Select multiple output formats"
  items:
    type: string
    enum: ["json", "markdown", "html", "xml"]
  default: ["json", "markdown"]
  ui_component: "multiselect"
  
# Simple string array
keywords:
  type: array
  title: "Keywords"
  description: "List of keywords to search for"
  items:
    type: string
  default: []
  ui_component: "tags"  # Tag input interface
  
# Number array
thresholds:
  type: array
  title: "Confidence Thresholds"
  description: "Multiple confidence thresholds"
  items:
    type: number
    min: 0.0
    max: 1.0
  default: [0.7, 0.8, 0.9]
  ui_component: "list"
```

#### Object Parameters

```yaml
# Complex nested object
ai_parameters:
  type: object
  title: "AI Configuration"
  description: "Advanced AI model parameters"
  properties:
    model_name:
      type: string
      title: "Model Name"
      default: "gpt-4"
      enum: ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    temperature:
      type: number
      title: "Temperature"
      default: 0.7
      min: 0.0
      max: 2.0
    max_tokens:
      type: integer
      title: "Max Tokens"
      default: 2000
      min: 1
      max: 8000
    enable_streaming:
      type: boolean
      title: "Enable Streaming"
      default: false
  required: ["model_name"]
  default:
    model_name: "gpt-4"
    temperature: 0.7
    max_tokens: 2000
    enable_streaming: false
  
# Prompt configuration object
prompts:
  type: object
  title: "AI Prompts"
  description: "System and user prompts for AI processing"
  properties:
    system:
      type: string
      title: "System Prompt"
      description: "Instructions for the AI system"
      default: "You are a helpful assistant."
      ui_component: "textarea"
    user:
      type: string
      title: "User Prompt Template"
      description: "Template for user prompts (use {variables})"
      default: "Process this content: {content}"
      ui_component: "textarea"
  required: ["system", "user"]
  default:
    system: "You are a helpful assistant."
    user: "Process this content: {content}"
```

### UI Components

The `ui_component` field controls how parameters are rendered in the user interface:

#### Text Input Components
- **`input`**: Single-line text input (default for strings)
- **`textarea`**: Multi-line text area for longer content
- **`password`**: Password input with masked characters

#### Selection Components
- **`select`**: Dropdown selection from enum values
- **`multiselect`**: Multiple selection from array of enum values
- **`radio`**: Radio button selection (for small enum lists)
- **`checkbox`**: Boolean toggle switch

#### Numeric Input Components
- **`slider`**: Range slider for numeric values with min/max
- **`number`**: Numeric input with increment/decrement buttons
- **`range`**: Dual-handle range selector for min/max values

#### Specialized Components
- **`service_selector`**: Dropdown for selecting configured services
- **`file_selector`**: File browser for selecting local files
- **`color`**: Color picker for hex color values
- **`date`**: Date picker for date values
- **`time`**: Time picker for time values
- **`tags`**: Tag input for string arrays
- **`list`**: Dynamic list editor for arrays
- **`json`**: JSON editor for complex objects

#### Component Examples

```yaml
# Color picker for theme colors
theme_color:
  type: string
  title: "Theme Color"
  description: "Primary color for UI elements"
  default: "#3B82F6"
  pattern: "^#[0-9A-Fa-f]{6}$"
  ui_component: "color"

# File selector for local files
template_file:
  type: string
  title: "Template File"
  description: "Path to template file"
  default: ""
  ui_component: "file_selector"

# Range selector for numeric ranges
confidence_range:
  type: object
  title: "Confidence Range"
  description: "Acceptable confidence score range"
  properties:
    min:
      type: number
      default: 0.7
    max:
      type: number
      default: 0.95
  ui_component: "range"

# JSON editor for complex structures
metadata_mapping:
  type: object
  title: "Metadata Mapping"
  description: "Custom field mappings"
  default: {}
  ui_component: "json"
```

### Validation Options

#### String Validation

```yaml
# Length constraints
title:
  type: string
  minLength: 3
  maxLength: 100
  
# Regex pattern matching
email:
  type: string
  pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  
# Format validation (built-in formats)
url_endpoint:
  type: string
  format: "uri"  # Built-in URI format validation
  
# Custom validation with error messages
api_key:
  type: string
  pattern: "^[A-Za-z0-9]{32,64}$"
  patternErrorMessage: "API key must be 32-64 alphanumeric characters"
```

#### Numeric Validation

```yaml
# Range constraints
port_number:
  type: integer
  minimum: 1
  maximum: 65535
  exclusiveMinimum: false  # Include boundary values
  exclusiveMaximum: false
  
# Multiple constraints
percentage:
  type: number
  minimum: 0.0
  maximum: 100.0
  multipleOf: 0.1  # Must be multiple of 0.1
```

#### Array Validation

```yaml
# Array size constraints
selected_options:
  type: array
  minItems: 1      # At least one item required
  maxItems: 5      # Maximum five items
  uniqueItems: true # No duplicates allowed
  
# Item validation
scores:
  type: array
  items:
    type: number
    minimum: 0.0
    maximum: 10.0
  minItems: 3
  maxItems: 10
```

#### Object Validation

```yaml
# Required properties
user_config:
  type: object
  required: ["username", "email"]  # These properties must be present
  properties:
    username:
      type: string
      minLength: 3
    email:
      type: string
      format: "email"
    age:
      type: integer
      minimum: 18
  additionalProperties: false  # No extra properties allowed
```

### Conditional Schema (Advanced)

For complex validation logic, use conditional schemas:

```yaml
# Different validation based on mode
processing_config:
  type: object
  properties:
    mode:
      type: string
      enum: ["simple", "advanced"]
    batch_size:
      type: integer
  allOf:
    - if:
        properties:
          mode:
            const: "simple"
      then:
        properties:
          batch_size:
            maximum: 10
    - if:
        properties:
          mode:
            const: "advanced"
      then:
        properties:
          batch_size:
            maximum: 100
        required: ["advanced_options"]
```

### Service Types

When using `ui_component: "service_selector"`, specify the service type:

- **`azure_blob_storage`**: Azure Blob Storage services
- **`azure_ai_inference`**: Azure AI/OpenAI Inference services
- **`azure_ai_search`**: Azure Cognitive Search services
- **`azure_document_intelligence`**: Azure Document Intelligence services
- **`azure_storage`**: General Azure Storage services
- **`openai`**: OpenAI API services
- **`custom`**: Custom service implementations

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

| Step ID | Step Name | Category | Description | Documentation |
|---------|-----------|----------|-------------|---------------|
| `sample_step` | Sample Development Step | Development | A development and testing step that processes documents with configurable key-value pairs | [sample.py](./sample.py) |
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


## Step Input/Output Data Model

The document processing pipeline uses a standardized data model for passing information between steps. Understanding this model is crucial for developing effective steps.

### StepInputOutput Structure

Each step receives and returns a `StepInputOutput` object with the following structure:

```python
from pydantic import BaseModel
from typing import Dict, Any, Optional

class StepInputOutput(BaseModel):
    id: Optional[str] = None
    summary_data: Dict[str, Any] = {}
    data: Dict[str, Any] = {}
```

#### Key Fields Explanation

- **`id`**: Optional identifier for tracking the data through the pipeline
- **`summary_data`**: High-level metadata about the processing (e.g., counts, status, timing)
- **`data`**: The main payload containing document content and processing results

### Common Data Structure Patterns

#### Document Structure
```python
# Typical document structure in step_input.data
{
    "documents": [
        {
            "file_path": "/path/to/document.pdf",
            "file_name": "document.pdf",
            "file_size": 1048576,
            "content_type": "application/pdf",
            "document_type": {
                "primary_type": "pdf",
                "mime_type": "application/pdf",
                "confidence": 0.95
            },
            "chunks": [
                {
                    "chunk_id": "doc1_chunk1",
                    "chunk_type": "page",
                    "page_num": 1,
                    "text": "Raw text content...",
                    "markdown_text": "# Formatted content...",
                    "metadata": {
                        "extraction_method": "ai_ocr",
                        "confidence": 0.92
                    }
                }
            ]
        }
    ]
}
```

#### Summary Data Examples
```python
# Typical summary_data structure
{
    "pipeline_start_time": "2024-01-15T10:30:00Z",
    "documents_processed": 5,
    "total_pages": 23,
    "step_execution_times": {
        "document_type_identifier": 1.2,
        "pdf_text_extractor": 45.8
    },
    "errors": []
}
```

### Accessing Data in Steps

```python
async def run(self, step_input: StepInputOutput, 
              context: "PipelineExecutionContext", 
              **kwargs) -> StepInputOutput:
    
    # Access documents
    documents = step_input.data.get("documents", [])
    
    # Process each document
    for document in documents:
        file_path = document.get("file_path")
        chunks = document.get("chunks", [])
        
        # Process chunks
        for chunk in chunks:
            text = chunk.get("text", "")
            # Process text...
            chunk["processed_text"] = processed_result
    
    # Update summary data
    step_input.summary_data[f"{self.name}_processed"] = len(documents)
    
    return step_input
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

### Service Types

The system supports various service types:

#### Azure Blob Storage
```yaml
services:
  - name: primary_storage
    service_catalog_id: azure_storage_01
    settings:
      account_name: ${AZURE_STORAGE_ACCOUNT_NAME}
      credential_type: "account_key"
      credential_key: ${AZURE_STORAGE_ACCOUNT_KEY}
```

#### Azure AI Inference
```yaml
services:
  - name: ai_service
    service_catalog_id: azure_ai_inference_service_01
    settings:
      endpoint: ${AZURE_AI_ENDPOINT}
      credential_type: "api_key"
      api_key: ${AZURE_AI_API_KEY}
```

#### Azure AI Search
```yaml
services:
  - name: search_service
    service_catalog_id: azure_ai_search_01
    settings:
      endpoint: ${AZURE_SEARCH_ENDPOINT}
      credential_type: "api_key"
      api_key: ${AZURE_SEARCH_API_KEY}
```

### Using Services in Steps

#### Service Selection in Step Configuration
```yaml
steps:
  - name: pdf_extractor
    step_catalog_id: ai_pdf_text_extractor
    services: [ai_service, primary_storage]  # Reference services by name
    settings:
      ai_model_inference_service: "ai_service"
```

#### Accessing Services in Step Code
```python
async def run(self, step_input: StepInputOutput, 
              context: "PipelineExecutionContext", 
              **kwargs) -> StepInputOutput:
    
    # Get service instance
    ai_service = context.get_service_instance("ai_service")
    storage_service = context.get_service_instance("primary_storage")
    
    # Use services
    if ai_service:
        response = await ai_service.make_request(prompt_data)
    
    if storage_service:
        await storage_service.upload_blob(file_data)
    
    return step_input
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
async def run(self, step_input: StepInputOutput, 
              context: "PipelineExecutionContext", 
              **kwargs) -> StepInputOutput:
    
    if self.debug_mode:
        context.logger.debug(f"Step {self.name} input: {step_input}")
    
    # Your step logic here
    
    if self.debug_mode:
        context.logger.debug(f"Step {self.name} output: {result}")
    
    return result
```

#### Use Pipeline Debug Configuration
```yaml
pipeline:
  debug_mode: true
  log_level: "DEBUG"
  
steps:
  - name: my_step
    debug_mode: true  # Enable debug for specific steps
```

#### Inspect Step Input/Output
Add temporary logging to understand data flow:

```python
async def run(self, step_input: StepInputOutput, context, **kwargs):
    # Log input structure
    context.logger.info(f"Input keys: {list(step_input.data.keys())}")
    context.logger.info(f"Documents count: {len(step_input.data.get('documents', []))}")
    
    # Your processing logic
    result = self.process_data(step_input)
    
    # Log output structure  
    context.logger.info(f"Output keys: {list(result.data.keys())}")
    
    return result
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

### Testing Steps

#### Unit Testing Template
```python
import pytest
from unittest.mock import Mock, AsyncMock
from doc.proc.step.my_custom_step import MyCustomStep
from doc.proc.step.step_config import StepInstanceConfig

@pytest.mark.asyncio
async def test_my_custom_step():
    # Setup
    config = StepInstanceConfig(
        name="test_step",
        step_catalog_id="my_custom_step",
        settings={"param1": "value1"}
    )
    step = MyCustomStep(instance_config=config)
    
    # Mock context
    context = Mock()
    context.logger = Mock()
    context.get_service_instance = Mock(return_value=None)
    
    # Test data
    step_input = StepInputOutput(
        data={"documents": [{"file_path": "/test/file.pdf"}]}
    )
    
    # Execute
    result = await step.run(step_input, context)
    
    # Assert
    assert result is not None
    assert "documents" in result.data
```

#### Integration Testing
```python
# Test with real pipeline context
async def test_step_integration():
    from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
    
    # Create real context with services
    context = PipelineExecutionContext(
        pipeline_config=test_config,
        services=test_services
    )
    
    # Test step with real context
    result = await step.run(test_input, context)
    
    # Verify results
    assert result.data["processed"] == True
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
