# Excel Text Extractor Step

The Excel Text Extractor Step is a document processing component that extracts text content, images, and charts from Microsoft Excel spreadsheets (.xlsx, .xls, .xlsm, .xlsb formats). It processes each sheet individually and can optionally extract embedded images and charts.

## Features

- **Multi-Sheet Processing**: Extracts text from all or specified sheets in a workbook
- **Table/Cell Data Extraction**: Extracts structured data from Excel cells as tab-separated values
- **Image Extraction**: Extracts embedded images from sheets and saves them as PNG files
- **Chart Processing**: Identifies and processes charts (basic text representation)
- **Configurable Limits**: Set maximum rows and columns to process per sheet
- **Structured Output**: Organizes extracted content into chunks with metadata
- **Conditional Processing**: Supports conditional execution based on document type

## Dependencies

```bash
pip install openpyxl
```

## Configuration

The Excel Text Extractor Step requires the following configuration:

```yaml
- name: excel_text_extractor_1
  step_catalog_id: excel_text_extractor
  enabled: true
  fail_pipeline_on_error: true
  retry_on_failure: false
  retries: 3
  timeout: 600
  condition: "document_type.primary_type == 'excel_spreadsheet'"
  fail_step_on_document_error: true
  debug_mode: true
  settings:
    png_output_folder: "./output/png"
    extract_images: true
    extract_charts: true
    max_rows_per_sheet: -1  # -1 = all rows
    max_columns_per_sheet: -1  # -1 = all columns
    sheets_to_process: []  # Empty = all sheets
```

## Input Data Structure

The step expects input data in the following format:

```python
{
    "documents": [
        {
            "file_path": "/path/to/spreadsheet.xlsx",
            "document_type": {
                "primary_type": "excel_spreadsheet" # if type condition is used
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
                    "text": "Header1\tHeader2\nValue1\tValue2",
                    "input_file_path": "/path/to/spreadsheet.xlsx"
                },
                {
                    "chunk_id": "def456ghi789...",
                    "chunk_index": 2,
                    "chunk_type": "image",
                    "sheet_name": "Sheet1",
                    "image_path": "/output/png/excel_sheet_Sheet1_image_1.png",
                    "input_file_path": "/path/to/spreadsheet.xlsx"
                },
                {
                    "chunk_id": "ghi789jkl012...",
                    "chunk_index": 3,
                    "chunk_type": "chart",
                    "sheet_name": "Sheet1",
                    "text": "Chart: Sales Chart\nSeries: 2 data series",
                    "input_file_path": "/path/to/spreadsheet.xlsx"
                }
            ]
        }
    ]
}
```

## Settings Schema

### Core Settings

- **`png_output_folder`** (string, default: `"output_pngs"`): Directory path where extracted PNG images will be saved
- **`extract_images`** (boolean, default: `false`): Whether to extract embedded images from sheets
- **`extract_charts`** (boolean, default: `false`): Whether to extract and process charts from sheets
- **`max_rows_per_sheet`** (integer, default: `-1`): Maximum number of rows to process per sheet (-1 = all rows)
- **`max_columns_per_sheet`** (integer, default: `-1`): Maximum number of columns to process per sheet (-1 = all columns)
- **`sheets_to_process`** (array, default: `[]`): List of specific sheet names to process (empty = all sheets)

### AI Processing Settings

*Note: AI processing settings are not currently implemented in this step. Images and charts are extracted but not processed with AI.*

## Chunk Types

The step generates different types of chunks:

1. **Sheet Chunks** (`chunk_type: "sheet"`): Contains the textual content of Excel sheets as tab-separated values
2. **Image Chunks** (`chunk_type: "image"`): Contains extracted images saved as PNG files (no AI analysis currently)
3. **Chart Chunks** (`chunk_type: "chart"`): Contains basic text representation of charts with title and series information

## Processing Logic

1. **Document Validation**: Verifies the input file exists and has a valid Excel extension
2. **Workbook Loading**: Opens the Excel file using openpyxl library with `data_only=True` to get calculated values
3. **Sheet Selection**: Determines which sheets to process based on configuration
4. **Content Extraction**: For each sheet:
   - Extracts cell values as tab-separated text, respecting row/column limits
   - Identifies and extracts embedded images (saved as PNG files)
   - Processes charts (extracts basic text representation with title and series count)
5. **Chunk Generation**: Creates structured chunks with unique SHA-1 IDs and metadata
6. **Statistics Tracking**: Maintains processing statistics for successful, failed, and skipped documents

## Supported File Formats

- **.xlsx**: Excel 2007+ format (primary support)
- **.xls**: Legacy Excel format (limited support via openpyxl)
- **.xlsm**: Excel with macros
- **.xlsb**: Excel binary format

## Error Handling

The step handles various error scenarios:

- **File Not Found**: Logs error and raises FileNotFoundError if the Excel file doesn't exist
- **Invalid File Format**: Validates file extension before processing and raises ValueError for non-Excel files
- **Corrupted Files**: Catches openpyxl exceptions during file loading and raises StepExecutionError
- **Large Files**: Respects row/column limits to prevent memory issues with very large spreadsheets
- **Missing Dependencies**: Provides clear error message if openpyxl is not installed
- **Image Extraction Failures**: Logs warnings for failed image extractions but continues processing
- **Chart Processing Failures**: Logs warnings for failed chart processing but continues processing
- **Conditional Processing**: Supports document-level conditions and properly tracks skipped documents

## Performance Considerations

- **Memory Usage**: Large spreadsheets can consume significant memory. Use row/column limits for very large files
- **Processing Time**: Time scales with number of sheets and amount of content
- **Image Processing**: Each extracted image is saved as a PNG file, which may require storage space
- **No AI Processing**: Current implementation does not use AI services, so no API costs or latency concerns

## Examples

### Basic Text Extraction Only

```yaml
settings:
  extract_images: false
  extract_charts: false
  max_rows_per_sheet: 1000
```

### Specific Sheets Only

```yaml
settings:
  sheets_to_process: ["Summary", "Data", "Charts"]
  extract_images: true
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

- **Chart Extraction**: Chart image extraction is complex and currently provides basic text representation with title and series information
- **Formula Evaluation**: Only calculated cell values are extracted (using `data_only=True`), not the formulas themselves
- **Formatting**: Cell formatting (colors, fonts, borders, etc.) is not preserved in the extracted text
- **Hidden Content**: Hidden sheets or cells may not be processed depending on openpyxl behavior
- **Password Protection**: Password-protected files are not supported
- **No AI Processing**: Images and charts are extracted but not analyzed with AI services
- **Image Format**: All extracted images are saved as PNG files regardless of original format

## Related Steps

- **PDF Text Extractor**: For processing PDF documents
- **Word Text Extractor**: For processing Word documents
- **PowerPoint Text Extractor**: For processing PowerPoint presentations
- **Document Type Identifier**: For identifying document types before processing

## Troubleshooting

### Common Issues

1. **"openpyxl library is required"**: Install openpyxl using `pip install openpyxl`
2. **"File is not an Excel document"**: Verify file has correct extension (.xlsx, .xls, .xlsm, .xlsb)
3. **Memory errors with large files**: Set `max_rows_per_sheet` and `max_columns_per_sheet` limits
4. **Empty output**: Check if sheets contain actual data or if sheet names are specified correctly in `sheets_to_process`
5. **Images not extracted**: Verify `extract_images: true` is set and the PNG output folder is writable
6. **Charts not processed**: Ensure `extract_charts: true` is set and charts exist in the workbook

### Debug Mode

Enable debug mode for detailed logging:

```yaml
debug_mode: true
```

This will provide detailed information about:
- File processing status and validation results
- Number of sheets found and processed
- Content extraction progress for each sheet
- Image and chart extraction results
- Processing statistics (successful, failed, skipped documents)
