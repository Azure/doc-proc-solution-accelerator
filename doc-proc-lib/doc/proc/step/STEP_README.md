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
| PDF Text Extractor | Extracts text and metadata from PDF documents using AI-powered OCR and image analysis | [pdf_text_extractor](./pdf_text_extractor.md) |
| Document Type Identifier | Automatically identifies and categorizes document types using magic bytes detection and file extension analysis | [document_type_identifier](./document_type_identifier.md) |
| Custom AI Prompt | Applies custom AI prompts to document content for specialized analysis, transformation, and enhancement | [custom_ai_prompt](./custom_ai_prompt.md) |
| AI Search Index Writer | Writes processed document data to Azure AI Search indexes with configurable field mappings | [ai_search_index_writer](./ai_search_index_writer.md) |
| PowerPoint Text Extractor | Extracts text content, tables, and images from Microsoft PowerPoint presentations (.pptx format) | [pptx_text_extractor](./pptx_text_extractor.md) |
| Word Text Extractor | Extracts text content, tables, and images from Microsoft Word documents (.docx format) | [word_text_extractor](./word_text_extractor.md) |


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
