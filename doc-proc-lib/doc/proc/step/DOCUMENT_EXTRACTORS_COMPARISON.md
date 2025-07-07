# Document Text Extractors Comparison

This document provides a comprehensive comparison of the three document text extractor steps: PDF, Word, and PowerPoint extractors.

## Overview

All three extractors follow the same architectural pattern and share common base functionality while being optimized for their specific document formats.

## Common Features

### Shared Architecture
- Inherit from `StepBase` class
- Use `StepInputOutput` for data flow
- Integrate with Azure AI Model Inference Service
- Support configurable prompts and AI settings
- Include comprehensive error handling
- Generate SHA1 hash-based chunk IDs

### Common Settings
- `png_output_folder`: Output directory for extracted images
- `prompts`: System and user prompts for AI processing
- `max_completion_tokens`: AI response token limit
- `temperature`: AI model temperature
- `top_p`: AI model top-p sampling
- `frequency_penalty`: AI model frequency penalty
- `presence_penalty`: AI model presence penalty

### Common Methods
- `get_ai_inference_service()`: Retrieve AI service from context
- `generate_sha1_hash()`: Generate unique chunk identifiers
- `convert_png_to_base64()`: Convert images to base64
- `convert_png_to_markdown()`: AI-powered image analysis
- `extract_text_section()`: Parse AI-generated text sections
- `extract_image_sections()`: Parse AI-generated image descriptions

## Feature Comparison

| Feature | PDF Extractor | Word Extractor | PowerPoint Extractor |
|---------|---------------|----------------|---------------------|
| **Input Format** | `.pdf` | `.docx`, `.doc` | `.pptx`, `.ppt` |
| **Processing Unit** | Pages | Content blocks | Slides |
| **Text Extraction Method** | AI-powered (OCR) | Direct text access | Direct text access |
| **Primary Use Case** | Scanned documents, images | Structured documents | Presentations |
| **Processing Speed** | Slower (AI required) | Faster (direct access) | Faster (direct access) |
| **Text Accuracy** | AI-dependent | Very high | Very high |
| **Image Support** | Page screenshots | Embedded images | Slide images |
| **Table Support** | AI-powered | Native extraction | Native extraction |
| **Structure Preservation** | Page-based | Content-based | Slide-based |

## Settings Comparison

### PDF Extractor Specific
```yaml
settings:
  png_output_folder: "output_pngs"
  num_pages: -1  # Number of pages to process
```

### Word Extractor Specific
```yaml
settings:
  png_output_folder: "output_pngs"
  extract_images: true
  extract_tables: true
```

### PowerPoint Extractor Specific
```yaml
settings:
  png_output_folder: "output_pngs"
  extract_images: true
  extract_tables: true
  extract_shapes: true
  num_slides: -1  # Number of slides to process
```

## Output Structure Comparison

### PDF Extractor Output
```python
{
    "chunks": [
        {
            "input_file_path": "/path/to/document.pdf",
            "page_id": "sha1_hash",
            "page_num": 1,
            "png": "/path/to/page_1.png",
            "markdown": "AI-generated content",
            "markdown_text": "Extracted text",
            "markdown_image_descriptions": "Image descriptions"
        }
    ]
}
```

### Word Extractor Output
```python
{
    "chunks": [
        {
            "input_file_path": "/path/to/document.docx",
            "chunk_id": "sha1_hash",
            "chunk_type": "paragraph|table|image",
            "chunk_num": 1,
            "text": "Extracted text",
            "raw_text": "Raw text",
            "markdown": "AI-generated content (for images)",
            "png": "/path/to/image.png" (for images)
        }
    ]
}
```

### PowerPoint Extractor Output
```python
{
    "chunks": [
        {
            "input_file_path": "/path/to/presentation.pptx",
            "chunk_id": "sha1_hash",
            "chunk_type": "slide_text|table|image",
            "chunk_num": 1,
            "slide_number": 1,
            "text": "Extracted text",
            "raw_text": "Raw text",
            "markdown": "AI-generated content (for images)",
            "png": "/path/to/image.png" (for images),
            "table_index": 1 (for tables),
            "image_index": 1 (for images)
        }
    ]
}
```

## Processing Flow Comparison

### PDF Extractor Flow
1. **PDF → PNG Conversion**: Convert each page to PNG image
2. **AI Processing**: Analyze each PNG with AI model
3. **Content Extraction**: Extract text and image descriptions
4. **Chunk Creation**: Create page-based chunks

### Word Extractor Flow
1. **Direct Text Extraction**: Extract text from paragraphs
2. **Table Processing**: Extract tables with native APIs
3. **Image Extraction**: Extract embedded images
4. **AI Processing**: Analyze extracted images (optional)
5. **Chunk Creation**: Create content-based chunks

### PowerPoint Extractor Flow
1. **Slide Iteration**: Process each slide sequentially
2. **Text Extraction**: Extract text from slide shapes
3. **Table Processing**: Extract tables with native APIs
4. **Image Extraction**: Extract slide images
5. **AI Processing**: Analyze extracted images (optional)
6. **Chunk Creation**: Create slide-based chunks

## Performance Characteristics

### PDF Extractor
- **Pros**: Handles any PDF content, including scanned documents
- **Cons**: Slower due to AI processing requirement
- **Best For**: Scanned documents, image-heavy PDFs, legacy documents

### Word Extractor
- **Pros**: Fast, accurate text extraction, native structure access
- **Cons**: Limited to modern Word formats
- **Best For**: Structured documents, reports, manuscripts

### PowerPoint Extractor
- **Pros**: Preserves slide context, handles presentation structure
- **Cons**: Limited to modern PowerPoint formats
- **Best For**: Presentations, slide-based content, visual documents

## Use Case Recommendations

### Choose PDF Extractor When:
- Processing scanned documents or image-based PDFs
- Dealing with legacy or unknown document sources
- Need to extract text from images and graphics
- Working with documents that don't have structured text

### Choose Word Extractor When:
- Processing structured text documents
- Need fast, accurate text extraction
- Working with reports, manuscripts, or documentation
- Require native table structure preservation

### Choose PowerPoint Extractor When:
- Processing presentations or slide-based content
- Need to maintain slide context and structure
- Working with educational or business presentation materials
- Require slide-by-slide content organization

## Integration Example

```python
# Example: Processing different document types in a pipeline
from doc.proc.step.pdf_text_extractor import PDFTextExtractorStep
from doc.proc.step.word_text_extractor import WordTextExtractorStep
from doc.proc.step.pptx_text_extractor import PowerPointTextExtractorStep

# Configure extractors based on file type
def get_extractor_for_file(file_path):
    if file_path.lower().endswith('.pdf'):
        return PDFTextExtractorStep(**pdf_config)
    elif file_path.lower().endswith(('.docx', '.doc')):
        return WordTextExtractorStep(**word_config)
    elif file_path.lower().endswith(('.pptx', '.ppt')):
        return PowerPointTextExtractorStep(**pptx_config)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

# Process documents based on type
async def process_documents(documents, context):
    for document in documents:
        extractor = get_extractor_for_file(document['file_path'])
        result = await extractor.run(input_data, context)
        # Process result...
```

## Dependencies Summary

```bash
# PDF Extractor
pip install PyMuPDF==1.26.1

# Word Extractor
pip install python-docx==1.1.2

# PowerPoint Extractor
pip install python-pptx==1.0.2

# Common dependencies
pip install azure-ai-inference==1.0.0b9
pip install azure-core==1.34.0
pip install azure-identity==1.23.0
```

## Future Enhancements

### Common Improvements
- Enhanced error recovery and retry logic
- Configurable output formats
- Batch processing optimization
- Memory usage optimization

### Format-Specific Enhancements
- **PDF**: Support for PDF forms and annotations
- **Word**: Support for comments and tracked changes
- **PowerPoint**: Support for slide notes and animations

## Conclusion

Each extractor is optimized for its specific document format while maintaining architectural consistency. Choose the appropriate extractor based on your document types and processing requirements:

- **PDF Extractor**: Best for scanned or image-based documents
- **Word Extractor**: Best for structured text documents
- **PowerPoint Extractor**: Best for presentation and slide-based content

All extractors can be used together in a comprehensive document processing pipeline to handle diverse document types with optimal performance and accuracy.
