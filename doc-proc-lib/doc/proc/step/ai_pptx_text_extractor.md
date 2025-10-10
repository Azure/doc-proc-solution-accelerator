# AI PowerPoint Text Extractor Step

The AI PowerPoint Text Extractor Step is a document processing component that extracts text content, tables, and images from Microsoft PowerPoint presentations (.pptx and .ppt formats). It follows the same architectural pattern as the AI PDF and Word Text Extractor Steps.

## Features

- **Slide Text Extraction**: Extracts text from all text shapes in PowerPoint slides
- **Table Extraction**: Extracts and formats table content from slides using pipe separators
- **Image Extraction**: Extracts embedded images from slides and processes them with AI
- **Shape Processing**: Handles various PowerPoint shape types and content
- **AI-Powered Image Analysis**: Uses Azure AI Model Inference Service to analyze extracted images
- **Slide-by-Slide Processing**: Organizes content by slide number for better context
- **Structured Output**: Organizes extracted content into chunks with metadata
- **Condition-Based Processing**: Supports conditional execution based on document properties

## Dependencies

```bash
pip install python-pptx
```

## Configuration

The PowerPoint Text Extractor Step requires the following configuration:

```yaml
- name: ai_pptx_text_extractor_1
  step_catalog_id: ai_pptx_text_extractor
  enabled: true
  fail_pipeline_on_error: true
  retry_on_failure: false
  retries: 3
  timeout: 600
  services: [primary_ai_inference_service]
  condition: "document_type.primary_type == 'powerpoint_presentation'"
  fail_step_on_document_error: true
  debug_mode: false
  settings:
    ai_model_inference_service: "primary_ai_inference_service"
    output_field_name: "chunks"
    png_output_folder: "./tmp/docproc/pptx_output/png"
    num_slides: -1  # -1 means all slides
    extract_images: true
    extract_image_descriptions: true
    extract_tables: true
    extract_shapes: true
    system_prompt: "You are an AI assistant that helps convert images from a pptx slide to markdown text. Only output valid markdown."
    user_prompt: |
      Extract the text from the following image into markdown and provide descriptions of images. Always format the markdown as follows to distinguish the text extracted from image descriptions:
      ==Extracted-Text==
      {Insert extracted text as markdown here}==End-Extracted-Text==
      
      ==Image-Descriptions==
      {Insert image descriptions as markdown here}==End-Image-Descriptions==
    max_completion_tokens: 4000
    temperature: 1.0
    top_p: 0.4
    frequency_penalty: 0.0
    presence_penalty: 0.0
```

## Input Data Structure

The step expects input data in the following format:

```python
{
    "temp_file_path": "/path/to/presentation.pptx",
    "document_type": {
        "primary_type": "powerpoint_presentation"  # if type condition is used - see below.
    }
}
```

## Output Data Structure

The step adds a `chunks` array to the document with the following structure:

```python
{
    "temp_file_path": "/path/to/presentation.pptx",
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
            "markdown_text": "Extracted text from AI analysis (for images)",
            "markdown_image_descriptions": "AI-generated image descriptions (for images)",
            "png": "/path/to/extracted/image.png", # for image chunks only
            "table_index": 1, # for table chunks only
            "image_index": 1  # for image chunks only
        }
    ]
}
```

## Processing Flow

1. **Document Validation**: Validates input PowerPoint document format (.pptx/.ppt) and existence
2. **Condition Evaluation**: Evaluates condition if specified (e.g., document type check)
3. **Slide Iteration**: Processes each slide up to the specified limit
4. **Text Extraction**: Extracts text from all text shapes in each slide
5. **Table Extraction**: Extracts and formats table content with pipe separators (if enabled)
6. **Image Extraction**: Extracts embedded images and saves as PNG files (if enabled)
7. **AI Processing**: Processes extracted images using Azure AI Model Inference Service
8. **Structured Output**: Organizes all extracted content into chunks with slide context

## Chunk Types

- **slide_text**: Text content from slide shapes (titles, body text, text boxes, etc.)
- **table**: Formatted table content with pipe-separated values
- **image**: Extracted images with AI-generated descriptions and text analysis

## Shape Processing

The extractor handles various PowerPoint shape types:

- **Text Shapes**: Title placeholders, content placeholders, text boxes
- **Table Shapes**: Native PowerPoint tables with cell-by-cell extraction
- **Picture Shapes**: Embedded images and photos
- **All Shape Types**: Any shape with text property is processed for text extraction

## Settings Configuration

### Required Settings
- `ai_model_inference_service`: Reference to the AI service instance to use to extract text from images in slides (required)
- `output_field_name`: Field name in document data dict to store the extracted content (default: "chunks")

### Core Settings
- `png_output_folder`: Directory for saving extracted images (default: "./tmp/docproc/pptx_output/png")
- `extract_images`: Enable/disable image extraction (default: true)
- `extract_image_descriptions`: Enable/disable AI-generated image descriptions (default: true)
- `extract_tables`: Enable/disable table extraction (default: true)
- `extract_shapes`: Enable/disable shape processing (default: true)
- `num_slides`: Number of slides to process (-1 for all, default: -1, max: 200)

### AI Processing Settings
- `system_prompt`: System prompt for AI image analysis (default: "You are an AI assistant that helps convert images from a pptx slide to markdown text. Only output valid markdown.")
- `user_prompt`: User prompt template for AI image analysis
- `max_completion_tokens`: Maximum tokens for AI responses (default: 4000, range: 100-8000)
- `temperature`: AI model temperature 0.0-2.0 (default: 1.0)
- `top_p`: AI model top-p sampling (default: 0.4, range: 0.0-1.0)
- `frequency_penalty`: AI model frequency penalty (default: 0.0, range: -2.0 to 2.0)
- `presence_penalty`: AI model presence penalty (default: 0.0, range: -2.0 to 2.0)

## Error Handling

The step includes comprehensive error handling:

- **File Validation**: Checks file existence and format (.pptx/.ppt)
- **Document Processing**: Individual document errors are logged and tracked
- **Slide Processing**: Slide-level errors are logged as warnings and processing continues
- **Image Processing**: Image extraction errors are logged as warnings
- **Configurable Failure**: `fail_step_on_document_error` controls whether document errors fail the step
- **Statistics Tracking**: Maintains counts of successful, failed, and skipped documents

## Usage Example

```python
from doc.proc.step.ai_pptx_text_extractor import AIPowerPointTextExtractorStep
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import Document

# Configure the step
config = StepInstanceConfig(
    name="ai_pptx_extractor_1",
    step_catalog_id="ai_pptx_text_extractor",
    enabled=True,
    services=["primary_ai_inference_service"],
    condition="document_type.primary_type == 'powerpoint_presentation'",
    settings={
        "ai_model_inference_service": "primary_ai_inference_service",
        "output_field_name": "chunks",
        "png_output_folder": "./tmp/docproc/pptx_output/png",
        "extract_images": True,
        "extract_tables": True,
        "extract_shapes": True,
        "num_slides": -1,
        "system_prompt": "You are an AI assistant that helps convert images from a pptx slide to markdown text. Only output valid markdown.",
        "user_prompt": "Extract the text from the following image into markdown and provide descriptions of images..."
    }
)

# Create step instance
pptx_extractor = AIPowerPointTextExtractorStep(instance_config=config)

# Prepare input data
input_document = Document(
    data={
        "temp_file_path": "/path/to/presentation.pptx",
        "document_type": {"primary_type": "powerpoint_presentation"}
    }
)

# Process documents (requires pipeline context)
# result = await pptx_extractor.run(input_document, context)
```



## PowerPoint-Specific Features

### Slide Context
- Each chunk includes slide number for presentation flow context
- Slide-by-slide processing maintains presentation structure
- Text, tables, and images are all associated with their source slide

### Shape Type Recognition
- Identifies and processes different PowerPoint shape types
- Handles text boxes, placeholders, and native tables
- Preserves slide layout context through structured extraction

### Presentation Structure
- Maintains slide order and hierarchy
- Extracts all text content from shapes with text properties
- Handles complex slide layouts with multiple content types

### Image Processing
- Extracts images from picture shapes
- Saves images as PNG files with descriptive names
- Optional AI analysis for text extraction and image descriptions
- Configurable image descriptions extraction

## Performance Considerations

- **Direct Text Access**: Fast text extraction without OCR
- **Slide-by-Slide**: Sequential processing for memory efficiency
- **Optional AI Processing**: Can disable image processing for speed
- **Configurable Limits**: Can limit number of slides processed
- **Error Resilience**: Individual slide failures don't stop processing

## Limitations

- Supports `.pptx` and `.ppt` formats
- Image extraction depends on embedded picture shapes
- Complex animations and transitions are not preserved
- Slide notes and comments are not extracted
- Shape relationships and positioning are simplified

## Future Enhancements

- Support for slide notes extraction
- Animation and transition metadata
- Master slide and template information
- Enhanced shape relationship detection
- Speaker notes integration
- Chart and diagram text extraction

## Notes

- Generated chunk IDs are SHA1 hashes for consistent identification across runs
- AI processing is optional but recommended for comprehensive image analysis
- Table extraction preserves structure using pipe separators (|)
- Shape processing extracts text from any shape with a text property
- Slide context is preserved throughout the extraction process
- Condition evaluation allows selective processing based on document properties
