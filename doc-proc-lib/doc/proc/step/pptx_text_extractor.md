# PowerPoint Text Extractor Step

The PowerPoint Text Extractor Step is a document processing component that extracts text content, tables, and images from Microsoft PowerPoint presentations (.pptx format). It follows the same architectural pattern as the PDF and Word Text Extractor Steps.

## Features

- **Slide Text Extraction**: Extracts text from all text shapes in PowerPoint slides
- **Table Extraction**: Extracts and formats table content from slides
- **Image Extraction**: Extracts embedded images from slides and processes them with AI
- **Shape Processing**: Handles various PowerPoint shape types and content
- **AI-Powered Image Analysis**: Uses Azure AI Model Inference Service to analyze extracted images
- **Slide-by-Slide Processing**: Organizes content by slide number for better context
- **Structured Output**: Organizes extracted content into chunks with metadata

## Dependencies

```bash
pip install python-pptx
```

## Configuration

The PowerPoint Text Extractor Step requires the following configuration:

```yaml
- id: pptx_extractor_001
  name: PowerPoint Text Extractor
  enabled: true
  description: Extract text and images from PowerPoint documents
  tags: [text-extraction, powerpoint, presentation, document-processing]
  fail_step_on_document_error: false
  debug_mode: true
  services: [azure_ai_inference]
  settings:
    png_output_folder: output_images
    extract_images: true
    extract_tables: true
    extract_shapes: true
    num_slides: -1  # -1 means all slides
    prompts:
      system: "You are a presentation analysis assistant. Extract text and describe images from the provided presentation slide."
      user: "Please extract all text content and describe any images you see in this presentation slide. Format your response with ==Extracted-Text== and ==End-Extracted-Text== tags around the text, and ==Image-Descriptions== and ==End-Image-Descriptions== tags around image descriptions."
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
            "file_path": "/path/to/presentation.pptx",
            "file_name": "presentation.pptx",
            "file_size": 2048,
            "file_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
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
            "input_file_path": "/path/to/presentation.pptx",
            "chunk_id": "sha1_hash_of_chunk",
            "chunk_type": "slide_text|table|image",
            "chunk_num": 1,
            "slide_number": 1,
            "text": "Extracted text content",
            "raw_text": "Raw text content",
            "markdown": "AI-generated markdown (for images)",
            "markdown_text": "Extracted text from AI analysis",
            "markdown_image_descriptions": "AI-generated image descriptions",
            "png": "/path/to/extracted/image.png" (for image chunks),
            "table_index": 1 (for table chunks),
            "image_index": 1 (for image chunks)
        }
    ]
}
```

## Processing Flow

1. **Document Validation**: Validates input PowerPoint document format and existence
2. **Slide Iteration**: Processes each slide in the presentation
3. **Text Extraction**: Extracts text from all text shapes in each slide
4. **Table Extraction**: Extracts and formats table content (if enabled)
5. **Image Extraction**: Extracts embedded images and saves as PNG files (if enabled)
6. **AI Processing**: Processes extracted images using Azure AI Model Inference Service
7. **Structured Output**: Organizes all extracted content into chunks with slide context

## Chunk Types

- **slide_text**: Text content from slide shapes (titles, body text, etc.)
- **table**: Formatted table content with pipe-separated values
- **image**: Extracted images with AI-generated descriptions and text

## Shape Processing

The extractor handles various PowerPoint shape types:

- **Text Shapes**: Title placeholders, content placeholders, text boxes
- **Table Shapes**: Native PowerPoint tables
- **Picture Shapes**: Embedded images and photos
- **Group Shapes**: Grouped elements (processed recursively)

## Settings Configuration

### Core Settings
- `png_output_folder`: Directory for saving extracted images
- `extract_images`: Enable/disable image extraction
- `extract_tables`: Enable/disable table extraction
- `extract_shapes`: Enable/disable shape processing
- `num_slides`: Number of slides to process (-1 for all)

### AI Processing Settings
- `max_completion_tokens`: Maximum tokens for AI responses
- `temperature`: AI model temperature (0.0-1.0)
- `top_p`: AI model top-p sampling
- `frequency_penalty`: AI model frequency penalty
- `presence_penalty`: AI model presence penalty

## Error Handling

The step includes comprehensive error handling:

- File existence validation
- Format validation (PowerPoint document check)
- Slide processing errors (logged as warnings)
- Individual shape processing errors (logged as warnings)
- Optional fail-fast behavior for document errors

## Usage Example

```python
from doc.proc.step.pptx_text_extractor import PowerPointTextExtractorStep
from doc.proc.step.step_base import StepInputOutput

# Configure the step
config = {
    "id": "pptx_extractor_001",
    "name": "PowerPoint Text Extractor",
    "enabled": True,
    "services": ["azure_ai_inference"],
    "settings": {
        "png_output_folder": "output_images",
        "extract_images": True,
        "extract_tables": True,
        "extract_shapes": True,
        "num_slides": -1,
        "prompts": {
            "system": "You are a presentation analysis assistant...",
            "user": "Please extract all text content..."
        }
    }
}

# Create step instance
pptx_extractor = PowerPointTextExtractorStep(**config)

# Prepare input data
input_data = StepInputOutput(
    data={
        "documents": [
            {"file_path": "/path/to/presentation.pptx"}
        ]
    }
)

# Process documents (requires pipeline context)
# result = await pptx_extractor.run(input_data, context)
```

## Comparison with Other Text Extractors

| Feature | PDF Extractor | Word Extractor | PowerPoint Extractor |
|---------|---------------|----------------|---------------------|
| **Input Format** | PDF files | Word documents (.docx) | PowerPoint presentations (.pptx) |
| **Processing Unit** | Pages | Content blocks | Slides |
| **Text Extraction** | AI-powered from images | Direct text extraction | Direct text extraction |
| **Table Support** | AI-powered from images | Native table extraction | Native table extraction |
| **Image Support** | Page images | Embedded images | Slide images |
| **Structure** | Page-based | Content-based | Slide-based |
| **Performance** | Slower (AI processing) | Faster (direct extraction) | Faster (direct extraction) |
| **Metadata** | Page numbers | Chunk types | Slide numbers + types |

## PowerPoint-Specific Features

### Slide Context
- Each chunk includes slide number for context
- Slide-by-slide processing maintains presentation flow
- Slide titles and content are extracted separately

### Shape Type Recognition
- Identifies and processes different shape types
- Handles text boxes, placeholders, and grouped content
- Preserves slide layout context

### Presentation Structure
- Maintains slide order and hierarchy
- Extracts titles, subtitles, and body content
- Handles complex slide layouts

## Performance Considerations

- **Direct Text Access**: Faster than PDF processing (no OCR needed)
- **Slide-by-Slide**: Processes slides sequentially for memory efficiency
- **Image Processing**: Optional AI processing for images only
- **Configurable Limits**: Can limit number of slides processed

## Limitations

- Currently supports `.pptx` format only (not legacy `.ppt` format)
- Image extraction depends on slide structure and embedded content
- Complex animations and transitions are not preserved
- Slide notes and comments are not extracted (can be added if needed)

## Future Enhancements

- Support for slide notes extraction
- Animation and transition metadata
- Master slide and template information
- Enhanced shape relationship detection
- Speaker notes integration

## Notes

- Generated chunk IDs are SHA1 hashes for consistent identification
- AI processing is optional but recommended for comprehensive image analysis
- Table extraction preserves basic structure using pipe separators
- Shape processing can be disabled for performance optimization
- Slide context is preserved throughout the extraction process
