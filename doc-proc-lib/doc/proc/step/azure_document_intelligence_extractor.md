# Azure Document Intelligence Extractor Step

## Overview

The Azure Document Intelligence Extractor Step (`AzureDocumentIntelligenceExtractorStep`) is a powerful document processing component that leverages Azure's Document Intelligence service (formerly Form Recognizer) to extract structured content from various document formats. This step provides advanced capabilities for extracting text, tables, key-value pairs, and structured layouts from documents with high accuracy and confidence scores.

## Description

The Azure Document Intelligence Extractor step processes documents using Azure's Document Intelligence service to extract and structure content. Unlike traditional text extraction methods, this step understands document layouts, identifies tables, form fields, and key-value pairs, making it ideal for processing structured and semi-structured documents.

### Key Features

- **Multiple Model Support**: Use various pre-built models for different document types
- **Structured Content Extraction**: Extract text with layout understanding
- **Table Processing**: Identify and extract tables with cell-level precision
- **Key-Value Pair Extraction**: Automatically identify form fields and their values
- **Page-wise Processing**: Option to process documents page by page or as a whole
- **Confidence Scoring**: Provides confidence scores for extracted content
- **Format Flexibility**: Output content in structured, markdown, or text formats
- **Multi-format Support**: Process PDFs, images, and Office documents
- **Conditional Processing**: Support for conditional document processing
- **Error Handling**: Robust error handling with detailed statistics

## Use Cases

### Business Documents
- **Invoices**: Extract vendor information, line items, totals
- **Receipts**: Process expense receipts for accounting
- **Business Cards**: Extract contact information
- **Tax Forms**: Process tax documents like W-2 forms

### Legal Documents
- **Contracts**: Extract key terms and clauses
- **Legal Forms**: Process structured legal documents
- **Court Documents**: Extract case information and details

### Healthcare Documents
- **Insurance Cards**: Extract member and plan information
- **Medical Forms**: Process patient intake forms
- **Healthcare Claims**: Extract claim details and amounts

### General Documents
- **Forms**: Process any structured form documents
- **Reports**: Extract data from formatted reports
- **Surveys**: Process survey responses and data

## Prerequisites

### Required Services

1. **Azure Document Intelligence Service**: A configured Azure Document Intelligence service instance

### Input Data Requirements

The step expects a `Document` instance with the following data structure:

```python
{
    "temp_file_path": "/path/to/document.pdf"
}
```

**Required Fields:**
- `temp_file_path`: Path to the document file to be processed

### Supported File Formats

- **PDF**: Portable Document Format files (.pdf)
- **Images**: JPEG (.jpg, .jpeg), PNG (.png), BMP (.bmp), TIFF (.tiff, .tif), HEIC (.heic)
- **Office Documents**: DOCX (.docx), XLSX (.xlsx), PPTX (.pptx) - limited support

## Configuration

### Required Settings

#### Output Field Name
- **Parameter**: `output_field_name`
- **Type**: String
- **Description**: Field name in document data dict to store the extracted content
- **Required**: No
- **Default**: `doc_intell_chunks`

#### Model Selection
- **Parameter**: `model_id`
- **Type**: String
- **Description**: Model ID to use for document analysis
- **Required**: No
- **Default**: `prebuilt-layout`

### Optional Settings

#### Content Extraction Options
- **Parameter**: `extract_tables`
- **Type**: Boolean
- **Description**: Whether to extract and process table content
- **Default**: `true`

- **Parameter**: `extract_key_value_pairs`
- **Type**: Boolean
- **Description**: Whether to extract key-value pairs from documents
- **Default**: `true`

- **Parameter**: `extract_paragraphs`
- **Type**: Boolean
- **Description**: Whether to extract paragraph content
- **Default**: `true`

#### Processing Options
- **Parameter**: `chunk_by_pages`
- **Type**: Boolean
- **Description**: Whether to create separate chunks for each page
- **Default**: `true`

- **Parameter**: `output_format`
- **Type**: String
- **Description**: Format for the extracted content
- **Default**: `markdown`
- **Options**:
  - `structured`: Structured data format with metadata
  - `markdown`: Markdown formatted text
  - `text`: Plain text format

## Processing Flow

1. **Input Validation**: Validates Document instance and ensures it contains the required `temp_file_path` field
2. **Service Initialization**: Retrieves Azure Document Intelligence service from context
3. **File Validation**: Checks file existence and supported format
4. **File Reading**: Reads document file as binary data
5. **Document Analysis**: Sends document to Azure Document Intelligence service with specified model
6. **Content Processing**: Processes analysis results into structured chunks
7. **Chunk Creation**: Creates chunks based on configuration (pages, tables, key-value pairs, or document-level)
8. **Format Application**: Applies selected output format (structured, markdown, or text)
9. **Metadata Addition**: Adds confidence scores, chunk metadata, and structural information
10. **Output Update**: Adds processed chunks to document data using specified output field name

## Output Data Structure

### Chunk Structure

Each processed document will have the specified output field (default: `doc_intell_chunks`) with the following structure:

```python
{
  "doc_intell_chunks": [
    {
      "input_file_path": "/path/to/document.pdf",
      "chunk_id": "sha1_hash_of_content",
      "chunk_type": "page|table|key_value_pairs|document",
      "chunk_num": 1,
      "page_num": 1, # For page chunks
      "markdown_text": "Extracted text in markdown format",
      "json": "Extracted text in JSON format", 
      "raw_text": "Raw extracted text",
      "structured_content": {
        "page_number": 1,
        "word_count": 150,
        "line_count": 12,
        "words": [...],
        "lines": [...],
        "paragraphs": [...]
      }, # Only for structured output format
      "confidence": 0.98,
      "table_data": {...}, # For table chunks
      "row_count": 5, # For table chunks
      "column_count": 3, # For table chunks
      "key_value_data": [...], # For key-value chunks
      "total_pairs": 10, # For key-value chunks
      "total_pages": 5, # For document-level chunks
      "text": "Combined key-value text" # For key-value chunks
    }
  ]
}
```


## Usage Example

```python
from doc.proc.step.azure_document_intelligence_extractor import AzureDocumentIntelligenceExtractorStep
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import Document

# Configure the step
instance_config = StepInstanceConfig(
    name="document_intelligence_extractor",
    step_catalog_id="azure_document_intelligence_extractor",
    enabled=True,
    services=["primary_document_intelligence_service"],
    settings={
        "output_field_name": "doc_intell_chunks",
        "model_id": "prebuilt-layout",
        "extract_tables": True,
        "extract_key_value_pairs": True,
        "extract_paragraphs": True,
        "chunk_by_pages": True,
        "output_format": "markdown"
    },
    debug_mode=False
)

# Create step instance  
extractor = AzureDocumentIntelligenceExtractorStep(instance_config=instance_config)

# Prepare input document
document = Document(
    id="doc_1",
    data={"temp_file_path": "/path/to/document.pdf"}
)

# Process document (requires pipeline context)
# result = await extractor.run(document, context)
```

## Azure Document Intelligence Service Configuration

### Service Settings

The step requires a configured Azure Document Intelligence service:

```yaml
services:
  - name: primary_document_intelligence_service
    service_catalog_id: azure_document_intelligence_service_01
    settings:
      endpoint: "${AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT}"
      credential_type: "azure_key_credential"
      api_key: "${AZURE_DOCUMENT_INTELLIGENCE_API_KEY}"
```

## Model Selection Guide

### General Purpose Models

- **prebuilt-layout**: Best for general document analysis with layout understanding
- **prebuilt-document**: Good for mixed document types with basic structure
- **prebuilt-read**: Basic OCR text extraction without structure

### Specialized Models

- **prebuilt-invoice**: Optimized for invoice processing with line items and totals
- **prebuilt-receipt**: Designed for receipt processing with merchant and item details
- **prebuilt-businessCard**: Extracts contact information from business cards
- **prebuilt-idDocument**: Processes ID documents like driver's licenses
- **prebuilt-tax.us.w2**: Specialized for US W-2 tax forms
- **prebuilt-healthInsuranceCard.us**: US health insurance card processing

## Error Handling

### Common Issues

#### Service Connection Errors
- **Cause**: Invalid endpoint or authentication credentials
- **Solution**: Verify service configuration and API keys
- **Prevention**: Test service connection before running pipeline

#### Unsupported File Format
- **Cause**: File format not supported by selected model
- **Solution**: Convert file to supported format or use different model
- **Prevention**: Validate file formats in earlier pipeline steps

#### Model Quota Exceeded
- **Cause**: Azure service quota limits reached
- **Solution**: Reduce processing frequency or upgrade service tier
- **Prevention**: Monitor service usage and implement rate limiting

#### Large File Processing
- **Cause**: File size exceeds service limits
- **Solution**: Split large files or use different processing approach
- **Prevention**: Implement file size validation

### Error Recovery

The step includes several error recovery mechanisms:

- **Document-level Error Handling**: Continue processing remaining documents if one fails
- **Graceful Degradation**: Fallback to basic text extraction if advanced features fail
- **Retry Logic**: Automatic retry for transient service errors
- **Detailed Logging**: Comprehensive error logging for troubleshooting

## Performance Considerations

### Throughput Optimization

- **Batch Processing**: Process multiple documents in parallel where possible
- **Model Selection**: Choose appropriate models for your document types
- **Chunk Configuration**: Optimize chunking strategy for downstream processing
- **Service Tier**: Use appropriate Azure service tier for your volume

### Cost Management

- **Model Efficiency**: Use more efficient models when advanced features aren't needed
- **Page Limits**: Set reasonable page limits for long documents
- **Caching**: Implement result caching for frequently processed documents
- **Usage Monitoring**: Monitor API usage to manage costs

## Integration Examples

### Basic Document Processing Pipeline

```yaml
pipeline:
  name: "Document Intelligence Processing Pipeline"
  description: "Extract structured content from business documents"
  
  services:
    - name: primary_document_intelligence
      service_catalog_id: azure_document_intelligence_service_01
      settings:
        endpoint: "${AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT}"
        credential_type: "azure_key_credential"
        api_key: "${AZURE_DOCUMENT_INTELLIGENCE_API_KEY}"
        api_version: "2023-07-31"
  
  steps:
    - name: extract_content
      step_catalog_id: azure_document_intelligence_extractor
      services: [primary_document_intelligence]
      settings:
        model_id: "prebuilt-layout"
        output_format: "structured"
        chunk_by_pages: true
        extract_tables: true
        extract_key_value_pairs: true
```

### Invoice Processing Pipeline

```yaml
pipeline:
  name: "Invoice Processing Pipeline"
  description: "Process invoices with specialized model"
  
  services:
    - name: invoice_intelligence
      service_catalog_id: azure_document_intelligence_service_01
      settings:
        endpoint: "${AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT}"
        credential_type: "azure_key_credential"
        api_key: "${AZURE_DOCUMENT_INTELLIGENCE_API_KEY}"
        model_id: "prebuilt-invoice"
  
  steps:
    - name: process_invoices
      step_catalog_id: azure_document_intelligence_extractor
      services: [invoice_intelligence]
      settings:
        model_id: "prebuilt-invoice"
        output_format: "markdown"
        extract_tables: true
        extract_key_value_pairs: true
```

## Best Practices

### Document Preparation

- **Quality**: Use high-quality, clear document images
- **Orientation**: Ensure documents are properly oriented
- **Format**: Use PDF format when possible for best results
- **Resolution**: Use appropriate resolution for image documents (300 DPI recommended)

### Model Selection

- **Specificity**: Use specialized models for specific document types
- **Testing**: Test different models with your document types
- **Fallback**: Have fallback strategies for unsupported formats
- **Performance**: Balance accuracy needs with processing speed

### Configuration Optimization

- **Chunking Strategy**: Choose appropriate chunking based on downstream needs
- **Content Selection**: Only extract content types you need to reduce processing time
- **Batch Size**: Optimize batch sizes for your infrastructure
- **Error Handling**: Configure appropriate error handling for your use case

### Security and Compliance

- **Data Privacy**: Ensure compliance with data privacy regulations
- **Access Control**: Implement proper access controls for sensitive documents
- **Audit Logging**: Enable audit logging for document processing
- **Data Retention**: Implement appropriate data retention policies

## Troubleshooting

### Common Problems

#### No Content Extracted
- Check if file format is supported
- Verify document quality and readability
- Try different models for better recognition
- Check service logs for detailed errors

#### Poor Extraction Quality
- Use specialized models for document types
- Improve document quality (resolution, orientation)
- Adjust confidence thresholds if available
- Consider document preprocessing

#### Service Timeouts
- Reduce document size or complexity
- Implement retry logic with backoff
- Check service tier limitations
- Split large documents into smaller parts

#### High Processing Costs
- Use appropriate models for document complexity
- Implement document filtering and validation
- Monitor usage patterns and optimize
- Consider caching frequently processed documents

### Debugging Tips

- Enable debug mode for detailed logging
- Check service connection and authentication
- Validate document formats before processing
- Review extraction results and confidence scores
- Monitor service usage and quotas
- Check file permissions and accessibility

## Dependencies

### Required Services
- **Azure Document Intelligence Service**: Required for document analysis
  - Service type: `azure_document_intelligence`
  - Used for: Document analysis and content extraction


## Version History

- **Version 1.0**: Initial release with core functionality
  - Azure Document Intelligence SDK integration
  - Multiple model support (prebuilt models)
  - Structured content extraction with confidence scoring
  - Page-wise and document-level chunking strategies
  - Table extraction with markdown and text formatting
  - Key-value pair extraction and processing
  - Conditional document processing support
  - Comprehensive error handling and statistics
  - Debug mode with detailed logging and result export

## Implementation Details

### Chunk Types

The step creates different types of chunks based on the configuration:

1. **Page Chunks** (`chunk_type: "page"`): Created when `chunk_by_pages` is `true`
   - Contains text from individual pages
   - Includes page number and confidence scores
   - Structured content includes word and line information

2. **Document Chunks** (`chunk_type: "document"`): Created when `chunk_by_pages` is `false`
   - Contains entire document content
   - Includes total page count
   - Overall document confidence score

3. **Table Chunks** (`chunk_type: "table"`): Created when `extract_tables` is `true`
   - Contains formatted table data
   - Supports markdown and text formats
   - Includes row and column counts

4. **Key-Value Chunks** (`chunk_type: "key_value_pairs"`): Created when `extract_key_value_pairs` is `true`
   - Contains extracted form fields
   - Includes confidence scores for each pair
   - Aggregates all key-value pairs from the document

### Content Formats

The step supports three output formats:

- **Structured**: Preserves all metadata and structural information
- **Markdown**: Formats content with markdown syntax (especially useful for tables)
- **Text**: Plain text format for simple downstream processing

### Error Handling

The implementation includes robust error handling:

- **File-level validation**: Checks file existence and format support
- **Service connection errors**: Handles authentication and endpoint issues
- **Document processing errors**: Individual document failures don't stop the pipeline
- **Graceful degradation**: Continues processing other documents on errors
  - Table and key-value pair processing
  - Configurable output formats


## Support and Resources

### Azure Documentation
- [Azure Document Intelligence Documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/?view=doc-intel-4.0.0)

### Best Practices
- [Model Selection Guide](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept/choose-model-feature?view=doc-intel-4.0.0)
