# Service Documentation - Doc-Proc-Lib

A comprehensive guide to understanding, creating, configuring, and using services in the Doc-Proc-Lib document processing pipeline library.

## Table of Contents

- [Overview](#overview)
- [Service Architecture](#service-architecture)
- [Service Configuration](#service-configuration)
- [Built-in Services](#built-in-services)
- [Creating Custom Services](#creating-custom-services)
- [Service Integration](#service-integration)
- [Configuration Management](#configuration-management)
- [Security and Credentials](#security-and-credentials)
- [Testing and Debugging](#testing-and-debugging)
- [Best Practices](#best-practices)
- [Advanced Topics](#advanced-topics)
- [Troubleshooting](#troubleshooting)

## Overview

Services in Doc-Proc-Lib are external integrations that provide specific functionality to processing pipelines. They act as connectors to cloud services, databases, APIs, and other external systems. Services are:

- **Reusable**: Define once in the catalog, instantiate multiple times
- **Configurable**: Schema-driven configuration with validation
- **Secure**: Built-in credential management and sensitive data handling
- **Testable**: Connection testing and health checks
- **Extensible**: Easy to create custom services for new integrations

### Key Concepts

```
Service Catalog (Template)    →    Service Instance (Runtime)
         ↓                                   ↓
- Configuration Schema        →    - Actual Configuration
- Module/Class Definition     →    - Instantiated Service Object
- Validation Rules            →    - Runtime Validation
- UI Metadata                 →    - Pipeline Integration
```

## Service Architecture

### Core Components

1. **ServiceBase**: Abstract base class for all services
2. **ServiceConfig**: Configuration model for service definitions
3. **ServiceManager**: Factory for creating service instances
4. **PipelineExecutionContext**: Runtime context for accessing services

### Service Lifecycle

```
1. Catalog Definition → 2. Configuration Loading → 3. Instance Creation → 4. Pipeline Integration → 5. Runtime Execution
```

### Class Hierarchy

```python
ServiceBase (Abstract)
├── BlobService (Azure Blob Storage)
├── AzureAIInferenceService (Azure AI)
├── CosmosDBService (Azure Cosmos DB)
├── SearchService (Azure AI Search)
└── CustomService (User-defined)
```

## Service Configuration

### Service Catalog Structure

Services are defined in `service_catalog.yaml` with the following structure:

```yaml
services_catalog:
  - id: unique_service_id                    # Unique identifier
    name: "Human Readable Name"              # Display name
    description: "Service description"       # Purpose description
    type: service_type                       # Service category
    module_name: service_module              # Python module name
    module_path: ./path/to/service.py        # Module file path
    class_name: ServiceClassName             # Service class name
    test_connection: true                    # Enable connection testing
    category: "Service Category"             # Logical grouping
    version: "1.0"                           # Service version
    tags: [tag1, tag2, tag3]                 # Search/filter tags
    
    # Configuration schema for validation
    settings_schema:
      setting_name:
        type: string                         # Data type
        title: "Setting Title"               # Display title
        description: "Setting description"   # Help text
        required: true                       # Required field
        sensitive: false                     # Sensitive data flag
        env_var: "ENV_VAR_NAME"              # Environment variable
        default: ${ENV_VAR_NAME}             # Default value
        pattern: "^regex_pattern$"           # Validation pattern
        enum: ["option1", "option2"]         # Allowed values
        min: 0                               # Minimum value (numbers)
        max: 100                             # Maximum value (numbers)
    
    # UI metadata for frontend display
    ui_metadata:
      icon: "service-icon"                   # Icon identifier
      color: "#HEX_COLOR"                    # Theme color
      description_short: "Brief description"
      description_long: "Detailed description"
```

### Configuration Schema Types

The `settings_schema` supports various data types and validation rules:

#### String Settings
```yaml
string_setting:
  type: string
  title: "String Setting"
  description: "A text configuration value"
  required: true
  pattern: "^[a-zA-Z0-9_-]+$"              # Regex validation
  env_var: "STRING_SETTING_ENV"
  default: ${STRING_SETTING_ENV}
```

#### Integer Settings
```yaml
integer_setting:
  type: integer
  title: "Integer Setting"
  description: "A numeric configuration value"
  required: false
  default: 10
  minimum: 0                               # Minimum value
  maximum: 1000                            # Maximum value
  multipleOf: 5                            # Must be multiple of value
```

#### Boolean Settings
```yaml
boolean_setting:
  type: boolean
  title: "Boolean Setting"
  description: "A true/false configuration value"
  required: false
  default: false
```

#### Enum Settings
```yaml
enum_setting:
  type: string
  title: "Enum Setting"
  description: "A setting with predefined options"
  required: true
  enum: ["option1", "option2", "option3"]
  default: "option1"
```

#### Sensitive Settings
```yaml
sensitive_setting:
  type: string
  title: "API Key"
  description: "Sensitive authentication key"
  required: true
  sensitive: true                          # Mark as sensitive
  env_var: "API_KEY_ENV"
  default: ${API_KEY_ENV}
```

## Built-in Services

### Azure Blob Storage Service

**Purpose**: Document storage and retrieval from Azure Blob Storage.

**Configuration Example**:
```yaml
- id: azure_storage_01
  name: "Azure Blob Storage - Primary"
  type: azure_blob
  module_name: blob_service
  module_path: ./doc/proc/service/blob_service.py
  class_name: BlobService
  test_connection: true
  
  settings_schema:
    account_name:
      type: string
      title: "Storage Account Name"
      required: true
      env_var: "AZURE_STORAGE_ACCOUNT_NAME"
      default: ${AZURE_STORAGE_ACCOUNT_NAME}
    
    credential_type:
      type: string
      title: "Credential Type"
      enum: ["azure_key_credential", "default_azure_credential"]
      default: "azure_key_credential"
      env_var: "AZURE_STORAGE_CREDENTIAL_TYPE"
      default: ${AZURE_STORAGE_CREDENTIAL_TYPE}
    
    credential_key:
      type: string
      title: "Account Key"
      required: false
      sensitive: true
      env_var: "AZURE_STORAGE_ACCOUNT_KEY"
      default: ${AZURE_STORAGE_ACCOUNT_KEY}
```

**Usage in Pipeline**:
```python
# In a step's run method
storage_service = context.get_service("primary_blob_storage")
async with storage_service:
    # Upload file
    blob_url = await storage_service.upload_file(
        container_name="documents",
        filename="document.pdf",
        file_content=file_data
    )
    
    # Get container client for more operations
    container_client = await storage_service.get_container_client("documents")
```

### Azure AI Inference Service

**Purpose**: AI-powered document processing using Azure AI services.

**Configuration Example**:
```yaml
- id: azure_ai_inference_service_01
  name: "Azure AI Inference Service"
  type: azure_ai_inference
  module_name: azure_ai_inference_service
  module_path: ./doc/proc/service/azure_ai_inference_service.py
  class_name: AzureAIInferenceService
  test_connection: true
  
  settings_schema:
    endpoint:
      type: string
      title: "Service Endpoint"
      required: true
      pattern: "^https://.*"
      env_var: "AZURE_AI_ENDPOINT"
      default: ${AZURE_AI_ENDPOINT}
    
    credential_type:
      type: string
      title: "Credential Type"
      enum: ["azure_key_credential", "default_azure_credential"]
      default: "azure_key_credential"
    
    api_key:
      type: string
      title: "API Key"
      required: false
      sensitive: true
      env_var: "AZURE_AI_API_KEY"
      default: ${AZURE_AI_API_KEY}
    
    model_name:
      type: string
      title: "Model Name"
      enum: ["gpt-4o", "gpt-4", "gpt-35-turbo"]
      default: "gpt-4o"
    
    max_tokens:
      type: integer
      title: "Max Tokens"
      default: 4000
      minimum: 100
      maximum: 8000
```

**Usage in Pipeline**:
```python
# In a step's run method
ai_service = context.get_service("ai_inference_service")

# Prepare messages
messages = [
    SystemMessage("You are a document analyzer"),
    UserMessage("Analyze this document content...")
]

# Run completion
response = ai_service.run_chat_completion(
    messages=messages,
    max_completion_tokens=4000,
    temperature=0.7,
    top_p=0.9,
    frequency_penalty=0.0,
    presence_penalty=0.0
)

# Extract result
analysis_result = response.choices[0].message.content
```

### Azure Cosmos DB Service

**Purpose**: NoSQL database for storing document metadata and processing results.

**Configuration Example**:
```yaml
- id: azure_cosmos_db_01
  name: "Azure Cosmos DB"
  type: azure_cosmos
  module_name: cosmos_service
  module_path: ./doc/proc/service/cosmos_service.py
  class_name: CosmosService
  test_connection: true
  
  settings_schema:
    endpoint:
      type: string
      title: "Cosmos DB Endpoint"
      required: true
      pattern: "^https://.*"
      env_var: "AZURE_COSMOS_ENDPOINT"
      default: ${AZURE_COSMOS_ENDPOINT}
    
    key:
      type: string
      title: "Primary Key"
      required: true
      sensitive: true
      env_var: "AZURE_COSMOS_KEY"
      default: ${AZURE_COSMOS_KEY}
    
    database_name:
      type: string
      title: "Database Name"
      required: true
      default: "document-processing"
    
    container_name:
      type: string
      title: "Container Name"
      required: true
      default: "documents"
```

### Azure AI Search Service

**Purpose**: Full-text and semantic search capabilities for processed documents.

**Configuration Example**:
```yaml
- id: azure_ai_search_service_01
  name: "Azure AI Search Service"
  type: azure_search
  module_name: search_service
  module_path: ./doc/proc/service/search_service.py
  class_name: SearchService
  test_connection: true
  
  settings_schema:
    service_name:
      type: string
      title: "Search Service Name"
      required: true
      env_var: "AZURE_SEARCH_SERVICE_NAME"
      default: ${AZURE_SEARCH_SERVICE_NAME}
    
    index_name:
      type: string
      title: "Index Name"
      required: true
      default: "documents-index"
    
    api_key:
      type: string
      title: "Admin API Key"
      required: true
      sensitive: true
      env_var: "AZURE_SEARCH_API_KEY"
      default: ${AZURE_SEARCH_API_KEY}
    
    api_version:
      type: string
      title: "API Version"
      enum: ["2023-11-01", "2023-07-01-Preview"]
      default: "2023-11-01"
```

## Creating Custom Services

### Step 1: Create Service Class

Create a new Python file in `doc/proc/service/` directory:

```python
# doc/proc/service/my_custom_service.py
import logging
from typing import Dict, Any, Optional
from doc.proc.service.service_base import ServiceBase, ServiceExecutionError

logger = logging.getLogger(__name__)


class MyCustomService(ServiceBase):
    """Custom service for specific integration needs."""
    
    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        """Initialize the custom service with configuration."""
        super().__init__(name=name, type=type, settings=settings, **kwargs)
        
        # Extract and validate settings
        self.api_endpoint = self._get_required_setting('api_endpoint')
        self.api_key = self._get_required_setting('api_key')
        self.timeout = settings.get('timeout', 30)
        self.retry_count = settings.get('retry_count', 3)
        self.enable_logging = settings.get('enable_logging', True)
        
        # Initialize client or connection
        self._client = None
        self._initialize_client()
    
    def _get_required_setting(self, key: str) -> str:
        """Get a required setting with environment variable support."""
        value = self.settings.get(key)
        if not value:
            raise ValueError(f"Settings key '{key}' is required")
        
        # Handle environment variable substitution
        if value.startswith('${') and value.endswith('}'):
            import os
            env_var_name = value[2:-1]
            env_value = os.getenv(env_var_name)
            if not env_value:
                raise ValueError(f"Environment variable '{env_var_name}' is not set")
            return env_value
        
        return value
    
    def _initialize_client(self):
        """Initialize the service client."""
        try:
            # Initialize your service client here
            # self._client = SomeServiceClient(
            #     endpoint=self.api_endpoint,
            #     api_key=self.api_key,
            #     timeout=self.timeout
            # )
            logger.debug(f"Initialized {self.name} service client")
        except Exception as e:
            logger.error(f"Failed to initialize {self.name} service client: {e}")
            raise ServiceExecutionError(f"Service initialization failed: {e}")
    
    async def test_connection(self) -> bool:
        """Test the service connection."""
        try:
            # Implement connection test logic
            # For example, make a simple API call
            # response = await self._client.health_check()
            # return response.status == 'ok'
            
            logger.info(f"Connection test passed for {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed for {self.name}: {e}")
            raise ServiceExecutionError(f"Connection test failed: {e}")
    
    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data using the service."""
        try:
            # Implement your service logic here
            processed_data = {
                "original_data": data,
                "processed_by": self.name,
                "processing_result": "success"
            }
            
            if self.enable_logging:
                logger.info(f"Data processed successfully by {self.name}")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Data processing failed in {self.name}: {e}")
            raise ServiceExecutionError(f"Data processing failed: {e}")
    
    async def custom_operation(self, operation_data: Dict[str, Any]) -> Any:
        """Custom operation specific to this service."""
        try:
            # Implement custom operations
            result = f"Custom operation executed with data: {operation_data}"
            return result
            
        except Exception as e:
            logger.error(f"Custom operation failed in {self.name}: {e}")
            raise ServiceExecutionError(f"Custom operation failed: {e}")
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        if self._client:
            # Close connections, cleanup resources
            # self._client.close()
            logger.debug(f"Cleaned up {self.name} service resources")
```

### Step 2: Add to Service Catalog

Add your service definition to `service_catalog.yaml`:

```yaml
services_catalog:
  - id: my_custom_service_01
    name: "My Custom Service"
    description: "Custom service for specific integration needs"
    type: custom_service
    module_name: my_custom_service
    module_path: ./doc/proc/service/my_custom_service.py
    class_name: MyCustomService
    test_connection: true
    category: "Custom Integrations"
    version: "1.0"
    tags: [custom, integration, api]
    
    settings_schema:
      api_endpoint:
        type: string
        title: "API Endpoint"
        description: "The API endpoint URL for the service"
        required: true
        pattern: "^https://.*"
        env_var: "MY_CUSTOM_SERVICE_ENDPOINT"
        default: ${MY_CUSTOM_SERVICE_ENDPOINT}
      
      api_key:
        type: string
        title: "API Key"
        description: "Authentication key for the service"
        required: true
        sensitive: true
        env_var: "MY_CUSTOM_SERVICE_API_KEY"
        default: ${MY_CUSTOM_SERVICE_API_KEY}
      
      timeout:
        type: integer
        title: "Request Timeout"
        description: "Request timeout in seconds"
        required: false
        default: 30
        minimum: 5
        maximum: 300
      
      retry_count:
        type: integer
        title: "Retry Count"
        description: "Number of retries for failed requests"
        required: false
        default: 3
        minimum: 0
        maximum: 10
      
      enable_logging:
        type: boolean
        title: "Enable Logging"
        description: "Enable detailed logging for this service"
        required: false
        default: true
    
    ui_metadata:
      icon: "custom"
      color: "#FF5722"
      description_short: "Custom service for specific integrations"
      description_long: "A custom service implementation that can be adapted for various API integrations and custom processing needs."
```

### Step 3: Configure Service Instance

Add the service instance to your `pipeline_config.yaml`:

```yaml
service_instances:
  - name: my_custom_service_instance
    service_catalog_id: my_custom_service_01
    settings:
      api_endpoint: ${MY_CUSTOM_SERVICE_ENDPOINT}
      api_key: ${MY_CUSTOM_SERVICE_API_KEY}
      timeout: 60
      retry_count: 5
      enable_logging: true
```

### Step 4: Use in Pipeline Steps

Access and use the service in your pipeline steps:

```python
# In a step's run method
async def run(self, input_data: StepInputOutput, context, **kwargs) -> StepInputOutput:
    # Get the custom service
    custom_service = context.get_service("my_custom_service_instance")
    
    if not custom_service:
        raise StepExecutionError("Custom service not found in context")
    
    # Use the service
    try:
        # Process data using the service
        processed_data = await custom_service.process_data(input_data.data)
        
        # Perform custom operations
        custom_result = await custom_service.custom_operation({
            "operation": "analyze",
            "input": input_data.data
        })
        
        # Update step output
        return StepInputOutput(
            summary_data={
                **input_data.summary_data,
                "custom_service_used": custom_service.name,
                "processing_timestamp": datetime.now().isoformat()
            },
            data={
                **input_data.data,
                "processed_data": processed_data,
                "custom_result": custom_result
            }
        )
        
    except ServiceExecutionError as e:
        logger.error(f"Service execution failed: {e}")
        raise StepExecutionError(f"Custom service failed: {e}")
```

## Service Integration

### Pipeline Integration

Services are integrated into pipelines through the following mechanism:

1. **Service Catalog Definition**: Services are defined in the catalog with their schema
2. **Service Instance Configuration**: Instances are configured in pipeline config
3. **Runtime Service Creation**: Service manager creates instances during pipeline initialization
4. **Context Injection**: Services are injected into step execution context
5. **Step Access**: Steps access services through the context

### Service Access Pattern

```python
# Standard service access pattern in steps
class MyProcessingStep(StepBase):
    async def run(self, input_data: StepInputOutput, context, **kwargs) -> StepInputOutput:
        # 1. Get required services
        storage_service = context.get_service("storage_service_instance")
        ai_service = context.get_service("ai_service_instance")
        
        # 2. Validate service availability
        if not storage_service:
            raise StepExecutionError("Storage service not available")
        
        # 3. Use services with proper error handling
        try:
            # Download document
            document_data = await storage_service.download_file("document.pdf")
            
            # Process with AI
            analysis_result = await ai_service.analyze_document(document_data)
            
            # Return results
            return StepInputOutput(
                summary_data={**input_data.summary_data, "analysis_completed": True},
                data={**input_data.data, "analysis_result": analysis_result}
            )
            
        except ServiceExecutionError as e:
            logger.error(f"Service operation failed: {e}")
            raise StepExecutionError(f"Step failed due to service error: {e}")
```

### Service Dependencies

Steps can declare service dependencies for validation and documentation:

```yaml
# In step_catalog.yaml
steps:
  - name: document_analysis_step
    # ... other configuration
    services_required:
      - type: azure_blob
        purpose: "Document storage and retrieval"
      - type: azure_ai_inference
        purpose: "Document analysis and processing"
    
    # Service validation in step configuration
    settings_schema:
      storage_service:
        type: string
        title: "Storage Service"
        description: "Reference to storage service instance"
        required: true
        ui_component: "service_selector"
        service_type: "azure_blob"
      
      ai_service:
        type: string
        title: "AI Service"
        description: "Reference to AI service instance"
        required: true
        ui_component: "service_selector"
        service_type: "azure_ai_inference"
```

## Configuration Management

### Environment Variable Integration

Services support automatic environment variable substitution:

```yaml
# Service configuration with environment variables
settings_schema:
  api_key:
    type: string
    env_var: "MY_SERVICE_API_KEY"
    default: ${MY_SERVICE_API_KEY}    # Automatically substituted
```

**Environment File (`.env`)**:
```bash
# Service configuration
MY_SERVICE_API_KEY=your_actual_api_key_here
MY_SERVICE_ENDPOINT=https://api.example.com
MY_SERVICE_TIMEOUT=60
```

### Configuration Validation

Services validate configuration at initialization:

```python
class MyService(ServiceBase):
    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        super().__init__(name, type, settings, **kwargs)
        
        # Validate required settings
        self._validate_required_settings([
            'api_key', 'endpoint', 'timeout'
        ])
        
        # Validate data types
        self._validate_setting_types({
            'timeout': int,
            'retry_count': int,
            'enable_ssl': bool
        })
    
    def _validate_required_settings(self, required_keys: List[str]):
        """Validate that all required settings are present."""
        for key in required_keys:
            if key not in self.settings or not self.settings[key]:
                raise ValueError(f"Required setting '{key}' is missing or empty")
    
    def _validate_setting_types(self, type_mapping: Dict[str, type]):
        """Validate setting data types."""
        for key, expected_type in type_mapping.items():
            if key in self.settings:
                value = self.settings[key]
                if not isinstance(value, expected_type):
                    raise TypeError(f"Setting '{key}' must be of type {expected_type.__name__}")
```

### Configuration Overrides

Pipeline instances can override catalog defaults:

```yaml
# Pipeline configuration with overrides
service_instances:
  - name: custom_ai_service
    service_catalog_id: azure_ai_inference_service_01
    settings:
      # Override catalog defaults
      model_name: "gpt-4o"           # Override default model
      max_tokens: 8000               # Override default token limit
      temperature: 0.3               # Override default temperature
      # Custom instance-specific settings
      custom_prompt_prefix: "Analyze the following document:"
      enable_detailed_logging: true
```

## Security and Credentials

### Credential Management

Services support multiple credential types:

1. **Azure Key Credential**: Direct API key authentication
2. **Default Azure Credential**: Managed identity/service principal
3. **Connection String**: Database connection strings
4. **Certificate**: Certificate-based authentication

### Sensitive Data Handling

Mark sensitive configuration as `sensitive: true`:

```yaml
settings_schema:
  api_key:
    type: string
    title: "API Key"
    sensitive: true              # Marks as sensitive
    env_var: "API_KEY"
    default: ${API_KEY}
  
  connection_string:
    type: string
    title: "Database Connection String"
    sensitive: true
    env_var: "DB_CONNECTION_STRING"
    default: ${DB_CONNECTION_STRING}
```

### Security Best Practices

1. **Never hardcode credentials** in configuration files
2. **Use environment variables** for all sensitive data
3. **Enable connection testing** to validate credentials
4. **Implement proper error handling** to avoid credential leakage
5. **Use managed identities** when running on Azure
6. **Rotate credentials regularly** and update environment variables

### Example: Secure Azure Service Configuration

```python
class SecureAzureService(ServiceBase):
    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        super().__init__(name, type, settings, **kwargs)
        
        # Secure credential handling
        self.credential_type = self._get_env_setting('credential_type')
        
        if self.credential_type == 'azure_key_credential':
            self.api_key = self._get_env_setting('api_key', sensitive=True)
            self.credential = AzureKeyCredential(self.api_key)
        elif self.credential_type == 'default_azure_credential':
            self.credential = DefaultAzureCredential()
        else:
            raise ValueError(f"Unsupported credential type: {self.credential_type}")
    
    def _get_env_setting(self, key: str, sensitive: bool = False) -> str:
        """Securely get setting from environment variables."""
        value = self.settings.get(key)
        if not value:
            raise ValueError(f"Setting '{key}' is required")
        
        if value.startswith('${') and value.endswith('}'):
            import os
            env_var = value[2:-1]
            env_value = os.getenv(env_var)
            if not env_value:
                raise ValueError(f"Environment variable '{env_var}' not set")
            
            if sensitive:
                # Log that sensitive data was loaded without exposing it
                logger.debug(f"Loaded sensitive setting '{key}' from environment")
            
            return env_value
        
        return value
```

## Testing and Debugging

### Connection Testing

All services should implement connection testing:

```python
async def test_connection(self) -> bool:
    """Test service connection with comprehensive checks."""
    try:
        # Test 1: Basic connectivity
        response = await self._client.ping()
        if not response.success:
            return False
        
        # Test 2: Authentication
        auth_response = await self._client.authenticate()
        if not auth_response.authenticated:
            return False
        
        # Test 3: Basic operation
        test_response = await self._client.get_info()
        if not test_response.accessible:
            return False
        
        logger.info(f"Connection test passed for {self.name}")
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed for {self.name}: {e}")
        return False
```

### Debug Logging

Enable comprehensive debug logging:

```python
class DebuggableService(ServiceBase):
    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        super().__init__(name, type, settings, **kwargs)
        
        # Enable debug logging if requested
        self.debug_enabled = settings.get('debug_logging', False)
        
        if self.debug_enabled:
            self.logger = logging.getLogger(f"{__name__}.{self.name}")
            self.logger.setLevel(logging.DEBUG)
    
    def _debug_log(self, message: str, data: Any = None):
        """Debug logging with optional data."""
        if self.debug_enabled:
            if data:
                self.logger.debug(f"{message}: {data}")
            else:
                self.logger.debug(message)
    
    async def process_with_debug(self, input_data: Any) -> Any:
        """Process data with debug logging."""
        self._debug_log("Starting data processing", {"input_size": len(str(input_data))})
        
        try:
            # Process data
            result = await self._process_data(input_data)
            
            self._debug_log("Data processing completed", {"output_size": len(str(result))})
            return result
            
        except Exception as e:
            self._debug_log("Data processing failed", {"error": str(e)})
            raise
```


## Best Practices

### Service Design Principles

1. **Single Responsibility**: Each service should handle one type of integration
2. **Fail Fast**: Validate configuration early and provide clear error messages
3. **Async First**: Design services to be async-compatible for better performance
4. **Resource Management**: Properly manage connections and resources
5. **Error Handling**: Implement comprehensive error handling and logging

### Configuration Best Practices

1. **Use Environment Variables**: Store all sensitive data in environment variables
2. **Provide Defaults**: Set sensible defaults for optional configuration
3. **Validate Early**: Validate configuration during service initialization
4. **Document Schema**: Provide clear titles and descriptions for all settings
5. **Version Control**: Version your service definitions for compatibility

### Performance Optimization

1. **Connection Pooling**: Reuse connections when possible
2. **Async Operations**: Use async/await for I/O operations
3. **Caching**: Cache expensive operations and data
4. **Batch Processing**: Support batch operations when available
5. **Timeouts**: Set appropriate timeouts for all operations

### Error Handling

```python
class RobustService(ServiceBase):
    async def robust_operation(self, data: Any) -> Any:
        """Operation with comprehensive error handling."""
        retry_count = 0
        max_retries = self.settings.get('max_retries', 3)
        
        while retry_count <= max_retries:
            try:
                # Attempt operation
                result = await self._perform_operation(data)
                return result
                
            except ConnectionError as e:
                # Retryable error
                retry_count += 1
                if retry_count > max_retries:
                    raise ServiceExecutionError(f"Connection failed after {max_retries} retries: {e}")
                
                # Wait before retry
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                
            except ValueError as e:
                # Non-retryable error
                raise ServiceExecutionError(f"Invalid data provided: {e}")
                
            except Exception as e:
                # Unexpected error
                logger.error(f"Unexpected error in {self.name}: {e}")
                raise ServiceExecutionError(f"Unexpected error: {e}")
```

## Advanced Topics

### Service Composition

Create composite services that use multiple underlying services:

```python
class CompositeDocumentService(ServiceBase):
    """Service that combines storage, AI, and database operations."""
    
    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        super().__init__(name, type, settings, **kwargs)
        
        # Initialize component services
        self.storage_service = None
        self.ai_service = None
        self.database_service = None
    
    async def initialize_components(self, context):
        """Initialize component services from context."""
        self.storage_service = context.get_service(
            self.settings.get('storage_service_name')
        )
        self.ai_service = context.get_service(
            self.settings.get('ai_service_name')
        )
        self.database_service = context.get_service(
            self.settings.get('database_service_name')
        )
    
    async def process_document_end_to_end(self, document_id: str) -> Dict[str, Any]:
        """Complete document processing workflow."""
        try:
            # 1. Retrieve document from storage
            document_data = await self.storage_service.download_file(document_id)
            
            # 2. Process with AI
            analysis_result = await self.ai_service.analyze_document(document_data)
            
            # 3. Store results in database
            await self.database_service.store_analysis(document_id, analysis_result)
            
            # 4. Return processing summary
            return {
                "document_id": document_id,
                "processing_status": "completed",
                "analysis_summary": analysis_result.get("summary"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"End-to-end processing failed for {document_id}: {e}")
            raise ServiceExecutionError(f"Document processing failed: {e}")
```


### Service Middleware

Implement middleware for cross-cutting concerns:

```python
class ServiceMiddleware:
    """Middleware for services with logging, metrics, and error handling."""
    
    def __init__(self, service: ServiceBase):
        self.service = service
        self.call_count = 0
        self.error_count = 0
    
    async def __call__(self, method_name: str, *args, **kwargs):
        """Execute service method with middleware."""
        start_time = time.time()
        self.call_count += 1
        
        try:
            # Log method call
            logger.debug(f"Calling {self.service.name}.{method_name}")
            
            # Execute method
            method = getattr(self.service, method_name)
            result = await method(*args, **kwargs)
            
            # Log success
            elapsed = time.time() - start_time
            logger.debug(f"{self.service.name}.{method_name} completed in {elapsed:.2f}s")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            elapsed = time.time() - start_time
            
            logger.error(
                f"{self.service.name}.{method_name} failed after {elapsed:.2f}s: {e}"
            )
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            "service_name": self.service.name,
            "total_calls": self.call_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.call_count if self.call_count > 0 else 0
        }
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Service Configuration Errors

**Problem**: Service fails to initialize with configuration errors.

**Solutions**:
```python
# Validate service configuration
try:
    service_config = ServiceConfig.from_file('service_catalog.yaml')
    print("Service catalog loaded successfully")
except Exception as e:
    print(f"Service catalog error: {e}")
```

#### 2. Connection Failures

**Problem**: Service cannot connect to external systems.

**Solutions**:
```python
# Test service connection independently
async def test_service_connection():
    service = MyService(name="test", type="test", settings=test_settings)
    try:
        result = await service.test_connection()
        print(f"Connection test: {'PASSED' if result else 'FAILED'}")
    except Exception as e:
        print(f"Connection error: {e}")

```

#### 3. Service Not Found in Context

**Problem**: Service is not available in pipeline execution context.

**Solutions**:
```python
# Debug service context
def debug_service_context(context):
    print("Available services in context:")
    if hasattr(context, 'services'):
        for service in context.services:
            print(f"  - {service.get('name', 'unnamed')}: {service.get('type', 'unknown')}")
    else:
        print("  No services found in context")

# Verify service instance configuration
def verify_service_instances(pipeline_config):
    print("Configured service instances:")
    for instance in pipeline_config.service_instances:
        print(f"  - {instance.name} (catalog_id: {instance.service_catalog_id})")
```

### Debug Utilities

Create debug utilities for service troubleshooting:

```python
# debug_services.py
import asyncio
import logging
from typing import List, Dict, Any
from doc.proc.service.service_config import ServiceConfig
from doc.proc.service.service_manager import get_service

logging.basicConfig(level=logging.DEBUG)

class ServiceDebugger:
    """Utility class for debugging services."""
    
    @staticmethod
    async def debug_service_catalog(catalog_file: str):
        """Debug service catalog loading."""
        try:
            services = ServiceConfig.from_file(catalog_file)
            print(f"Loaded {len(services)} services from catalog:")
            for service in services:
                print(f"  - {service.id}: {service.name} ({service.type})")
        except Exception as e:
            print(f"Error loading service catalog: {e}")
    
    @staticmethod
    async def test_all_services(catalog_file: str, settings_override: Dict[str, Any] = None):
        """Test all services in catalog."""
        services = ServiceConfig.from_file(catalog_file)
        results = {}
        
        for service_config in services:
            try:
                # Override settings if provided
                test_settings = settings_override.get(service_config.id, {})
                
                # Create service instance
                service = await get_service(service_config, test_settings)
                
                # Test connection
                connection_result = await service.test_connection()
                results[service_config.id] = {
                    "status": "success" if connection_result else "failed",
                    "connection_test": connection_result
                }
                
            except Exception as e:
                results[service_config.id] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Print results
        print("\nService Test Results:")
        for service_id, result in results.items():
            status = result["status"]
            print(f"  {service_id}: {status.upper()}")
            if status == "error":
                print(f"    Error: {result['error']}")
    
    @staticmethod
    def validate_environment_variables():
        """Validate required environment variables."""
        import os
        
        # Common Azure environment variables
        azure_vars = [
            'AZURE_STORAGE_ACCOUNT_NAME',
            'AZURE_STORAGE_ACCOUNT_KEY',
            'AZURE_AI_ENDPOINT',
            'AZURE_AI_API_KEY',
            'AZURE_COSMOS_ENDPOINT',
            'AZURE_COSMOS_KEY'
        ]
        
        print("Environment Variable Check:")
        for var in azure_vars:
            value = os.getenv(var)
            if value:
                # Hide sensitive values
                display_value = "***" if "KEY" in var or "SECRET" in var else value
                print(f"  ✓ {var}: {display_value}")
            else:
                print(f"  ✗ {var}: NOT SET")

# Usage
if __name__ == "__main__":
    debugger = ServiceDebugger()
    
    # Validate environment
    debugger.validate_environment_variables()
    
    # Test service catalog
    asyncio.run(debugger.debug_service_catalog("service_catalog.yaml"))
    
    # Test all services
    # asyncio.run(debugger.test_all_services("service_catalog.yaml"))
```

### Performance Monitoring

Monitor service performance:

```python
class ServiceMonitor:
    """Monitor service performance and health."""
    
    def __init__(self):
        self.metrics = {}
    
    async def monitor_service(self, service: ServiceBase, duration_seconds: int = 60):
        """Monitor service for specified duration."""
        start_time = time.time()
        call_count = 0
        error_count = 0
        
        while time.time() - start_time < duration_seconds:
            try:
                # Test service operation
                await service.test_connection()
                call_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(f"Service error during monitoring: {e}")
            
            # Wait before next check
            await asyncio.sleep(5)
        
        # Calculate metrics
        total_time = time.time() - start_time
        self.metrics[service.name] = {
            "total_calls": call_count,
            "error_count": error_count,
            "error_rate": error_count / call_count if call_count > 0 else 0,
            "calls_per_second": call_count / total_time,
            "uptime_percentage": ((call_count - error_count) / call_count * 100) if call_count > 0 else 0
        }
        
        return self.metrics[service.name]
```
