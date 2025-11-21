# Multi-Format Document Processing Example

This example demonstrates a comprehensive pipeline that can process multiple document formats:
- PDF documents
- Word documents (.docx)
- PowerPoint presentations (.pptx)
- Excel spreadsheets (.xlsx)

## Pipeline Steps

1. **Content Retriever** - Downloads/retrieves documents from sources
2. **Document Type Identifier** - Identifies the document format
3. **AI PDF Text Extractor** - Extracts text from PDF files
4. **AI Word Text Extractor** - Extracts text from Word documents
5. **AI PowerPoint Text Extractor** - Extracts text from presentations
6. **Excel Text Extractor** - Extracts data from spreadsheets

Each extractor step is configured with conditional execution to only process its specific document type.

## Configuration Files

- `pipeline_config.yaml` - Pipeline configuration with conditional step execution
- `run_pipeline.py` - Python script to execute the pipeline with multiple documents

## Prerequisites

- Copy the .env.example file to .env
- Set the values for following environment variables in the .env file:

```bash
# Azure AI Inference Service
AZURE_AI_INFERENCE_SERVICE_ENDPOINT=https://<ai-foundry-service>.cognitiveservices.azure.com/openai/deployments/<deployment-name>
AZURE_AI_INFERENCE_SERVICE_CREDENTIAL_TYPE=default_azure_credential # default_azure_credential or azure_key_credential
AZURE_AI_INFERENCE_SERVICE_API_KEY=your-api-key # if using azure_key_credential for the above
```

## Usage

```bash
# From the doc-proc-lib directory
cd examples/02-multi-format-processing
python run_pipeline.py
```

## What This Example Shows

- Processing multiple document formats in a single pipeline
- Using conditional execution based on document type
- Configuring format-specific extractors
- Batch processing of mixed document types
- Handling different output structures per format
