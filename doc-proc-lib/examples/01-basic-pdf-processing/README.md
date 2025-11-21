# Basic PDF Processing Example

This example demonstrates a simple pipeline that processes PDF documents by:
1. Retrieving content from a source (file path or blob storage)
2. Identifying document type
3. Extracting text from PDF pages using AI services
4. Converting extracted content to markdown format

## Pipeline Steps

1. **Content Retriever** - Downloads/retrieves the document from specified source
2. **Document Type Identifier** - Identifies the document type (PDF, Word, etc.)
3. **AI PDF Text Extractor** - Extracts text from PDF pages using Azure AI Inference Service

## Configuration Files

- `pipeline_config.yaml` - Pipeline configuration with service and step instances
- `run_pipeline.py` - Python script to execute the pipeline

## Prerequisites

- Copy the .env.example file to .env
- Set the values for following environment variables in the .env file:

```bash
# Azure AI Inference Service
AZURE_AI_INFERENCE_SERVICE_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_AI_INFERENCE_SERVICE_CREDENTIAL_TYPE=default_azure_credential # default_azure_credential or azure_key_credential
AZURE_AI_INFERENCE_SERVICE_API_KEY=your-api-key # if using azure_key_credential for the above
```

## Usage

```bash
# From the doc-proc-lib directory
cd examples/01-basic-pdf-processing
python run_pipeline.py
```

## What This Example Shows

- How to instantiate a pipeline from YAML configuration
- How to configure service instances for Azure AI
- How to chain multiple processing steps
- How to execute a pipeline with document input
- How to access pipeline execution results
