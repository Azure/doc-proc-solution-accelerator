# AI Word Text Extractor Step

The AI Word Text Extractor Step (`AIWordTextExtractorStep`) is a document processing component that extracts text content, tables, and images from Microsoft Word documents (.docx and .doc formats). It follows the same architectural pattern as other document extractors in the pipeline and provides native text extraction capabilities with AI-powered image analysis using Azure AI Inference Service.

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
  step_catalog_id: ai_word_text_extractor
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
    output_field_name: "chunks"
    png_output_folder: "./tmp/docproc/word_output/png"
    extract_images: true
    extract_image_desacriptions: true
    extract_tables: true
    max_chunk_size: 4000
    system_prompt: "You are an AI assistant that helps convert images from pages from a word document to markdown text. Only output valid markdown."
    user_prompt: "Extract the text from the following image into markdown and provide descriptions of images. Always format the markdown as follows to distinguish the text extracted from image descriptions:\n==Extracted-Text==\n{Insert extracted text as markdown here}==End-Extracted-Text==\n\n==Image-Descriptions==\n{Insert image descriptions as markdown here}==End-Image-Descriptions=="
    max_completion_tokens: 4000
    temperature: 1.0
    top_p: 0.4
    frequency_penalty: 0.0
    presence_penalty: 0.0
```

## Input Data Structure

The step expects a `Document` instance with the following data structure:

```python
{
    "temp_file_path": "/path/to/document.docx"
}
```

**Required Fields:**
- `temp_file_path`: Path to the Word document file (.docx or .doc format)

## Output Data Structure

The step adds the specified output field (default: `chunks`) to the document data with the following structure:

```python
{
    "chunks": [
        {
            "input_file_path": "/path/to/document.docx",
            "chunk_id": "sha1_hash_of_chunk", 
            "chunk_type": "paragraph|table|image",
            "chunk_num": 1,
            "markdown_text": "Extracted text content",
            "raw_text": "Raw text content",
            "text": "Combined text and descriptions (for images)",
            "markdown": "AI-generated markdown (for images)",
            "markdown_image_descriptions": "AI-generated image descriptions (for images)",
            "png": "/path/to/extracted/image.png"  # Only for image chunks
        }
    ]
}
```

## Processing Flow

1. **Input Validation**: Validates Document instance and ensures it contains the required `temp_file_path` field
2. **Service Initialization**: Retrieves Azure AI Model Inference Service from the pipeline context
3. **File Validation**: Validates Word document format (.docx/.doc) and file existence
4. **Text Extraction**: Extracts text from paragraphs and organizes into chunks based on `max_chunk_size`
5. **Table Extraction**: Extracts and formats table content using pipe separators (if enabled)
6. **Image Extraction**: Extracts embedded images from document relationships and saves as PNG files (if enabled)
7. **AI Processing**: Processes extracted images using Azure AI Model Inference Service to generate markdown descriptions (if enabled)
8. **Content Organization**: Organizes all extracted content into chunks with SHA1-based unique identifiers
9. **Output Update**: Adds the processed chunks to the document data using the specified output field name

## Chunk Types

- **paragraph**: Text content from document paragraphs
- **table**: Formatted table content with pipe-separated values
- **image**: Extracted images with AI-generated descriptions and text

## Error Handling

The step includes comprehensive error handling:

- **Input validation**: Validates Document instance and data structure
- **Required field validation**: Ensures `temp_file_path` field is present
- **File existence validation**: Checks if Word document exists at specified path
- **Format validation**: Ensures file has proper Word document extension (.docx/.doc)
- **Import validation**: Handles missing `python-docx` dependency with clear error messages
- **Document processing errors**: Catches and handles Word document loading errors
- **Image extraction failures**: Logs warnings for failed image extractions but continues processing
- **AI processing failures**: Logs warnings for failed AI image analysis but continues processing

## Usage Example

```python
from doc.proc.step.ai_word_text_extractor import AIWordTextExtractorStep
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import Document

# Configure the step
instance_config = StepInstanceConfig(
    name="word_text_extractor_1",
    step_catalog_id="ai_word_text_extractor",
    enabled=True,
    services=["primary_ai_inference_service"],
    settings={
        "output_field_name": "chunks",
        "png_output_folder": "./tmp/docproc/word_output/png",
        "extract_images": True,
        "extract_image_desacriptions": True,
        "extract_tables": True,
        "max_chunk_size": 4000,
        "system_prompt": "You are an AI assistant that helps convert images from pages from a word document to markdown text. Only output valid markdown.",
        "user_prompt": "Extract the text from the following image into markdown and provide descriptions of images. Always format the markdown as follows to distinguish the text extracted from image descriptions:\n==Extracted-Text==\n{Insert extracted text as markdown here}==End-Extracted-Text==\n\n==Image-Descriptions==\n{Insert image descriptions as markdown here}==End-Image-Descriptions==",
        "max_completion_tokens": 4000,
        "temperature": 1.0,
        "top_p": 0.4,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    condition="document_type.primary_type == 'word_document'",
    fail_step_on_document_error=True,
    debug_mode=False
)

# Create step instance
word_extractor = AIWordTextExtractorStep(instance_config=instance_config)

# Prepare input document
document = Document(
    id="doc_1",
    data={"temp_file_path": "/path/to/document.docx"}
)

# Process document (requires pipeline context)
# result = await word_extractor.run(document, context)
```

## Configuration Settings

### Required Settings

- **`output_field_name`** (string): Field name in document data dict to store the extracted content (default: `"chunks"`)
- **`system_prompt`** (string): Instructions for the AI system to process images from word document pages (default: `"You are an AI assistant that helps convert images from pages from a word document to markdown text. Only output valid markdown."`)
- **`user_prompt`** (string): Template for user prompts sent to AI to process images from word document pages

### Optional Settings

- **`png_output_folder`** (string): Directory path where PNG files will be saved (default: `"./tmp/docproc/word_output/png"`)
- **`extract_images`** (boolean): Whether to extract text from images in pages (default: `true`)
- **`extract_image_desacriptions`** (boolean): Whether to extract descriptions from images in pages. Uses AI to generate descriptions (default: `true`)
- **`extract_tables`** (boolean): Whether to extract tables from pages (default: `true`)
- **`max_chunk_size`** (integer): Maximum number of chars per chunk (default: `4000`)
- **`max_completion_tokens`** (integer): Maximum number of tokens to generate (default: `4000`)
- **`temperature`** (number): Controls randomness in AI responses (0.0 = deterministic, 2.0 = very random) (default: `1.0`)
- **`top_p`** (number): Controls diversity of AI responses (default: `0.4`)
- **`frequency_penalty`** (number): Reduces repetition in AI responses (default: `0.0`)
- **`presence_penalty`** (number): Encourages AI to talk about new topics (default: `0.0`)


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