# PDF Text Extractor Step Documentation

## Overview

The PDF Text Extractor step is a specialized component of the document processing pipeline that extracts text and metadata from PDF documents using advanced AI-powered optical character recognition (OCR) and image analysis. This step combines PDF page rendering with Azure AI Inference services to convert PDF pages into structured markdown content.

## Step Information

- **Step ID**: `pdf_text_extractor`
- **Step Name**: PDF Text Extractor
- **Category**: Document Processing
- **Version**: 1.0
- **Module**: `doc.proc.step.pdf_text_extractor`
- **Class**: `PDFTextExtractorStep`

## Description

The PDF Text Extractor step processes PDF documents by first converting each page to PNG images, then using Azure AI Inference services to extract text and analyze visual content. The step produces structured markdown output with separated text content and image descriptions, making it ideal for downstream processing and indexing.

### Key Features

- **Multi-Page Processing**: Convert and process multiple pages from PDF documents
- **High-Quality Rendering**: Configurable DPI settings for optimal image quality
- **AI-Powered Text Extraction**: Uses Azure AI Inference for intelligent text recognition
- **Structured Output**: Separates extracted text from image descriptions
- **Flexible Configuration**: Customizable prompts, page limits, and output formats
- **Batch Processing**: Process multiple documents efficiently
- **Error Handling**: Robust error handling with detailed logging and recovery options
- **Debug Mode**: Comprehensive logging for troubleshooting

## Use Cases

### 1. Document Digitization
Convert scanned PDF documents into searchable, structured text for digital archives.

**Example Scenario**: A law firm digitizes historical case files by converting PDF scans into searchable text, enabling lawyers to quickly find relevant precedents and case information.

### 2. Research Paper Processing
Extract text and analyze figures, tables, and diagrams from academic papers.

**Example Scenario**: Researchers process scientific literature to extract key findings, methodology descriptions, and experimental data for systematic reviews and meta-analyses.

### 3. Contract and Legal Document Analysis
Extract text from legal contracts while preserving formatting and identifying key clauses.

**Example Scenario**: A corporate legal department processes hundreds of contracts to extract key terms, dates, and obligations for compliance monitoring.

### 4. Financial Document Processing
Extract text from financial reports, statements, and regulatory filings.

**Example Scenario**: Financial analysts process quarterly reports and SEC filings to extract key financial metrics and management commentary for investment analysis.

### 5. Technical Documentation Conversion
Convert technical manuals and documentation from PDF to structured markdown.

**Example Scenario**: A software company converts PDF user manuals to markdown format for integration into their online documentation platform.

### 6. Form Processing and Data Extraction
Extract structured data from filled forms and applications.

**Example Scenario**: An insurance company processes claim forms by extracting policyholder information, incident details, and damage assessments.

## Prerequisites

### Required Services

1. **Azure AI Inference Service**: A configured Azure AI service for image analysis and text extraction

### Required Dependencies

- **PyMuPDF**: For PDF page rendering and conversion
- **Azure AI Inference SDK**: For AI-powered text extraction
- **Python Imaging Libraries**: For image processing and format conversion

### Input Data Requirements

The step expects input data in the following structure:

```python
{
  "documents": [
    {
      "file_path": "/path/to/document.pdf",
      "document_type": {
                "primary_type": "pdf" # if type condition is used - see below.
            }
    }
  ]
}
```

## Configuration

### Required Settings

#### AI Inference Service
- **Parameter**: `ai_model_inference_service`
- **Type**: String
- **Description**: Reference to the Azure AI Inference service instance
- **Required**: Yes
- **UI Component**: Service Selector (azure_ai_inference)

### File Processing Settings

#### PNG Output Folder
- **Parameter**: `png_output_folder`
- **Type**: String
- **Description**: Directory path where PNG files will be saved
- **Required**: Yes
- **Default**: `./output/png`
- **Pattern**: `^\\.\\/.*` (must start with `./`)

#### Number of Pages
- **Parameter**: `num_pages`
- **Type**: Integer
- **Description**: Maximum number of pages to convert (-1 = all pages)
- **Required**: No
- **Default**: `-1`
- **Range**: `-1` to `200`

#### DPI Resolution
- **Parameter**: `dpi`
- **Type**: Integer
- **Description**: Resolution for PNG output in dots per inch
- **Required**: No
- **Default**: `300`
- **Range**: `72` to `600`

#### Image Format
- **Parameter**: `image_format`
- **Type**: String
- **Description**: Output image format
- **Required**: No
- **Default**: `PNG`
- **Options**: `PNG`, `JPEG`, `TIFF`

### AI Processing Settings

#### Prompts Configuration
- **Parameter**: `prompts`
- **Type**: Object
- **Description**: Contains system and user prompts for AI processing
- **Required**: Yes
- **Structure**:
  - `system`: System-level instructions for the AI
  - `user`: User prompt template for processing images

#### System Prompt
- **Parameter**: `prompts.system`
- **Type**: String
- **Description**: Instructions for the AI system
- **Required**: Yes
- **Default**: `You are an AI assistant that helps convert images of pages of a pdf document to markdown text. Only output valid markdown.`

#### User Prompt Template
- **Parameter**: `prompts.user`
- **Type**: String
- **Description**: Template for user prompts sent to AI
- **Required**: Yes
- **Default**: Complex template with structured output format

#### Max Completion Tokens
- **Parameter**: `max_completion_tokens`
- **Type**: Integer
- **Description**: Maximum number of tokens to generate
- **Required**: No
- **Default**: `4000`
- **Range**: `100` to `8000`

#### Temperature
- **Parameter**: `temperature`
- **Type**: Number
- **Description**: Controls randomness in AI responses (0.0 = deterministic, 2.0 = very random)
- **Required**: No
- **Default**: `1.0`
- **Range**: `0.0` to `2.0`
- **Step**: `0.1`

#### Top P
- **Parameter**: `top_p`
- **Type**: Number
- **Description**: Controls diversity of AI responses
- **Required**: No
- **Default**: `1.0`
- **Range**: `0.0` to `1.0`
- **Step**: `0.1`

#### Frequency Penalty
- **Parameter**: `frequency_penalty`
- **Type**: Number
- **Description**: Reduces repetition in AI responses
- **Required**: No
- **Default**: `0.0`
- **Range**: `-2.0` to `2.0`
- **Step**: `0.1`

#### Presence Penalty
- **Parameter**: `presence_penalty`
- **Type**: Number
- **Description**: Encourages AI to talk about new topics
- **Required**: No
- **Default**: `0.0`
- **Range**: `-2.0` to `2.0`
- **Step**: `0.1`

### Conditional Processing

The step supports conditional execution based on document properties:

#### Condition Parameter
- **Parameter**: `condition`
- **Type**: String
- **Description**: Expression that determines whether to process a document
- **Required**: No
- **Default**: None (process all documents)

#### Example Conditions

**Process only PDF documents:**
```yaml
condition: "document_type.primary_type == 'pdf'"
```

**Process documents larger than 1MB:**
```yaml
condition: "file_size > 1048576"
```

**Process documents with specific patterns:**
```yaml
condition: "file_name.contains('report')"
```

When a condition is not met, the document is skipped and counted in the `skipped_documents` statistic.

### Debug Configuration

The step supports debug mode for detailed logging and troubleshooting:

#### Debug Mode
- **Parameter**: `debug_mode`
- **Type**: Boolean
- **Description**: Enable detailed debug logging
- **Required**: No
- **Default**: `false`

When enabled, debug mode provides:
- Detailed processing logs for each document
- Step initialization parameters
- Processing time information
- Detailed error messages and stack traces

#### Failure Handling
- **Parameter**: `fail_step_on_document_error`
- **Type**: Boolean
- **Description**: Whether to fail the entire step if a single document fails
- **Required**: No
- **Default**: `false`

When set to `true`, any document processing error will cause the entire step to fail. When `false`, failed documents are logged and counted in statistics, but processing continues.

### Step Configuration Example

```yaml
steps:
  - name: extract_pdf_text
    step_catalog_id: pdf_text_extractor
    enabled: true
    fail_pipeline_on_error: true
    retry_on_failure: false
    retries: 3
    timeout: 600
    services: [primary_ai_inference_service]
    condition: "document_type.primary_type == 'pdf'"
    fail_step_on_document_error: false
    debug_mode: false
    settings:
      png_output_folder: "./output/png"
      num_pages: 10
      dpi: 300
      image_format: "PNG"
      prompts:
        system: "You are an AI assistant that helps convert images of pages of a pdf document to markdown text. Only output valid markdown."
        user: |
          Extract the text from the following image into markdown and provide descriptions of images. 
          Always format the markdown as follows to distinguish the text extracted from image descriptions:
          
          ==Extracted-Text==
          {Insert extracted text as markdown here}
          ==End-Extracted-Text==

          ==Image-Descriptions==
          {Insert image descriptions as markdown here}
          ==End-Image-Descriptions==
      max_completion_tokens: 4000
      temperature: 1.0
      top_p: 1.0
      frequency_penalty: 0.0
      presence_penalty: 0.0
```

## Service Configuration

## Service Configuration

### Azure AI Inference Service

The step requires a configured Azure AI Inference service:

```yaml
services:
  - name: primary_ai_inference_service
    service_catalog_id: azure_ai_inference_service_01
    settings:
      endpoint: "https://your-ai-service.cognitiveservices.azure.com/"
      api_version: "2024-02-01"
```

## Processing Workflow

### Step 1: PDF to PNG Conversion

1. **PDF Loading**: Load the PDF document using PyMuPDF
2. **Page Iteration**: Process each page up to the specified limit
3. **Image Rendering**: Convert each page to PNG with specified DPI
4. **File Storage**: Save PNG files to the configured output folder
5. **Metadata Generation**: Generate unique page IDs and metadata

### Step 2: AI-Powered Text Extraction

1. **Image Analysis**: Send each PNG image to Azure AI Inference
2. **Text Extraction**: Use AI to extract text content from images
3. **Content Structure**: Parse AI response into structured sections
4. **Markdown Generation**: Format extracted content as markdown

### Step 3: Content Processing

1. **Text Separation**: Extract plain text from markdown
2. **Image Description Parsing**: Extract image descriptions
3. **Metadata Enrichment**: Add page numbers and file references
4. **Chunk Assembly**: Organize content into processable chunks

## Output Data Structure

The step produces a structured output with detailed chunks for each page:

```python
{
  "summary_data": {
    "pdf_text_extractor_stats": {
      "total_documents": 1,
      "successful_documents": 1,
      "skipped_documents": 0,
      "failed_documents": 0
    }
  },
  "data": {
    "documents": [
      {
        "file_path": "/path/to/document.pdf",
        "chunks": [
          {
            "input_file_path": "/path/to/document.pdf",
            "chunk_id": "abc123def456...",
            "chunk_num": 1,
            "chunk_type": "page",
            "page_num": 1,
            "png": "./output/png/page_1.png",
            "markdown": "==Extracted-Text==\n# Document Title\n...\n==End-Extracted-Text==\n\n==Image-Descriptions==\n...\n==End-Image-Descriptions==",
            "page_text": "# Document Title\n...",
            "page_image_descriptions": "Description of charts and figures...",
            "text": "# Document Title\n...Description of charts and figures..."
          }
        ]
      }
    ]
  }
}
```

### Output Fields Description

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | String | Unique SHA1 hash identifier for the page |
| `input_file_path` | String | Original PDF file path |
| `chunk_num` | Integer | Sequential chunk number within the document |
| `chunk_type` | String | Type of chunk (always "page" for PDF pages) |
| `page_num` | Integer | Page number within the document |
| `png` | String | Path to the generated PNG file |
| `markdown` | String | Complete markdown content with structured sections |
| `page_text` | String | Plain text extracted from the page |
| `page_image_descriptions` | String | Descriptions of images found on the page |
| `text` | String | Combined text content (page_text + page_image_descriptions) |

## Execution Statistics

The step tracks detailed execution statistics for monitoring and debugging purposes:

### Statistics Fields

| Field | Description |
|-------|-------------|
| `total_documents` | Total number of documents processed |
| `successful_documents` | Number of documents processed successfully |
| `skipped_documents` | Number of documents skipped due to conditions |
| `failed_documents` | Number of documents that failed processing |

### Statistics Usage

These statistics are included in the `summary_data` section of the output under the key `{step_name}_stats` (e.g., `pdf_text_extractor_1_stats`). They can be used for:

- **Monitoring**: Track processing success rates
- **Debugging**: Identify failure patterns
- **Optimization**: Understand processing bottlenecks
- **Reporting**: Generate processing summaries

## Prompt Engineering

### Default System Prompt

```
You are an AI assistant that helps convert images of pages of a pdf document to markdown text. Only output valid markdown.
```

### Default User Prompt Template

```
Extract the text from the following image into markdown and provide descriptions of images. Always format the markdown as follows to distinguish the text extracted from image descriptions:

==Extracted-Text==
{Insert extracted text as markdown here}
==End-Extracted-Text==

==Image-Descriptions==
{Insert image descriptions as markdown here}
==End-Image-Descriptions==
```

### Custom Prompt Design

#### Best Practices for System Prompts

1. **Be Specific**: Clearly define the AI's role and expected behavior
2. **Set Output Format**: Specify the desired output format (markdown, JSON, etc.)
3. **Include Context**: Provide context about the document type or domain
4. **Quality Instructions**: Include instructions for handling edge cases

#### Example Custom System Prompts

**For Legal Documents:**
```
You are an AI assistant specialized in legal document analysis. Convert PDF pages to markdown while preserving legal terminology, clause structures, and formatting. Focus on accuracy and maintain the hierarchical structure of legal documents.
```

**For Technical Documentation:**
```
You are an AI assistant specialized in technical documentation. Convert PDF pages to markdown while preserving code snippets, technical diagrams, and procedural steps. Pay special attention to technical accuracy and formatting.
```

**For Financial Reports:**
```
You are an AI assistant specialized in financial document analysis. Convert PDF pages to markdown while preserving numerical data, tables, and financial terminology. Ensure accuracy of financial figures and maintain table structures.
```

#### User Prompt Customization

**For Table-Heavy Documents:**
```
Extract the text from the following image into markdown. Pay special attention to tables and preserve their structure. Format as follows:

==Extracted-Text==
{Insert extracted text as markdown here, preserving table structures}
==End-Extracted-Text==

==Image-Descriptions==
{Insert descriptions of charts, graphs, and non-table images}
==End-Image-Descriptions==
```

**For Scientific Papers:**
```
Extract the text from the following image into markdown. Focus on scientific accuracy and preserve mathematical equations, formulas, and scientific notation. Format as follows:

==Extracted-Text==
{Insert extracted text as markdown here, preserving scientific notation}
==End-Extracted-Text==

==Image-Descriptions==
{Insert descriptions of figures, diagrams, and experimental setups}
==End-Image-Descriptions==
```

## Error Handling

### Error Types

1. **File System Errors**: Missing PDF files, permission issues, disk space
2. **PDF Processing Errors**: Corrupt PDFs, unsupported formats, encryption
3. **AI Service Errors**: API limits, authentication failures, model errors
4. **Image Processing Errors**: Conversion failures, format issues

### Error Handling Configuration

#### Fail on Document Error
- **Setting**: `fail_step_on_document_error`
- **Default**: `false`
- **Description**: Whether to fail the entire step if a single document fails

#### Retry Configuration
- **Retry on Failure**: `true`
- **Retry Count**: `3`
- **Timeout**: `600` seconds

### Common Error Scenarios

#### 1. PDF File Not Found
```
Error: PDF file not found: /path/to/document.pdf
```
**Solution**: Verify the file path and ensure the PDF exists

#### 2. AI Service Unavailable
```
Error: Azure AI Model Inference Service not found in context
```
**Solution**: Verify service configuration and network connectivity

#### 3. PNG Conversion Failed
```
Error: Error converting PNG file to Markdown
```
**Solution**: Check image quality, file permissions, and AI service limits

#### 4. Insufficient Permissions
```
Error: Permission denied when creating output directory
```
**Solution**: Ensure write permissions for the output folder

### Error Recovery

The step implements several recovery mechanisms:

1. **Page-Level Recovery**: If one page fails, processing continues with remaining pages
2. **Graceful Degradation**: Warnings for non-critical failures
3. **Detailed Logging**: Comprehensive error information for debugging
4. **Statistics Tracking**: Track success/failure rates for monitoring

## Performance Optimization

### Processing Speed

#### Factors Affecting Performance

1. **Page Count**: More pages require more processing time
2. **Image Quality**: Higher DPI increases processing time
3. **AI Model**: Different models have varying response times
4. **Network Latency**: API calls to Azure services

#### Optimization Strategies

1. **Batch Processing**: Process multiple documents in parallel
2. **DPI Optimization**: Use appropriate DPI for content type
3. **Page Limits**: Set reasonable page limits for large documents
4. **Model Selection**: Choose appropriate AI models for your use case

### Resource Usage

#### Memory Considerations

- **PDF Size**: Large PDFs require more memory
- **Image Generation**: PNG files consume disk space
- **AI Responses**: Large responses use more memory

#### Disk Space Management

- **Output Folder**: Monitor PNG file accumulation
- **Cleanup**: Implement cleanup routines for temporary files
- **Compression**: Consider image compression for storage

### Scalability

#### Horizontal Scaling

1. **Document Partitioning**: Split large document sets across instances
2. **Service Scaling**: Scale Azure AI services for higher throughput
3. **Storage Scaling**: Use appropriate storage tiers for volume

#### Vertical Scaling

1. **CPU**: More cores for concurrent processing
2. **Memory**: Sufficient RAM for large documents
3. **Storage**: Fast storage for improved I/O

## Integration Examples

### Complete Pipeline Example

```yaml
pipeline:
  name: "PDF Processing and Indexing Pipeline"
  description: "Extract text from PDFs and index in search service"
  
  services:
    - name: primary_ai_inference_service
      service_catalog_id: azure_ai_inference_service_01
      settings:
        endpoint: "https://myaiservice.cognitiveservices.azure.com/"
        api_key: "your-api-key"
        model_name: "gpt-4-vision-preview"
        
    - name: primary_ai_search_service
      service_catalog_id: azure_ai_search_service_01
      settings:
        account_name: "mysearchservice"
        api_key: "your-search-api-key"
        index_name: "documents-index"
  
  steps:
    - name: extract_pdf_text
      step_catalog_id: pdf_text_extractor
      services: [primary_ai_inference_service]
      settings:
        png_output_folder: "./output/png"
        num_pages: 20
        dpi: 300
        image_format: "PNG"
        prompts:
            system: "You are an AI assistant that helps convert images of pages of a pdf document to markdown text. Only output valid markdown."
            user: |
              Extract the text from the following image into markdown and provide descriptions of images. 
              Always format the markdown as follows to distinguish the text extracted from image descriptions:
              
              ==Extracted-Text==
                {Insert extracted text as markdown here}
              ==End-Extracted-Text==
                
              ==Image-Descriptions==
                {Insert image descriptions as markdown here}
              ==End-Image-Descriptions==
        max_completion_tokens: 4000
        temperature: 0.7
        top_p: 0.4
        
    - name: index_documents
      step_catalog_id: ai_search_index_writer
      services: [primary_ai_search_service]
      settings:
        ai_search_service: "primary_ai_search_service"
        index_name: "documents-index"
        index_field_mappings: |
          {
            "chunk_id": "id",
            "input_file_path": "file_name",
            "page_num": "page_num",
            "markdown": "content",
            "page_text": "text_content",
            "page_image_descriptions": "image_descriptions"
          }
```

### Batch Processing Example

```yaml
pipeline:
  name: "Batch PDF Processing"
  description: "Process multiple PDFs in parallel"
  
  steps:
    - name: extract_legal_documents
      step_catalog_id: pdf_text_extractor
      services: [primary_blob_storage, primary_ai_inference_service]
      settings:
        png_output_folder: "./output/legal_docs"
        num_pages: -1  # Process all pages
        dpi: 300
        prompts:
          system: "You are an AI assistant specialized in legal document analysis. Convert PDF pages to markdown while preserving legal terminology and clause structures."
          user: |
            Extract the text from this legal document page into markdown. 
            Preserve the hierarchical structure and legal formatting.
            
            ==Extracted-Text==
            {Insert extracted legal text with proper formatting}
            ==End-Extracted-Text==
            
            ==Image-Descriptions==
            {Insert descriptions of any diagrams, signatures, or visual elements}
            ==End-Image-Descriptions==
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Poor Text Extraction Quality

**Symptoms**: Inaccurate text extraction, missing content
**Causes**: 
- Low DPI settings
- Poor image quality
- Inappropriate AI model

**Solutions**:
- Increase DPI to 300 or higher
- Use appropriate AI model for document type
- Adjust system prompts for better context

#### 2. Slow Processing Speed

**Symptoms**: Long processing times, timeouts
**Causes**:
- High DPI settings
- Large page counts
- Network latency

**Solutions**:
- Optimize DPI settings
- Implement page limits
- Use regional Azure services

#### 3. Memory Issues

**Symptoms**: Out of memory errors, crashes
**Causes**:
- Large PDF files
- High DPI settings
- Insufficient system memory

**Solutions**:
- Process fewer pages at once
- Reduce DPI settings
- Increase available memory

#### 4. Authentication Failures

**Symptoms**: API authentication errors
**Causes**:
- Invalid API keys
- Expired credentials
- Network connectivity issues

**Solutions**:
- Verify API key validity
- Check network connectivity
- Ensure service endpoints are correct

### Debug Mode

Enable debug mode for comprehensive logging:

```yaml
steps:
  - name: extract_pdf_text
    step_catalog_id: pdf_text_extractor
    debug_mode: true
    # ... other settings
```

Debug mode provides:
- Detailed processing logs
- AI request/response logging
- File operation tracking
- Performance metrics

## Best Practices

### 1. Document Preparation

- **File Quality**: Ensure PDFs are not corrupted or password-protected
- **Size Management**: Consider splitting very large documents
- **Format Consistency**: Standardize PDF formats when possible
- **Metadata Preservation**: Maintain original file metadata

### 2. Configuration Optimization

- **DPI Settings**: Use 300 DPI for standard documents, 600 for fine detail
- **Page Limits**: Set reasonable limits based on document types
- **Prompt Engineering**: Customize prompts for document domains
- **Token Management**: Monitor and optimize token usage

### 3. Error Handling Strategy

- **Graceful Degradation**: Continue processing when individual pages fail
- **Comprehensive Logging**: Implement detailed error logging
- **Monitoring**: Track success rates and processing times
- **Recovery Procedures**: Define procedures for handling failures

### 4. Performance Optimization

- **Batch Processing**: Group similar documents for efficiency
- **Resource Monitoring**: Monitor CPU, memory, and disk usage
- **Service Scaling**: Scale Azure services based on demand
- **Caching**: Implement caching for frequently processed documents

### 5. Security and Compliance

- **Data Protection**: Ensure sensitive documents are handled securely
- **Access Control**: Implement proper access controls for services
- **Audit Trails**: Maintain processing logs for compliance
- **Data Retention**: Implement appropriate data retention policies

## Security Considerations

### Data Privacy

- **Sensitive Content**: Be aware of sensitive information in documents
- **Data Residency**: Ensure compliance with data residency requirements
- **Encryption**: Use encryption for data in transit and at rest
- **Access Logging**: Log all access to processed documents

### Service Security

- **API Key Management**: Use Azure Key Vault for API key storage
- **Network Security**: Implement network security groups and firewalls
- **Authentication**: Use managed identities when possible
- **Regular Updates**: Keep services and dependencies updated

### Compliance

- **GDPR**: Ensure GDPR compliance for EU documents
- **HIPAA**: Implement HIPAA controls for healthcare documents
- **SOX**: Maintain SOX compliance for financial documents
- **Industry Standards**: Follow industry-specific compliance requirements

## Monitoring and Maintenance

### Key Metrics

- **Processing Success Rate**: Percentage of successfully processed documents
- **Average Processing Time**: Time per document/page
- **Error Rate**: Frequency of different error types
- **Resource Utilization**: CPU, memory, and storage usage
- **API Usage**: Azure service consumption and costs

### Maintenance Tasks

- **Regular Cleanup**: Remove old PNG files and temporary data
- **Service Updates**: Keep Azure services updated
- **Performance Tuning**: Optimize settings based on usage patterns
- **Cost Optimization**: Monitor and optimize Azure service costs

### Alerting

Set up alerts for:
- High error rates
- Processing delays
- Resource constraints
- Service availability issues

## Version History

- **Version 1.0**: Initial release with basic PDF to markdown conversion
- **Future Versions**: Planned enhancements for:
  - Advanced table extraction
  - Multi-language support
  - Enhanced image analysis
  - Improved error recovery

## Support and Resources

- **Step Implementation**: `doc/proc/step/pdf_text_extractor.py`
- **Step Catalog**: `step_catalog.yaml`
- **Service Catalog**: `service_catalog.yaml`
- **PyMuPDF Documentation**: [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- **Azure AI Documentation**: [Azure AI Services Documentation](https://docs.microsoft.com/azure/cognitive-services/)
- **Pipeline Configuration**: Refer to pipeline configuration documentation
