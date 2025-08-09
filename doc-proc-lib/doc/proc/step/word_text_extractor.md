# Word Text Extractor Step

The Word Text Extractor Step is a document processing component that extracts text content, tables, and images from Microsoft Word documents (.docx format). It follows the same architectural pattern as other document extractors in the pipeline and provides native text extraction capabilities with optional AI-powered image analysis.

## Features

- **Text Extraction**: Extracts and chunks text from paragraphs in Word documents with configurable chunk size limits
- **Table Extraction**: Extracts and formats table content using pipe separators
- **Image Extraction**: Extracts embedded images from document relationships and saves them as PNG files
- **AI-Powered Image Analysis**: Uses Azure AI Model Inference Service to analyze extracted images and generate markdown descriptions
- **Structured Output**: Organizes extracted content into chunks with metadata and SHA1-based unique identifiers
- **Condition-Based Execution**: Supports conditional processing based on document properties
- **Error Handling**: Comprehensive error handling with configurable fail-fast behavior

## Dependencies

```bash
pip install python-docx
```

## Configuration

The Word Text Extractor Step requires the following configuration:

```yaml
- name: word_text_extractor_1
  step_catalog_id: word_text_extractor
  enabled: true
  fail_pipeline_on_error: true
  retry_on_failure: false
  retries: 3
  timeout: 600
  services: [primary_ai_inference_service]
  condition: "document_type.primary_type == 'word_document'"
  fail_step_on_document_error: true
  debug_mode: false
  settings:
    png_output_folder: "./output/png"
    extract_images: true
    extract_image_descriptions: true
    extract_tables: true
    max_chunk_size: 4000
    prompts:
      system: "You are an AI assistant that helps convert images extracted from a word document to markdown text. Only output valid markdown."
      user: |
        Extract the text from the following image into markdown and provide descriptions of images. If the image has no text, don't output any text, just provide the image description. 
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

## Input Data Structure

The step expects input data in the following format:

```python
{
    "documents": [
        {
            "file_path": "/path/to/document.docx",
            "file_name": "document.docx",
            "file_size": 1024,
            "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "document_type": {
                "primary_type": "word_document"
            }
        }
    ]
}
```

## Output Data Structure

The step adds a `chunks` array to each document with the following structure:

```python
{
    "chunks": [
        {
            "input_file_path": "/path/to/document.docx",
            "chunk_id": "sha1_hash_of_chunk",
            "chunk_type": "paragraph|table|image",
            "chunk_num": 1,
            "text": "Extracted text content",
            "raw_text": "Raw text content",
            "markdown": "AI-generated markdown (for images)",
            "markdown_text": "Extracted text from AI analysis",
            "markdown_image_descriptions": "AI-generated image descriptions",
            "png": "/path/to/extracted/image.png" (for image chunks)
        }
    ]
}
```

## Processing Flow

1. **Input Validation**: Validates input data structure and ensures it contains a list of documents
2. **Service Initialization**: Retrieves Azure AI Model Inference Service from the pipeline context
3. **Document Iteration**: Processes each document in the input list with condition evaluation
4. **Document Validation**: Validates Word document format (.docx/.doc) and file existence
5. **Text Extraction**: Extracts text from paragraphs and organizes into chunks based on `max_chunk_size`
6. **Table Extraction**: Extracts and formats table content using pipe separators (if enabled)
7. **Image Extraction**: Extracts embedded images from document relationships and saves as PNG files (if enabled)
8. **AI Processing**: Processes extracted images using Azure AI Model Inference Service to generate markdown
9. **Structured Output**: Organizes all extracted content into chunks with SHA1-based unique identifiers
10. **Statistics Collection**: Tracks processing statistics for successful, skipped, and failed documents

## Chunk Types

- **paragraph**: Text content from document paragraphs
- **table**: Formatted table content with pipe-separated values
- **image**: Extracted images with AI-generated descriptions and text

## Error Handling

The step includes comprehensive error handling:

- **Input validation**: Validates StepInputOutput format and document structure
- **File existence validation**: Checks if Word documents exist at specified paths
- **Format validation**: Ensures files have proper Word document extensions (.docx/.doc)
- **Import validation**: Handles missing `python-docx` dependency with clear error messages
- **Individual chunk processing**: Logs warnings for chunk-level errors without stopping the pipeline
- **Configurable fail behavior**: Uses `fail_step_on_document_error` setting for document-level error handling
- **Statistical tracking**: Maintains counts of successful, skipped, and failed documents

## Usage Example

```python
from doc.proc.step.word_text_extractor import WordTextExtractorStep
from doc.proc.step.step_base import StepInputOutput, StepInstanceConfig

# Configure the step
instance_config = StepInstanceConfig(
    name="word_text_extractor_1",
    step_catalog_id="word_text_extractor",
    enabled=True,
    services=["primary_ai_inference_service"],
    settings={
        "png_output_folder": "./output/png",
        "extract_images": True,
        "extract_image_descriptions": True,
        "extract_tables": True,
        "max_chunk_size": 4000,
        "prompts": {
            "system": "You are an AI assistant that helps convert images...",
            "user": "Extract the text from the following image..."
        },
        "max_completion_tokens": 4000,
        "temperature": 1.0,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    condition="document_type.primary_type == 'word_document'",
    fail_step_on_document_error=True,
    debug_mode=False
)

# Create step instance
word_extractor = WordTextExtractorStep(instance_config=instance_config)

# Prepare input data
input_data = StepInputOutput(
    data={
        "documents": [
            {
                "file_path": "/path/to/document.docx",
                "document_type": {"primary_type": "word_document"}
            }
        ]
    }
)

# Process documents (requires pipeline context)
# result = await word_extractor.run(input_data, context)
```

## Configuration Settings

### Required Settings

- **prompts.system**: System prompt for AI image processing
- **prompts.user**: User prompt template for AI image processing

### Optional Settings

- **png_output_folder**: Directory path for saving extracted images (default: "output_pngs")
- **extract_images**: Enable image extraction and AI processing (default: true)
- **extract_image_descriptions**: Include AI-generated image descriptions (default: true)
- **extract_tables**: Enable table extraction (default: true)
- **max_chunk_size**: Maximum character count per text chunk (default: 4000)
- **max_completion_tokens**: AI model token limit (default: 4000)
- **temperature**: AI model randomness (default: 1.0)
- **top_p**: AI model nucleus sampling (default: 1.0)
- **frequency_penalty**: AI model frequency penalty (default: 0.0)
- **presence_penalty**: AI model presence penalty (default: 0.0)

## Comparison with PDF Text Extractor

| Feature | PDF Text Extractor | Word Text Extractor |
|---------|-------------------|---------------------|
| Input Format | PDF files | Word documents (.docx/.doc) |
| Processing Method | Page-by-page PNG conversion | Content-based chunking with size limits |
| Text Extraction | AI-powered from page images | Direct text extraction from paragraphs |
| Table Support | AI-powered from page images | Native table extraction with pipe separators |
| Image Support | Page-rendered images | Document relationship-based embedded images |
| Performance | Slower (AI processing for all content) | Faster (direct extraction + optional AI for images) |
| Accuracy | Depends on AI model for all content | High for text/tables, AI-dependent for images |
| Chunking Strategy | Page-based chunks | Size-based text chunking with configurable limits |

## Notes

- **Format Support**: Currently supports `.docx` format primarily, with basic `.doc` support
- **Image Extraction**: Depends on document's internal relationship structure and embedded image format
- **AI Processing**: Optional but recommended for comprehensive image analysis and description generation
- **Table Extraction**: Preserves basic table structure using pipe separators (` | `)
- **Chunk Identification**: Uses SHA1 hashes of content and metadata for consistent chunk identification
- **Text Chunking**: Intelligently splits text into chunks based on `max_chunk_size` while preserving paragraph boundaries
- **Error Resilience**: Individual chunk failures don't stop document processing unless `fail_step_on_document_error` is enabled
- **Condition Support**: Supports conditional execution based on document properties (e.g., document type filtering)

## Dependencies

- **python-docx**: Required for Word document processing
- **Azure AI Inference SDK**: Required for image processing capabilities