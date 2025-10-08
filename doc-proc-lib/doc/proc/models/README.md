# Document Processing Library - Models Documentation

This document provides comprehensive documentation for the core data models used in the document processing pipeline system, focusing on how documents flow through processing steps.

## Table of Contents

1. [Overview](#overview)
2. [Document Model](#document-model)
3. [ContentIdentifier Model](#contentidentifier-model)
4. [PipelineInput Model](#pipelineinput-model)
5. [Pipeline Execution Models](#pipeline-execution-models)
6. [Usage Patterns](#usage-patterns)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

## Overview

The document processing system uses several core Pydantic models to represent documents, their metadata, and processing results. These models ensure type safety and provide a consistent interface for data exchange between pipeline steps.

### Key Models

- **`Document`**: Core data structure for individual documents in the pipeline
- **`ContentIdentifier`**: Unique identification and source metadata for content
- **`PipelineInput`**: Input data structure for pipeline execution
- **`PipelineExecutionResult`**: Results and statistics from pipeline runs
- **`DocumentResult`**: Processing results for individual documents
- **`StepExecutionResult`**: Results from individual step executions

## Document Model

The `Document` model is the primary data structure that flows through pipeline steps. It encapsulates document content, metadata, and processing state.

### Model Definition

```python
from pydantic import BaseModel, Field
from typing import Optional

class Document(BaseModel):
    """Input/Output data structure for pipeline steps that holds document data."""
    
    id: ContentIdentifier = Field(default=None, description="Content identifier for the document")
    summary_data: dict = Field(default_factory=dict, description="Summary data for the document")
    data: dict = Field(default_factory=dict, description="Main data dictionary for the document")
```

### Field Descriptions

#### `id: ContentIdentifier`
- **Purpose**: Uniquely identifies the document and its source
- **Type**: `ContentIdentifier` object (see below)
- **Usage**: Used for tracking, logging, and referencing documents across steps
- **Required**: Yes (but can be None initially and set by early steps)

#### `summary_data: dict`
- **Purpose**: Stores high-level metadata and summary information about the document
- **Type**: Python dictionary with flexible schema
- **Usage**: Contains counts, statistics, processing flags, and overview data
- **Examples**: Page counts, file sizes, document type, processing status

#### `data: dict`
- **Purpose**: Contains the actual document content and detailed processing results
- **Type**: Python dictionary with flexible schema
- **Usage**: Stores extracted text, images, tables, structured data, and step-specific results
- **Examples**: Raw text, parsed content, AI analysis results, indexed data

### Document Structure Evolution

Documents evolve as they flow through pipeline steps:

```python
# Initial document (from content retriever)
initial_doc = Document(
    id=ContentIdentifier(
        canonical_id="doc123.pdf",
        source_id="blob-storage-1",
        path="documents/doc123.pdf"
    ),
    summary_data={
        "file_size": 1024000,
        "mime_type": "application/pdf"
    },
    data={
        "content_url": "https://storage.blob.core.windows.net/docs/doc123.pdf"
    }
)

# After text extraction step
processed_doc = Document(
    id=initial_doc.id,  # ID remains the same
    summary_data={
        **initial_doc.summary_data,
        "page_count": 15,
        "text_extraction_status": "completed",
        "word_count": 3450
    },
    data={
        **initial_doc.data,
        "extracted_text": "Full document text content...",
        "pages": [
            {"page_num": 1, "text": "Page 1 content..."},
            {"page_num": 2, "text": "Page 2 content..."}
        ],
        "images": [
            {"page": 3, "image_data": "base64_encoded_image_data"}
        ]
    }
)

# After AI processing step
ai_processed_doc = Document(
    id=initial_doc.id,
    summary_data={
        **processed_doc.summary_data,
        "entities_found": 25,
        "ai_processing_status": "completed"
    },
    data={
        **processed_doc.data,
        "entities": [
            {"type": "PERSON", "text": "John Smith", "confidence": 0.95},
            {"type": "ORG", "text": "Acme Corp", "confidence": 0.88}
        ],
        "summary": "AI-generated document summary...",
        "keywords": ["contract", "agreement", "legal"]
    }
)
```

### Common Data Patterns

#### Text Content Structure
```python
# Standard text extraction format
data = {
    "extracted_text": "Full document text",
    "pages": [
        {
            "page_num": 1,
            "text": "Page content",
            "word_count": 245,
            "confidence": 0.98
        }
    ],
    "metadata": {
        "language": "en",
        "text_extraction_method": "ocr"
    }
}
```

#### Image and Media Content
```python
# Image and media references
data = {
    "images": [
        {
            "page": 1,
            "image_id": "img_001",
            "format": "jpeg",
            "size": {"width": 800, "height": 600},
            "content": "base64_encoded_data",
            "description": "Chart showing quarterly results"
        }
    ],
    "tables": [
        {
            "page": 2,
            "table_id": "table_001",
            "rows": 10,
            "cols": 4,
            "data": [["Header1", "Header2"], ["Value1", "Value2"]]
        }
    ]
}
```

#### AI Processing Results
```python
# AI analysis and extraction results
data = {
    "ai_analysis": {
        "document_type": "contract",
        "confidence": 0.92,
        "key_sections": {
            "parties": ["Company A", "Company B"],
            "terms": "12 months",
            "value": "$50,000"
        }
    },
    "entities": [
        {
            "type": "MONEY",
            "text": "$50,000",
            "start_pos": 1250,
            "end_pos": 1257,
            "confidence": 0.95
        }
    ]
}
```

## ContentIdentifier Model

The `ContentIdentifier` model provides comprehensive identification and source metadata for documents.

### Model Definition

```python
from pydantic import BaseModel, Field
from typing import Optional

class ContentIdentifier(BaseModel):
    canonical_id: str = Field(description='Canonical identifier for the content')
    unique_id: Optional[str] = Field(default=None, description='Unique identifier for the content')
    source_id: str = Field(description='Identifier for the source instance of the content')
    source_name: Optional[str] = Field(default=None, description='Name of the source instance of the content')
    source_type: Optional[str] = Field(default=None, description='Type of the data source (e.g., azure_blob, azure_files, sharepoint)')
    container: Optional[str] = Field(default=None, description='Container or bucket name where the content is stored')
    path: Optional[str] = Field(default=None, description='Path or location of the content within the source')
    metadata: dict[str, object] | None = Field(default=None, description='Metadata associated with the content')
```

### Field Descriptions

#### Required Fields
- **`canonical_id`**: Primary identifier for the content (e.g., filename, document ID)
- **`source_id`**: Identifier for the source system or service instance

#### Optional Fields
- **`unique_id`**: Additional unique identifier (e.g., GUID, hash)
- **`source_name`**: Human-readable name of the source
- **`source_type`**: Type of source system (azure_blob, sharepoint, local_file, etc.)
- **`container`**: Container, bucket, or collection name
- **`path`**: Full path or location within the source
- **`metadata`**: Additional source-specific metadata

### Usage Examples

```python
# Azure Blob Storage document
blob_id = ContentIdentifier(
    canonical_id="contract_2024_001.pdf",
    source_id="prod-storage-account",
    source_name="Production Document Storage",
    source_type="azure_blob",
    container="legal-documents",
    path="contracts/2024/contract_2024_001.pdf",
    metadata={
        "blob_url": "https://storage.blob.core.windows.net/legal-documents/contracts/2024/contract_2024_001.pdf",
        "last_modified": "2024-01-15T10:30:00Z",
        "content_type": "application/pdf"
    }
)

# SharePoint document
sharepoint_id = ContentIdentifier(
    canonical_id="meeting_notes_q1.docx",
    unique_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
    source_id="company-sharepoint",
    source_name="Company SharePoint Site",
    source_type="sharepoint",
    container="Documents",
    path="/sites/team/Shared Documents/meetings/meeting_notes_q1.docx",
    metadata={
        "site_url": "https://company.sharepoint.com/sites/team",
        "created_by": "john.doe@company.com",
        "version": "1.2"
    }
)

# Local file system
local_id = ContentIdentifier(
    canonical_id="report.xlsx",
    source_id="local-filesystem",
    source_type="local_file",
    path="/Users/user/Documents/reports/report.xlsx",
    metadata={
        "file_size": 2048000,
        "created_date": "2024-01-10T14:22:00Z"
    }
)
```

## PipelineInput Model

The `PipelineInput` model defines the input data structure for pipeline execution.

### Model Definition

```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class PipelineInput(BaseModel):
    """Model for the input data to a pipeline."""
    documents: List[Document] = []  # List of documents to be processed
    metadata: Optional[Dict[str, Any]] = None  # Optional metadata for the pipeline execution
```

### Field Descriptions

#### `documents: List[Document]`
- **Purpose**: Collection of documents to process through the pipeline
- **Type**: List of `Document` objects
- **Usage**: Contains all documents that should be processed in this pipeline run
- **Can be empty**: Yes (for pipelines that generate their own documents)

#### `metadata: Optional[Dict[str, Any]]`
- **Purpose**: Pipeline-level metadata and configuration
- **Type**: Optional dictionary
- **Usage**: Contains execution parameters, user context, processing flags
- **Examples**: User ID, batch ID, processing mode, output preferences

### Usage Patterns

#### Batch Document Processing
```python
# Processing multiple documents in a batch
pipeline_input = PipelineInput(
    documents=[
        Document(
            id=ContentIdentifier(canonical_id="doc1.pdf", source_id="batch-001"),
            data={"content_url": "https://storage.blob.core.windows.net/docs/doc1.pdf"}
        ),
        Document(
            id=ContentIdentifier(canonical_id="doc2.docx", source_id="batch-001"),
            data={"content_url": "https://storage.blob.core.windows.net/docs/doc2.docx"}
        )
    ],
    metadata={
        "batch_id": "batch_2024_001",
        "user_id": "john.doe@company.com",
        "processing_mode": "standard",
        "output_format": "json",
        "notify_on_completion": True
    }
)
```

#### Empty Document List (Source-generating Pipeline)
```python
# Pipeline that retrieves its own documents
pipeline_input = PipelineInput(
    documents=[],  # Empty - documents will be retrieved by the pipeline
    metadata={
        "source_container": "incoming-documents",
        "date_filter": "2024-01-01",
        "file_types": ["pdf", "docx", "xlsx"],
        "max_documents": 100
    }
)
```

#### Single Document Processing
```python
# Processing a single document with specific parameters
pipeline_input = PipelineInput(
    documents=[
        Document(
            id=ContentIdentifier(
                canonical_id="important_contract.pdf",
                source_id="legal-docs"
            ),
            data={"file_path": "/tmp/important_contract.pdf"}
        )
    ],
    metadata={
        "priority": "high",
        "extract_entities": True,
        "generate_summary": True,
        "output_destination": "legal-search-index"
    }
)
```

## Pipeline Execution Models

### PipelineExecutionResult

The main result model for pipeline execution:

```python
class PipelineExecutionResult(BaseModel):
    pipeline_name: str
    result: Literal["NotStarted", "Succeeded", "Failed", "PartialSucceeded"] = "NotStarted"
    reason: Optional[str] = None
    elapsed_time_secs: float
    document_results: List[DocumentResult] = []
    summary_stats: dict = {}
    started_at: Optional[str] = None  # UTC ISO format
    completed_at: Optional[str] = None  # UTC ISO format
```

### DocumentResult

Results for individual document processing:

```python
class DocumentResult(BaseModel):
    document_id: ContentIdentifier
    result: Literal["NotStarted", "Succeeded", "Failed", "PartialSucceeded"] = "NotStarted"
    reason: Optional[str] = None
    elapsed_time_secs: float
    data: Dict[str, Any] = {}  # Final processed document data
    summary_data: Dict[str, Any] = {}  # Document summary information
    step_results: List[StepExecutionResult] = []  # Results from each step
```

### StepExecutionResult

Results for individual step execution:

```python
class StepExecutionResult(BaseModel):
    step_name: str
    result: Literal["NotStarted", "Succeeded", "Failed", "Skipped"] = "NotStarted"
    reason: Optional[str] = None
    elapsed_time_secs: float
    error: Optional[str] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
```

## Usage Patterns

### Step Implementation Pattern

When implementing pipeline steps, follow this pattern for handling documents:

```python
from doc.proc.step.step_base import StepBase
from doc.proc.models import Document

class MyProcessingStep(StepBase):
    
    def process_document(self, document: Document, config, context) -> Document:
        # Access document identification
        doc_id = document.id.canonical_id
        source_path = document.id.path
        
        # Read existing data
        existing_text = document.data.get("extracted_text", "")
        page_count = document.summary_data.get("page_count", 0)
        
        # Perform processing
        processed_content = self.my_processing_logic(existing_text)
        
        # Update document with new data
        document.data.update({
            "my_step_result": processed_content,
            "processing_timestamp": datetime.utcnow().isoformat()
        })
        
        # Update summary data
        document.summary_data.update({
            "my_step_status": "completed",
            "additional_data_count": len(processed_content)
        })
        
        return document
```

### Data Preservation Pattern

Always preserve existing data when adding new information:

```python
# Good: Preserve existing data
document.data.update({
    "new_field": new_value
})

# Good: Preserve with explicit merge
document.data = {
    **document.data,
    "step_specific_data": {
        "result": processed_result,
        "metadata": step_metadata
    }
}

# Avoid: Overwriting existing data
# document.data = {"new_field": new_value}  # This loses all previous data
```

### Error Handling Pattern

Handle errors gracefully while preserving document state:

```python
def process_document(self, document: Document, config, context) -> Document:
    try:
        # Processing logic
        result = self.complex_processing(document.data)
        
        document.data["processing_result"] = result
        document.summary_data["status"] = "success"
        
    except Exception as e:
        # Preserve document but add error information
        document.summary_data.update({
            "status": "error",
            "error_message": str(e),
            "error_step": "complex_processing"
        })
        # Don't modify document.data on error to preserve existing content
        
    return document
```

## Best Practices

### Document ID Management
1. **Preserve IDs**: Never modify the `document.id` once set
2. **Set Early**: Ensure document IDs are set by the first step in the pipeline
3. **Use Canonical IDs**: Make canonical_id meaningful and human-readable
4. **Include Source Info**: Always populate source_type and source_id for traceability

### Data Organization
1. **Namespace Step Data**: Use step-specific keys in the data dictionary
2. **Preserve History**: Avoid overwriting data from previous steps
3. **Use Summary Data**: Put counts, flags, and metadata in summary_data
4. **Structure Nested Data**: Use nested dictionaries for complex data structures

### Error Handling
1. **Graceful Degradation**: Continue processing other documents if one fails
2. **Preserve State**: Don't lose existing document data on errors
3. **Detailed Errors**: Include helpful error messages and context
4. **Log Thoroughly**: Use the pipeline context for logging

### Performance Considerations
1. **Lazy Loading**: Don't load large content until needed
2. **Memory Management**: Clean up large temporary data structures
3. **Streaming**: Use streaming for large file processing when possible
4. **Batching**: Process multiple documents efficiently

## Examples

### Complete Pipeline Flow Example

```python
# 1. Initial document from content retriever
initial_docs = [
    Document(
        id=ContentIdentifier(
            canonical_id="annual_report.pdf",
            source_id="company-storage",
            source_type="azure_blob",
            container="reports",
            path="annual/annual_report.pdf"
        ),
        summary_data={
            "file_size": 5000000,
            "mime_type": "application/pdf"
        },
        data={
            "blob_url": "https://storage.blob.core.windows.net/reports/annual/annual_report.pdf"
        }
    )
]

pipeline_input = PipelineInput(
    documents=initial_docs,
    metadata={
        "pipeline_run_id": "run_001",
        "user_id": "analyst@company.com"
    }
)

# 2. After file download step
# Document data updated with local file path
document.data.update({
    "local_file_path": "/tmp/pipeline_run_001/annual_report.pdf",
    "download_status": "completed"
})

# 3. After text extraction step  
# Document enhanced with extracted content
document.data.update({
    "extracted_text": "Annual Report 2024...",
    "pages": [{"page_num": 1, "text": "..."}],
    "tables": [{"page": 5, "data": [...]}]
})
document.summary_data.update({
    "page_count": 85,
    "word_count": 15000,
    "table_count": 12
})

# 4. After AI analysis step
# Document enriched with AI insights
document.data.update({
    "ai_analysis": {
        "document_category": "financial_report",
        "key_metrics": {
            "revenue": "$50M",
            "growth_rate": "15%"
        },
        "sentiment": "positive"
    },
    "entities": [
        {"type": "MONEY", "text": "$50M", "confidence": 0.95}
    ]
})

# 5. Final result accessible through PipelineExecutionResult
result = PipelineExecutionResult(
    pipeline_name="document_analysis_pipeline",
    result="Succeeded",
    elapsed_time_secs=245.6,
    document_results=[
        DocumentResult(
            document_id=document.id,
            result="Succeeded",
            elapsed_time_secs=245.6,
            data=document.data,
            summary_data=document.summary_data,
            step_results=[...]
        )
    ]
)
```

This comprehensive model system ensures type safety, traceability, and flexibility for complex document processing workflows.