# Azure Document Intelligence Example

This example demonstrates using Azure Document Intelligence service for structured document extraction:
- Extract text, tables, and key-value pairs
- Process various document formats (PDF, images, Office documents)
- Use prebuilt models for common document types
- Get structured output in multiple formats

## Pipeline Steps

1. **Content Retriever** - Downloads/retrieves documents
2. **Document Type Identifier** - Identifies document types
3. **Azure Document Intelligence Extractor** - Extracts structured content using Azure AI

## Configuration Files

- `pipeline_config.yaml` - Pipeline with Document Intelligence configuration
- `run_pipeline.py` - Python script to execute the pipeline

## Prerequisites

- Copy the .env.example file to .env
- Set the values for following environment variables in the .env file:

```bash
## Settings for service: azure_doc_intelligence_service_01
AZURE_DOCUMENT_INTELLIGENCE_SERVICE_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_SERVICE_CREDENTIAL_TYPE=default_azure_credential  # Valid values are azure_key_credential or default_azure_credential
# If using azure_key_credential, set the API key below
# If using default_azure_credential, this can be left empty
AZURE_DOCUMENT_INTELLIGENCE_SERVICE_API_KEY=
```

## Usage

```bash
# From the doc-proc-lib directory
cd examples/06-azure-document-intelligence
python run_pipeline.py
```

## What This Example Shows

- Using Azure Document Intelligence service
- Extracting structured content (tables, key-value pairs, paragraphs)
- Processing with prebuilt models (layout, document, invoice, etc.)
- Getting multiple output formats (structured, markdown, JSON)
- Handling various document types with a single service
