# Word Text Extractor Step

The Word Text Extractor Step is a document processing component that extracts text content, tables, and images from Microsoft Word documents (.docx format). It follows the same architectural pattern as the PDF Text Extractor Step.

## Features

- **Text Extraction**: Extracts text from paragraphs in Word documents
- **Table Extraction**: Extracts and formats table content
- **Image Extraction**: Extracts embedded images and processes them with AI
- **AI-Powered Image Analysis**: Uses Azure AI Model Inference Service to analyze extracted images
- **Structured Output**: Organizes extracted content into chunks with metadata

## Dependencies

```bash
pip install python-docx
```

## Configuration

The Word Text Extractor Step requires the following configuration:

```yaml
- id: word_extractor_001
  name: Word Text Extractor
  enabled: true
  description: Extract text and images from Word documents
  tags: [text-extraction, word, document-processing]
  fail_step_on_document_error: false
  debug_mode: true
  services: [azure_ai_inference]
  settings:
    png_output_folder: output_images
    extract_images: true
    extract_tables: true
    prompts:
      system: "You are a document analysis assistant. Extract text and describe images from the provided document page."
      user: "Please extract all text content and describe any images you see in this document page. Format your response with ==Extracted-Text== and ==End-Extracted-Text== tags around the text, and ==Image-Descriptions== and ==End-Image-Descriptions== tags around image descriptions."
    max_completion_tokens: 4000
    temperature: 0.1
    top_p: 0.9
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
            "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
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

1. **Document Validation**: Validates input Word document format and existence
2. **Text Extraction**: Extracts text from all paragraphs
3. **Table Extraction**: Extracts and formats table content (if enabled)
4. **Image Extraction**: Extracts embedded images and saves as PNG files (if enabled)
5. **AI Processing**: Processes extracted images using Azure AI Model Inference Service
6. **Structured Output**: Organizes all extracted content into chunks with metadata

## Chunk Types

- **paragraph**: Text content from document paragraphs
- **table**: Formatted table content with pipe-separated values
- **image**: Extracted images with AI-generated descriptions and text

## Error Handling

The step includes comprehensive error handling:

- File existence validation
- Format validation (Word document check)
- Individual chunk processing errors (logged as warnings)
- Optional fail-fast behavior for document errors

## Usage Example

```python
from doc.proc.step.word_text_extractor import WordTextExtractorStep
from doc.proc.step.step_base import StepInputOutput

# Configure the step
config = {
    "id": "word_extractor_001",
    "name": "Word Text Extractor",
    "enabled": True,
    "services": ["azure_ai_inference"],
    "settings": {
        "png_output_folder": "output_images",
        "extract_images": True,
        "extract_tables": True,
        "prompts": {
            "system": "You are a document analysis assistant...",
            "user": "Please extract all text content..."
        }
    }
}

# Create step instance
word_extractor = WordTextExtractorStep(**config)

# Prepare input data
input_data = StepInputOutput(
    data={
        "documents": [
            {"file_path": "/path/to/document.docx"}
        ]
    }
)

# Process documents (requires pipeline context)
# result = await word_extractor.run(input_data, context)
```

## Comparison with PDF Text Extractor

| Feature | PDF Text Extractor | Word Text Extractor |
|---------|-------------------|---------------------|
| Input Format | PDF files | Word documents (.docx) |
| Page Processing | Page-by-page PNG conversion | Content-based chunking |
| Text Extraction | AI-powered from images | Direct text extraction |
| Table Support | AI-powered from images | Native table extraction |
| Image Support | Page images | Embedded images |
| Performance | Slower (AI processing) | Faster (direct extraction) |
| Accuracy | Depends on AI model | High for text, AI for images |

## Notes

- Currently supports `.docx` format only (not legacy `.doc` format)
- Image extraction depends on the document's internal structure
- AI processing is optional but recommended for comprehensive image analysis
- Table extraction preserves basic structure using pipe separators
- Generated chunk IDs are SHA1 hashes for consistent identification
