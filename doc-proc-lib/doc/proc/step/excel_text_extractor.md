# Excel Text Extractor Step

The Excel Text Extractor Step is a document processing component that extracts text content, images, and charts from Microsoft Excel spreadsheets (.xlsx, .xls, .xlsm, .xlsb formats). It processes each sheet individually and can optionally extract embedded images and charts using AI-powered analysis.

## Features

- **Multi-Sheet Processing**: Extracts text from all or specified sheets in a workbook
- **Table/Cell Data Extraction**: Extracts structured data from Excel cells
- **Image Extraction**: Extracts embedded images from sheets
- **Chart Processing**: Identifies and processes charts (basic text representation)
- **AI-Powered Image Analysis**: Uses Azure AI Model Inference Service to analyze extracted images
- **Configurable Limits**: Set maximum rows and columns to process per sheet
- **Structured Output**: Organizes extracted content into chunks with metadata

## Dependencies

```bash
pip install openpyxl
```

## Configuration

The Excel Text Extractor Step requires the following configuration:

```yaml
- id: excel_extractor_001
  name: Excel Text Extractor
  enabled: true
  description: Extract text, images, and charts from Excel spreadsheets
  tags: [text-extraction, excel, spreadsheet, document-processing]
  fail_step_on_document_error: false
  debug_mode: true
  services: [azure_ai_inference]
  settings:
    png_output_folder: output_images
    extract_images: true
    extract_charts: true
    max_rows_per_sheet: -1  # -1 = all rows
    max_columns_per_sheet: -1  # -1 = all columns
    sheets_to_process: []  # Empty = all sheets
    prompts:
      system: "You are a spreadsheet analysis assistant. Extract text and describe images/charts from the provided Excel content."
      user: "Please extract all text content and describe any images or charts you see in this Excel sheet. Format your response with ==Extracted-Text== and ==End-Extracted-Text== tags around the text, and ==Image-Descriptions== and ==End-Image-Descriptions== tags around image descriptions."
    max_completion_tokens: 4000
    temperature: 0.1
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
            "file_path": "/path/to/spreadsheet.xlsx",
            "file_name": "spreadsheet.xlsx",
            "file_size": 1048576,
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "document_type": {
                "primary_type": "excel",
                "confidence": 0.95
            }
        }
    ]
}
```

## Output Data Structure

The step extends each document with extracted chunks:

```python
{
    "documents": [
        {
            "file_path": "/path/to/spreadsheet.xlsx",
            "file_name": "spreadsheet.xlsx",
            "chunks": [
                {
                    "chunk_id": "abc123def456...",
                    "chunk_index": 1,
                    "chunk_type": "sheet",
                    "sheet_name": "Sheet1",
                    "text_content": "Header1\tHeader2\nValue1\tValue2",
                    "source_file": "/path/to/spreadsheet.xlsx"
                },
                {
                    "chunk_id": "def456ghi789...",
                    "chunk_index": 2,
                    "chunk_type": "image",
                    "sheet_name": "Sheet1",
                    "image_path": "/output/excel_sheet_Sheet1_image_1.png",
                    "markdown_text": "==Extracted-Text==\nChart showing sales data\n==End-Extracted-Text==",
                    "extracted_text": "Chart showing sales data",
                    "extracted_images": "Bar chart with quarterly sales figures",
                    "source_file": "/path/to/spreadsheet.xlsx"
                }
            ]
        }
    ]
}
```

## Settings Schema

### Core Settings

- **`png_output_folder`** (string, default: `"output_pngs"`): Directory path where extracted PNG images will be saved
- **`extract_images`** (boolean, default: `true`): Whether to extract embedded images from sheets
- **`extract_charts`** (boolean, default: `true`): Whether to extract and process charts from sheets
- **`max_rows_per_sheet`** (integer, default: `-1`): Maximum number of rows to process per sheet (-1 = all rows)
- **`max_columns_per_sheet`** (integer, default: `-1`): Maximum number of columns to process per sheet (-1 = all columns)
- **`sheets_to_process`** (array, default: `[]`): List of specific sheet names to process (empty = all sheets)

### AI Processing Settings

- **`prompts`** (object, required): Contains system and user prompts for AI processing
  - **`system`** (string, required): Instructions for the AI system
  - **`user`** (string, required): Template for user prompts sent to AI
- **`max_completion_tokens`** (integer, default: `4000`): Maximum number of tokens to generate
- **`temperature`** (number, default: `1.0`): Controls randomness in AI responses (0.0-2.0)
- **`top_p`** (number, default: `1.0`): Controls diversity of AI responses (0.0-1.0)
- **`frequency_penalty`** (number, default: `0.0`): Reduces repetition in AI responses (-2.0 to 2.0)
- **`presence_penalty`** (number, default: `0.0`): Encourages AI to talk about new topics (-2.0 to 2.0)

## Chunk Types

The step generates different types of chunks:

1. **Sheet Chunks** (`chunk_type: "sheet"`): Contains the textual content of Excel sheets
2. **Image Chunks** (`chunk_type: "image"`): Contains extracted images with AI analysis
3. **Chart Chunks** (`chunk_type: "chart"`): Contains basic text representation of charts

## Processing Logic

1. **Document Validation**: Verifies the input file exists and has a valid Excel extension
2. **Workbook Loading**: Opens the Excel file using openpyxl library
3. **Sheet Selection**: Determines which sheets to process based on configuration
4. **Content Extraction**: For each sheet:
   - Extracts cell values as tab-separated text
   - Identifies and extracts embedded images
   - Processes charts (basic text representation)
5. **AI Processing**: If images are extracted, uses Azure AI Inference Service to analyze them
6. **Chunk Generation**: Creates structured chunks with unique IDs and metadata

## Supported File Formats

- **.xlsx**: Excel 2007+ format (primary support)
- **.xls**: Legacy Excel format (limited support via openpyxl)
- **.xlsm**: Excel with macros
- **.xlsb**: Excel binary format

## Error Handling

The step handles various error scenarios:

- **File Not Found**: Logs error and marks document as failed
- **Invalid File Format**: Validates file extension before processing
- **Corrupted Files**: Catches openpyxl exceptions during file loading
- **Large Files**: Respects row/column limits to prevent memory issues
- **Missing Dependencies**: Provides clear error message if openpyxl is not installed

## Performance Considerations

- **Memory Usage**: Large spreadsheets can consume significant memory. Use row/column limits for very large files
- **Processing Time**: Time scales with number of sheets and amount of content
- **AI API Calls**: Each extracted image results in an AI API call, which may incur costs and latency

## Examples

### Basic Text Extraction

```yaml
settings:
  extract_images: false
  extract_charts: false
  max_rows_per_sheet: 1000
  prompts:
    system: "Extract spreadsheet data"
    user: "Convert this spreadsheet content to structured text"
```

### Specific Sheets Only

```yaml
settings:
  sheets_to_process: ["Summary", "Data", "Charts"]
  extract_images: true
  prompts:
    system: "Process specific Excel sheets"
    user: "Extract content from the specified sheets"
```

### Limited Processing for Performance

```yaml
settings:
  max_rows_per_sheet: 500
  max_columns_per_sheet: 20
  extract_images: false
  extract_charts: false
```

## Limitations

- **Chart Extraction**: Chart image extraction is complex and currently provides basic text representation
- **Formula Evaluation**: Only cell values are extracted, not formulas
- **Formatting**: Cell formatting (colors, fonts, etc.) is not preserved
- **Hidden Content**: Hidden sheets or cells may not be processed depending on openpyxl behavior
- **Password Protection**: Password-protected files are not supported

## Related Steps

- **PDF Text Extractor**: For processing PDF documents
- **Word Text Extractor**: For processing Word documents
- **PowerPoint Text Extractor**: For processing PowerPoint presentations
- **Document Type Identifier**: For identifying document types before processing

## Troubleshooting

### Common Issues

1. **"openpyxl library is required"**: Install openpyxl using `pip install openpyxl`
2. **"File is not an Excel document"**: Verify file has correct extension (.xlsx, .xls, etc.)
3. **Memory errors with large files**: Set `max_rows_per_sheet` and `max_columns_per_sheet` limits
4. **Empty output**: Check if sheets contain actual data or if sheet names are specified correctly

### Debug Mode

Enable debug mode for detailed logging:

```yaml
debug_mode: true
```

This will provide detailed information about:
- File processing status
- Number of sheets found
- Content extraction progress
- AI processing results
