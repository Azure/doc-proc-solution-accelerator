# Conditional Step Execution Example

This example demonstrates advanced pipeline orchestration with conditional step execution based on document properties:
- Document type conditions
- File size conditions
- Metadata-based conditions
- Combined logical conditions

## Pipeline Steps

1. **Content Retriever** - Downloads/retrieves documents
2. **Document Type Identifier** - Identifies document types
3. **PDF Extractor** - Only processes PDF files (conditional)
4. **Word Extractor** - Only processes Word files (conditional)
5. **Large File Handler** - Only processes files > 1MB (conditional)
6. **High Priority Handler** - Only processes high-priority docs (conditional)

## Configuration Files

- `pipeline_config.yaml` - Pipeline with multiple conditional steps
- `run_pipeline.py` - Python script demonstrating conditional execution

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
cd examples/05-conditional-execution
python run_pipeline.py
```

## What This Example Shows

- Configuring step conditions based on document properties
- Using document type conditions
- Using file size and metadata conditions
- Combining multiple conditions with logical operators
- Skipping steps that don't meet conditions
- Viewing which steps executed for each document
