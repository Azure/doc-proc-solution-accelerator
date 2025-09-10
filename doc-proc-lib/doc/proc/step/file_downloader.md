# FileDownloaderStep

## Overview

The `FileDownloaderStep` is a pipeline step that downloads files from Azure Blob Storage to a local temporary directory. It processes documents that contain blob references (either `blob_details` or `blob_sas_url` fields) and adds a local `file_path` to enable further processing by downstream steps.

## Features

- Downloads files from Azure Blob Storage using blob details or SAS URLs
- Configurable temporary directory for downloaded files
- Automatic creation of temporary directories
- Uses Blob service from service catalog to connect to Azure Storage account
- Skips documents that already have local file paths
- Comprehensive error handling and cleanup

## Configuration

### Step Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `temp_folder` | string | `None` | Path to temporary folder for downloaded files. If not specified, uses system temporary directory |

### Services Required

- `azure_blob_storage`: Azure Blob Storage service (required when using `blob_details`)

## Input Data Format

### Document
```python
# Document with blob_details
{
  "data": {
    "id": "document_1",
    "blob_details": {
      "container": "documents", 
      "blob": "sample.pdf"
    }
  }
}

# Document with blob_sas_url
{
  "data": {
    "id": "document_1",
    "blob_sas_url": "https://storage.blob.core.windows.net/container/file2.docx?sv=..."
  }
}
  
```

## Output Data Format

The step adds a `file_path` field to documents after successful download:

```python
{
  "data": {
    "id": "doc_1",
    "blob_details": {
        "container": "documents",
        "blob": "file1.pdf"
    },
    "file_path": "/tmp/tmpfile123"
  }
}
```

## Pipeline Configuration Example

```yaml
name: "document_processing_pipeline"
description: "Pipeline with file download as step"
version: "1.0"

steps:
  - name: "file_downloader"
    step_catalog_id: "file_downloader"
    settings:
      temp_folder: "/tmp/pipeline_files"
    services:
      - "azure_blob_service"

```

## Step Catalog Entry

```yaml
- id: "file_downloader"
  name: "File Downloader"
  description: "Downloads files from Azure Blob Storage to local temporary directory"
  version: "1.0"
  class_name: "FileDownloaderStep"
  module_name: "doc.proc.step.file_downloader"
```

## Error Handling

The step handles various error scenarios:

- **Invalid blob details**: Validates container and blob names
- **Missing blob service**: Logs warning when blob_details provided but no service available
- **HTTP errors**: Handles network issues when downloading from SAS URLs
- **File system errors**: Cleans up temporary files on failure
- **Permission errors**: Proper error reporting for access issues

## Usage Notes

1. **Order in Pipeline**: This step should typically be placed at the beginning of the pipeline to ensure files are available for subsequent processing steps.

2. **File Cleanup**: Downloaded temporary files are not automatically cleaned up. Consider implementing cleanup logic in your application or use a temporary directory that gets cleared periodically.

3. **Storage Requirements**: Ensure sufficient disk space is available in the temporary directory for all downloaded files.

## Integration with Other Steps

This step is designed to work seamlessly with other processing steps:

- **DocumentTypeIdentifierStep**: Expects documents to have `file_path`
- **Text Extraction Steps**: Can process the downloaded files directly
- **Analysis Steps**: Work with local files for improved performance
