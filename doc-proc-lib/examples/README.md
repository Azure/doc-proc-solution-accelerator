# Doc-Proc-Lib Pipeline Examples

This directory contains comprehensive examples demonstrating how to use the doc-proc-lib document processing pipeline library. Each example is self-contained with its own configuration files and Python scripts.

## Overview

The doc-proc-lib library enables you to build flexible, modular document processing pipelines by:
- Configuring pipelines using YAML files
- Chaining multiple processing steps
- Using Azure AI services for document analysis
- Applying conditional logic to steps
- Processing multiple document formats

## Examples

### 1. [Basic PDF Processing](./01-basic-pdf-processing/README.md)
**Location:** `01-basic-pdf-processing/`

A simple pipeline demonstrating PDF text extraction using Azure AI services.

**Key Features:**
- Content retrieval from files or blob storage
- Document type identification
- AI-powered text extraction from PDF pages
- Markdown output generation

**Use Case:** Extract text content from PDF documents for further processing.

---

### 2. [Multi-Format Document Processing](./02-multi-format-processing/README.md)
**Location:** `02-multi-format-processing/`

Comprehensive pipeline handling multiple document formats (PDF, Word, PowerPoint, Excel).

**Key Features:**
- Format-specific extractors for each document type
- Conditional step execution based on document type
- Batch processing of mixed formats
- Format-appropriate handling (tables in Excel, slides in PPTX, etc.)

**Use Case:** Process a variety of document types in a single pipeline run.

---

### 3. [AI Search Indexing](./03-ai-search-indexing/README.md)
**Location:** `03-ai-search-indexing/`

End-to-end pipeline that extracts document content and writes it to Azure AI Search for searchable storage.

**Key Features:**
- Document content extraction
- Azure AI Search integration
- Custom field mappings for search index
- Batch indexing of document chunks

**Use Case:** Make documents searchable by indexing extracted content.

---

### 4. [Custom AI Prompts](./04-custom-ai-prompts/README.md)
**Location:** `04-custom-ai-prompts/`

Advanced pipeline demonstrating custom AI analysis including summarization, sentiment analysis, and topic extraction.

**Key Features:**
- Custom AI prompts for specialized analysis
- Document summarization
- Sentiment and tone analysis
- Topic and entity extraction
- Chained AI processing steps

**Use Case:** Perform sophisticated AI-driven document analysis beyond simple extraction.

---

### 5. [Conditional Step Execution](./05-conditional-execution/README.md)
**Location:** `05-conditional-execution/`

Advanced orchestration example showing how to use conditions to control step execution.

**Key Features:**
- Document type-based conditions
- File size conditions
- Metadata-based conditions
- Combined logical conditions
- Step execution tracking

**Use Case:** Build intelligent pipelines that adapt processing based on document properties.

---

### 6. [Azure Document Intelligence](./06-azure-document-intelligence/README.md)
**Location:** `06-azure-document-intelligence/`

Pipeline using Azure Document Intelligence service for structured document extraction.

**Key Features:**
- Prebuilt models (layout, invoice, receipt, business card)
- Table extraction
- Key-value pair extraction
- Multiple output formats (structured, markdown, JSON)

**Use Case:** Extract structured data from documents using Azure's specialized models.

---

## Getting Started

### Prerequisites

1. **Python Environment**
   - Python 3.8 or higher
   - Install doc-proc-lib dependencies (see main README)

2. **Azure Services** (depending on the example)
   - Azure AI Inference Service (for AI-powered extraction)
   - Azure Document Intelligence (for structured extraction)
   - Azure AI Search (for indexing examples)
   - Azure Blob Storage (optional, for blob source examples)

3. **Environment Variables**
   
   Set the required environment variables for the services you'll use:
   
   ```bash
   # Azure AI Inference
   export AZURE_AI_INFERENCE_SERVICE_ENDPOINT="https://your-endpoint.openai.azure.com/"
   export AZURE_AI_INFERENCE_SERVICE_CREDENTIAL_TYPE="azure_key_credential"
   export AZURE_AI_INFERENCE_SERVICE_API_KEY="your-api-key"
   
   # Azure Document Intelligence
   export AZURE_DOCUMENT_INTELLIGENCE_SERVICE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
   export AZURE_DOCUMENT_INTELLIGENCE_SERVICE_CREDENTIAL_TYPE="azure_key_credential"
   export AZURE_DOCUMENT_INTELLIGENCE_SERVICE_API_KEY="your-api-key"
   
   # Azure AI Search
   export AZURE_AI_SEARCH_SERVICE_ACCOUNT_NAME="your-search-service"
   export AZURE_AI_SEARCH_SERVICE_CREDENTIAL_TYPE="azure_key_credential"
   export AZURE_AI_SEARCH_SERVICE_API_KEY="your-search-api-key"
   ```

### Running an Example

1. Navigate to the example directory:
   ```bash
   cd examples/01-basic-pdf-processing
   ```

2. Review the README.md in that directory for specific instructions

3. Update the document paths in `run_pipeline.py` to point to your test files

4. Run the pipeline:
   ```bash
   python run_pipeline.py
   ```

5. Check the output:
   - Console output shows execution progress and results
   - JSON results file contains detailed execution data

## Example Structure

Each example follows a consistent structure:

```
example-folder/
├── README.md              # Example-specific documentation
├── pipeline_config.yaml   # Pipeline and step configuration
├── run_pipeline.py        # Python script to execute the pipeline
└── *_results.json        # Generated results (after execution)
```

## Key Concepts Demonstrated

### Pipeline Configuration
All examples use YAML configuration files that define:
- **Service Instances**: Configured Azure services
- **Pipeline Steps**: Ordered sequence of processing steps
- **Step Settings**: Configuration for each step
- **Conditions**: Optional conditions for step execution

### Pipeline Execution
The Python scripts demonstrate:
- Loading pipelines from configuration files
- Creating document inputs
- Executing pipelines asynchronously
- Processing results
- Error handling

### Available Steps

The examples use these step types from the catalog:

- `content_retriever` - Download/retrieve documents
- `document_type_identifier` - Identify document formats
- `ai_pdf_text_extractor` - Extract text from PDFs
- `ai_word_text_extractor` - Extract text from Word documents
- `ai_pptx_text_extractor` - Extract text from PowerPoint
- `excel_text_extractor` - Extract data from Excel
- `azure_document_intelligence_extractor` - Structured extraction
- `custom_ai_prompt` - Apply custom AI analysis
- `ai_search_index_writer` - Write to search index

## Customization

### Modifying Examples

1. **Change Document Paths**: Update file paths in `run_pipeline.py`

2. **Adjust Step Settings**: Modify settings in `pipeline_config.yaml`
   - AI prompts
   - Number of pages to process
   - Output formats
   - Extraction options

3. **Add/Remove Steps**: Edit the `steps` section in `pipeline_config.yaml`

4. **Add Conditions**: Use the `condition` field to control step execution

### Creating New Examples

1. Copy an existing example as a template
2. Modify the `pipeline_config.yaml` to use different steps
3. Update `run_pipeline.py` with your document inputs
4. Test and document your example

## Common Patterns

### Document Input
```python
documents = [
    Document(
        id=ContentIdentifier(
                        canonical_id="doc_pdf_001",
                        unique_id="doc_pdf_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.pdf",
                    ),
        data={
            "source": "local",
            "metadata": {"key": "value"}
        }
    )
]
```

### Pipeline Execution
```python
pipeline = await create_pipeline_from_files(
    pipeline_name='your_pipeline_name',
    pipeline_config_path=str(pipeline_config_path),
    step_catalog_path=str(step_catalog_path),
    service_catalog_path=str(service_catalog_path)
)

result = await pipeline.run(input_data=PipelineInput(documents=documents))
```

### Accessing Results
```python
for doc_result in result.document_results:
    # Access extracted data
    if "chunks" in doc_result.data:
        chunks = doc_result.data["chunks"]
        # Process chunks...
    
    # Check step execution
    for step_result in doc_result.step_results:
        print(f"{step_result.step_name}: {step_result.result}")
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Ensure all required environment variables are set
   - Check variable names match the configuration

2. **File Not Found**
   - Update document paths in `run_pipeline.py`
   - Use absolute paths or ensure relative paths are correct

3. **Service Connection Errors**
   - Verify Azure service endpoints and credentials
   - Check network connectivity
   - Ensure service quotas aren't exceeded

4. **Step Execution Skipped**
   - Check step conditions in the configuration
   - Verify document properties match condition requirements

### Debug Mode

Enable debug mode for a step in `pipeline_config.yaml`:
```yaml
steps:
  - name: my_step
    debug_mode: true  # Enable detailed logging
```

## Additional Resources

- **Main Documentation**: See the root doc-proc-lib README.md
- **Step Catalog**: Review `step_catalog.yaml` for all available steps
- **Service Catalog**: Review `service_catalog.yaml` for service configurations
- **API Documentation**: Check the doc-proc-lib source code for detailed API docs

## Contributing

To contribute new examples:

1. Create a new directory following the naming pattern
2. Include all required files (README, config, script)
3. Document the example thoroughly
4. Test with sample documents
5. Submit a pull request

## License

These examples are part of the doc-proc-solution-accelerator project and follow the same license.
