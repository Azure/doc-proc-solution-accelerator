# AI Search Indexing Example

This example demonstrates a complete document processing and indexing pipeline that:
1. Retrieves documents from sources
2. Extracts text content using AI services
3. Writes extracted content to Azure AI Search index for searchable storage

## Pipeline Steps

1. **Content Retriever** - Downloads/retrieves documents
2. **Document Type Identifier** - Identifies document types
3. **AI PDF Text Extractor** - Extracts text from PDFs
4. **AI Search Index Writer** - Writes extracted content to Azure AI Search

## Configuration Files

- `pipeline_config.yaml` - Pipeline configuration with search indexing
- `run_pipeline.py` - Python script to execute the pipeline

## Prerequisites

Set the following environment variables:

```bash
# Azure AI Inference Service
export AZURE_AI_INFERENCE_SERVICE_ENDPOINT="https://your-endpoint.openai.azure.com/"
export AZURE_AI_INFERENCE_SERVICE_CREDENTIAL_TYPE="azure_key_credential"
export AZURE_AI_INFERENCE_SERVICE_API_KEY="your-api-key"

# Azure AI Search Service
export AZURE_AI_SEARCH_SERVICE_ACCOUNT_NAME="your-search-service"
export AZURE_AI_SEARCH_SERVICE_CREDENTIAL_TYPE="azure_key_credential"
export AZURE_AI_SEARCH_SERVICE_API_KEY="your-search-api-key"
```

## Usage

```bash
# From the doc-proc-lib directory
cd examples/03-ai-search-indexing
python run_pipeline.py
```

## What This Example Shows

- End-to-end document processing with searchable output
- Configuring Azure AI Search service integration
- Custom field mappings for search index
- Writing processed document chunks to search index
- Making documents searchable and discoverable
