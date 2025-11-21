# Custom AI Prompt Processing Example

This example demonstrates using custom AI prompts to perform specialized document analysis such as:
- Document summarization
- Sentiment analysis
- Entity extraction
- Question answering
- Custom transformations

## Pipeline Steps

1. **Content Retriever** - Downloads/retrieves documents
2. **Document Type Identifier** - Identifies document types
3. **AI PDF Text Extractor** - Extracts text from PDFs
4. **Custom AI Prompt Step** - Applies custom AI analysis to extracted content

## Configuration Files

- `pipeline_config.yaml` - Pipeline with custom AI prompt configuration
- `run_pipeline.py` - Python script to execute the pipeline

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
cd examples/04-custom-ai-prompts
python run_pipeline.py
```

## What This Example Shows

- Configuring custom AI prompts for document analysis
- Applying specialized AI processing to extracted content
- Generating summaries, sentiment analysis, or custom insights
- Chaining multiple AI processing steps
- Accessing custom AI results in pipeline output
