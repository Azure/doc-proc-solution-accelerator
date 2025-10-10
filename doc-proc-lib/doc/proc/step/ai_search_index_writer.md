# AI Search Index Writer Step Documentation

## Overview

The AI Search Index Writer step is a specialized component of the document processing pipeline that writes processed document data to Azure AI Search indexes. This step enables the creation of searchable document repositories by indexing structured document data including text content, metadata, and AI-generated summaries.

## Step Information

- **Step ID**: `ai_search_index_writer`
- **Step Name**: AI Search Index Writer
- **Category**: AI Processing
- **Version**: 1.0
- **Module**: `doc.proc.step.ai_search_index_writer`
- **Class**: `AISearchIndexWriterStep`

## Description

The AI Search Index Writer step processes document chunks and writes them to Azure AI Search indexes with configurable field mappings. It supports batch processing of multiple documents and provides detailed statistics on successful and failed indexing operations.

### Key Features

- **Flexible Field Mapping**: Configure custom mappings between document fields and search index fields
- **Batch Processing**: Process multiple documents efficiently in a single operation
- **Error Handling**: Robust error handling with detailed logging and optional fail-on-error behavior
- **Statistics Tracking**: Comprehensive statistics on processed documents
- **Service Integration**: Seamless integration with Azure AI Search services
- **Debug Mode**: Detailed logging for troubleshooting and development

## Use Cases

### 1. Document Search and Retrieval
Create searchable document repositories where users can quickly find relevant documents based on content, metadata, or AI-generated summaries.

**Example Scenario**: A legal firm processes contracts and writes them to a search index, enabling lawyers to quickly search for contracts by party names, dates, or specific clauses.

### 2. Knowledge Base Creation
Build comprehensive knowledge bases from processed documents with full-text search capabilities.

**Example Scenario**: A company processes technical documentation and creates a searchable knowledge base for customer support and internal teams.

### 3. Content Management Systems
Integrate with content management workflows to automatically index new documents as they are processed.

**Example Scenario**: An organization automatically indexes uploaded documents, making them immediately searchable through their internal portal.

### 4. Research and Analytics
Enable advanced search and analytics capabilities on large document collections.

**Example Scenario**: Researchers index academic papers and use the search functionality to find relevant studies and cross-reference findings.

### 5. Compliance and Audit
Index documents for compliance monitoring and audit trail purposes.

**Example Scenario**: Financial institutions index transaction records and regulatory documents for quick retrieval during audits.

## Prerequisites

### Required Services

1. **Azure AI Search Service**: A configured Azure AI Search service instance
2. **Azure Blob Storage Service**: A storage service for document access (optional, depending on use case)

### Input Data Requirements

The step expects input data in the following structure:

```json
{
  "chunks": [
    {
      "chunk_id": "unique_identifier",
      "input_file_path": "path/to/document.pdf",
      "page_num": 1,
      "markdown": "extracted_text_content",
      "markdown_text": "plain_text_content",
      "page_image_descriptions": "image_descriptions",
      "custom_ai_prompt_output": "ai_generated_content",
      "summary": "ai_generated_summary"
    }
  ]
}
```

## Configuration

### Required Settings

#### Azure AI Search Service
- **Parameter**: `ai_search_service`
- **Type**: String
- **Description**: Reference to the Azure AI Search service instance to use
- **Required**: Yes
- **UI Component**: Service Selector (azure_ai_search)

#### Chunks Field Name
- **Parameter**: `chunks_field_name`
- **Type**: String
- **Description**: Field in document that includes list of content chunks to be indexed
- **Required**: No
- **Default**: `chunks`
- **UI Component**: Input

#### Index Name
- **Parameter**: `index_name`
- **Type**: String
- **Description**: Name of the Azure AI Search index to write to
- **Required**: Yes
- **Default**: `pdf-index`
- **UI Component**: Input

#### Index Field Mappings
- **Parameter**: `index_field_mappings`
- **Type**: String (JSON)
- **Description**: Mappings of document data chunk fields to index fields. Document fields are mapped from the Document data dictionary.
- **Required**: Yes
- **UI Component**: Textarea

### Default Field Mappings

```json
{
  "page_id": "id",
  "input_file_path": "file_name",
  "page_num": "page_num",
  "markdown": "page_markdown",
  "markdown_text": "markdown_text",
  "page_text": "page_text",
  "text": "page_text",
  "page_image_descriptions": "image_descriptions",
  "custom_ai_prompt_output": "ai_result",
  "summary": "summary"
}
```

### Step Configuration Example

```yaml
steps:
  - name: write_to_search_index
    step_catalog_id: ai_search_index_writer
    services: [primary_ai_search_service]
    settings:
      ai_search_service: "primary_ai_search_service"
      chunks_field_name: "chunks"
      index_name: "documents_index"
      index_field_mappings: |
        {
          "chunk_id": "id",
          "input_file_path": "file_name",
          "page_num": "page_num",
          "markdown": "page_markdown",
          "markdown_text": "markdown_text",
          "page_image_descriptions": "image_descriptions",
          "custom_ai_prompt_output": "ai_result",
          "summary": "summary"
        }
```

## Field Mapping Configuration

### Understanding Field Mappings

Field mappings define how data from your document chunks is mapped to fields in the Azure AI Search index. The mapping is defined as a JSON object where:

- **Key**: Field name in the document chunk
- **Value**: Field name in the search index

### Common Field Mappings

| Document Chunk Field | Index Field | Description |
|---|---|---|
| `chunk_id` | `id` | Unique identifier for the document chunk |
| `input_file_path` | `file_name` | Original file path or name |
| `page_num` | `page_num` | Page number within the document |
| `markdown` | `page_markdown` | Extracted markdown content |
| `markdown_text` | `markdown_text` | Plain text content |
| `page_text` | `page_text` | Page text content |
| `text` | `page_text` | Combined text content |
| `page_image_descriptions` | `image_descriptions` | AI-generated image descriptions |
| `custom_ai_prompt_output` | `ai_result` | Custom AI prompt results |
| `summary` | `summary` | AI-generated summary |

### Custom Field Mappings

You can create custom mappings based on your specific document structure:

```json
{
  "custom_field_1": "index_field_1",
  "custom_field_2": "index_field_2",
  "author": "author",
  "created_date": "creation_date"
}
```

## Azure AI Search Service Configuration

### Service Settings

The step requires a configured Azure AI Search service with the following settings:

```yaml
services:
  - name: primary_ai_search_service
    service_catalog_id: azure_ai_search_service_01
    settings:
      account_name: "your-search-service-name"
      credential_type: "azure_key_credential"
      api_key: "your-search-service-api-key"
      api_version: "2024-07-01"
```

### Index Schema Requirements

Your Azure AI Search index must have fields that correspond to your field mappings. Example index schema:

```json
{
  "name": "documents-index",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true,
      "searchable": false
    },
    {
      "name": "file_name",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true
    },
    {
      "name": "page_num",
      "type": "Edm.Int32",
      "filterable": true,
      "sortable": true
    },
    {
      "name": "page_markdown",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "markdown_text",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "image_descriptions",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "summary",
      "type": "Edm.String",
      "searchable": true
    }
  ]
}
```

## Error Handling

### Error Types

1. **Configuration Errors**: Missing or invalid service configurations
2. **Data Validation Errors**: Invalid input data structure
3. **Service Connection Errors**: Issues connecting to Azure AI Search
4. **Indexing Errors**: Problems writing documents to the index

### Error Handling Options

#### Fail on Document Error
- **Setting**: `fail_step_on_document_error`
- **Default**: `false`
- **Description**: Whether to fail the entire step if a single document fails to process

#### Retry Configuration
- **Retry on Failure**: `true`
- **Retry Count**: `3`
- **Timeout**: `600` seconds

## Output Data

### Success Response

The step returns the original `Document` object with:

```json
{
  "chunks": [
    // Original chunks data passed through
  ]
}
```

### Processing Results

The indexing results are logged but not included in the output data structure. The step focuses on writing data to the search index rather than modifying the document structure.

### Processing Tracking

The step tracks processing through logging:

- **Document Processing**: Each document is logged when processing starts and completes
- **Indexing Results**: Results from the Azure AI Search service are logged in debug mode
- **Error Handling**: Errors are logged with detailed context for troubleshooting

## Performance Considerations

### Batch Processing

The step processes documents in batches for optimal performance:

- Documents are processed individually but written to the index in batches
- Each document's chunks are processed as a group
- Statistics are collected for monitoring performance

### Optimization Tips

1. **Index Field Selection**: Only map fields that are needed for search
2. **Batch Size**: Consider the size of your documents when configuring timeouts
3. **Service Tiers**: Use appropriate Azure AI Search service tiers for your workload
4. **Monitoring**: Monitor the statistics to identify performance bottlenecks

## Troubleshooting

### Common Issues

#### 1. Service Not Found
```
Error: Azure AI Search Service not found in context
```
**Solution**: Verify that the service is configured and referenced correctly in the pipeline.

#### 2. Invalid Field Mappings
```
Error: Invalid index field mappings format
```
**Solution**: Ensure the field mappings are valid JSON format.

#### 3. Index Not Found
```
Error: Index 'documents-index' not found
```
**Solution**: Create the index in Azure AI Search or verify the index name.

#### 4. Authentication Errors
```
Error: Authentication failed
```
**Solution**: Verify API keys and credential configuration.

### Debug Mode

Enable debug mode for detailed logging:

```yaml
steps:
  - name: write_to_search_index
    step_catalog_id: ai_search_index_writer
    debug_mode: true
    settings:
      ai_search_service: "primary_ai_search_service"
      chunks_field_name: "chunks"
      index_name: "documents-index"
      # ... other settings
```

## Integration Examples

### Complete Pipeline Example

```yaml
pipeline:
  name: "Document Processing and Indexing Pipeline"
  description: "Extract text from PDFs and index in Azure AI Search"
  
  services:
    - name: primary_ai_search_service
      service_catalog_id: azure_ai_search_service_01
      settings:
        account_name: "mysearchservice"
        api_key: "your-api-key"
        # ... other settings
  
  steps:
    - name: extract_pdf_text
      step_catalog_id: ai_pdf_text_extractor
      services: [primary_ai_inference_service]
      settings:
        # ... extractor settings
    
    - name: index_documents
      step_catalog_id: ai_search_index_writer
      services: [primary_ai_search_service]
      settings:
        ai_search_service: "primary_ai_search_service"
        chunks_field_name: "chunks"
        index_name: "documents-index"
        index_field_mappings: |
          {
            "chunk_id": "id",
            "input_file_path": "file_name",
            "page_num": "page_num",
            "markdown": "content",
            "markdown_text": "text_content",
            "summary": "summary"
          }
```


## Best Practices

### 1. Index Design

- **Plan your index schema** before configuring field mappings
- **Use appropriate field types** for different data types
- **Consider search requirements** when designing fields
- **Enable faceting and filtering** for relevant fields

### 2. Field Mapping Strategy

- **Map only necessary fields** to optimize performance
- **Use descriptive index field names** for clarity
- **Validate mappings** before deployment
- **Document your mapping strategy** for maintenance

### 3. Error Handling

- **Monitor processing statistics** regularly
- **Set appropriate retry policies** based on your workload
- **Use debug mode** during development and troubleshooting
- **Implement proper logging** for production monitoring

### 4. Performance Optimization

- **Batch process documents** when possible
- **Monitor Azure AI Search quotas** and limits
- **Use appropriate service tiers** for your workload
- **Consider index partitioning** for large datasets

## Security Considerations

### Authentication

- **Use Azure Key Vault** for storing API keys
- **Implement proper access controls** for services
- **Rotate API keys** regularly
- **Use managed identities** when possible

### Data Privacy

- **Ensure compliance** with data privacy regulations
- **Implement data retention policies** for indexed content
- **Consider data anonymization** for sensitive content
- **Audit access** to indexed data

## Monitoring and Maintenance

### Metrics to Monitor

- **Document processing success rate**
- **Indexing performance**
- **Azure AI Search service health**
- **Storage account usage**

### Maintenance Tasks

- **Regular index optimization**
- **Monitor and clean up failed documents**
- **Update field mappings** as needed
- **Review and update service configurations**

## Version History

- **Version 1.0**: Initial release with basic indexing functionality
- **Future Versions**: Planned enhancements for batch optimization and advanced field mapping

## Support and Resources

- **Step Implementation**: `doc/proc/step/ai_search_index_writer.py`
- **Step Catalog**: `step_catalog.yaml`
- **Service Catalog**: `service_catalog.yaml`
- **Azure AI Search Documentation**: [Documentation](https://learn.microsoft.com/en-us/azure/search)
- **Pipeline Configuration**: Refer to pipeline configuration documentation
