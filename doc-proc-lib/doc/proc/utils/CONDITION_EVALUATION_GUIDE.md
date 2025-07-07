# Secure Condition Evaluation for Pipeline Steps

## Overview

The secure condition evaluation system allows you to conditionally execute pipeline steps based on document data, metadata, and processing results. This provides dynamic workflow control while maintaining security by preventing code injection attacks.

## Key Features

- **Secure Evaluation**: Prevents code injection by using a controlled evaluation environment
- **Rich Operators**: Supports comparison, logical, and pattern matching operations
- **Nested Field Access**: Access deeply nested document properties using dot notation
- **Array Access**: Support for array indexing and nested array access
- **Type Safety**: Automatic type conversion and null-safe operations
- **Performance**: Optimized with regex caching and efficient evaluation
- **Validation**: Pre-validation of condition strings to catch errors early

## Supported Operators

### Comparison Operators
- `==` - Equals
- `!=` - Not equals
- `>` - Greater than
- `>=` - Greater than or equal
- `<` - Less than
- `<=` - Less than or equal

### Collection Operators
- `in` - Value is in collection
- `not_in` - Value is not in collection
- `contains` - Collection contains value
- `not_contains` - Collection does not contain value

### String Operators
- `starts_with` - String starts with pattern
- `ends_with` - String ends with pattern
- `regex_match` - String matches regex pattern

### Null/Empty Operators
- `is_empty` - Field is null, empty string, or empty array
- `is_not_empty` - Field is not null, not empty string, and not empty array

### Logical Operators
- `and` - Logical AND
- `or` - Logical OR

## Field Path Syntax

### Basic Field Access
```
document_type.primary_type
metadata.pages
file_name
```

### Array Access
```
tags[0]                    # First element
tags[1]                    # Second element
metadata.authors[0]        # First author
```

### Dictionary Access
```
metadata['custom_field']   # Dictionary key access
document_type['subtype']   # Alternative syntax
```

### Nested Access
```
document_type.analysis.confidence
metadata.sections[0].title
processing_results.steps[2].status
```

## Example Conditions

### Simple Conditions
```yaml
# Execute step only for PDF documents
condition: "document_type.primary_type == 'pdf'"

# Execute step only for high-confidence results
condition: "document_type.confidence > 0.8"

# Execute step only for large files
condition: "file_size >= 1048576"

# Execute step only for encrypted documents
condition: "metadata.encrypted == true"
```

### Collection Conditions
```yaml
# Execute step for office documents
condition: "document_type.category in ['office_document', 'spreadsheet', 'presentation']"

# Execute step if document has specific tags
condition: "'important' in tags"

# Execute step if filename contains specific text
condition: "file_name contains 'contract'"

# Execute step if document type is not in exclusion list
condition: "document_type.primary_type not_in ['unknown', 'corrupted']"
```

### Pattern Matching
```yaml
# Execute step for files with specific extensions
condition: "file_name ends_with '.pdf'"

# Execute step for files starting with specific prefix
condition: "file_name starts_with 'invoice_'"

# Execute step for files matching regex pattern
condition: "file_name regex_match '^contract_\\d{4}_\\d{2}_\\d{2}\\.pdf$'"
```

### Logical Combinations
```yaml
# Execute step for PDFs with high confidence
condition: "document_type.primary_type == 'pdf' and document_type.confidence > 0.8"

# Execute step for multiple document types
condition: "document_type.primary_type == 'pdf' or document_type.primary_type == 'word'"

# Complex condition with mixed operators
condition: "document_type.primary_type == 'pdf' and (document_type.confidence > 0.8 or file_size < 1024)"
```

### Empty/Null Checks
```yaml
# Execute step only if field is not empty
condition: "metadata.author is_not_empty"

# Execute step only if field is empty
condition: "error_message is_empty"

# Execute step if optional field is provided
condition: "processing_options.custom_field is_not_empty"
```

## Usage in Pipeline Configuration

### Basic Usage
```yaml
pipeline:
  name: "Conditional Processing Pipeline"
  steps:
    - name: identify_document_types
      step_catalog_id: document_type_identifier
      settings:
        identification_methods: "magic_bytes, file_extension"
        
    - name: process_pdfs
      step_catalog_id: pdf_text_extractor
      condition: "document_type.primary_type == 'pdf'"
      settings:
        dpi: 300
        extract_images: true
        
    - name: process_office_docs
      step_catalog_id: office_document_processor
      condition: "document_type.category in ['office_document', 'spreadsheet', 'presentation']"
      settings:
        extract_text: true
        preserve_formatting: true
```

### Advanced Usage
```yaml
pipeline:
  name: "Advanced Conditional Pipeline"
  steps:
    - name: identify_document_types
      step_catalog_id: document_type_identifier
      
    - name: high_confidence_processing
      step_catalog_id: advanced_text_extractor
      condition: "document_type.confidence > 0.9 and file_size < 10485760"
      settings:
        use_advanced_ocr: true
        
    - name: fallback_processing
      step_catalog_id: basic_text_extractor
      condition: "document_type.confidence <= 0.9 or file_size >= 10485760"
      settings:
        use_basic_ocr: true
        
    - name: security_scan
      step_catalog_id: security_scanner
      condition: "document_type.primary_type == 'pdf' and metadata.encrypted == false"
      settings:
        scan_for_malware: true
        
    - name: archive_important_docs
      step_catalog_id: document_archiver
      condition: "'important' in tags or 'contract' in tags"
      settings:
        archive_location: "secure_storage"
```

## Security Features

### Input Validation
- **Field Path Validation**: Only allows safe field names and paths
- **Operator Validation**: Restricts to safe, predefined operators
- **Value Parsing**: Safely parses values without executing code
- **Depth Limiting**: Prevents deep recursion attacks

### Code Injection Prevention
- **No eval() or exec()**: Never executes dynamic code
- **No import statements**: Prevents importing dangerous modules
- **No function calls**: Prevents calling system functions
- **Controlled environment**: Operates in a sandboxed evaluation context

### Error Handling
- **Graceful degradation**: Invalid conditions don't crash the pipeline
- **Detailed logging**: Comprehensive error messages for debugging
- **Validation**: Pre-validation catches issues before execution
- **Safe defaults**: Missing fields return safe default values

## Performance Considerations

### Optimization Features
- **Regex Caching**: Compiled regex patterns are cached for reuse
- **Lazy Evaluation**: Short-circuit evaluation for logical operators
- **Minimal Data Access**: Only accesses required fields
- **Efficient Parsing**: Optimized condition parsing

### Best Practices
1. **Use Simple Conditions**: Simple conditions evaluate faster
2. **Order Conditions**: Put most selective conditions first in AND operations
3. **Cache Results**: Results can be cached if the same condition is used multiple times
4. **Avoid Complex Regex**: Simple patterns are faster than complex ones

## Debugging and Troubleshooting

### Common Issues

#### Invalid Field Path
```
Error: Invalid field name: document type
Solution: Use valid field names (alphanumeric, underscore, hyphen only)
Correct: document_type.primary_type
```

#### Missing Operator
```
Error: Invalid condition format: document_type.primary_type 'pdf'
Solution: Include the comparison operator
Correct: document_type.primary_type == 'pdf'
```

#### Invalid Regex
```
Error: Invalid regex pattern '[invalid': unterminated character set
Solution: Use valid regex syntax
Correct: file_name regex_match '.*\\.pdf$'
```

### Debug Mode
Enable debug mode in your pipeline step to see detailed condition evaluation:
```yaml
- name: conditional_step
  step_catalog_id: my_step
  debug_mode: true
  condition: "document_type.primary_type == 'pdf'"
```

This will log:
- Condition being evaluated
- Data available for evaluation
- Evaluation result
- Execution time

## Integration with Existing Steps

### Updating Step Constructors
When creating custom steps, include the condition parameter:
```python
def __init__(self, id: str, name: str, enabled: bool, 
             description: str = None, tags: List[str] = None, 
             fail_step_on_document_error: bool = False, 
             debug_mode: bool = False, services: List[str] = None, 
             settings: dict = None, condition: str = None, **kwargs):
    super().__init__(id=id, name=name, enabled=enabled, 
                    description=description, tags=tags, 
                    fail_step_on_document_error=fail_step_on_document_error,
                    debug_mode=debug_mode, services=services, 
                    settings=settings, condition=condition, **kwargs)
```

### Condition Evaluation Data
The condition evaluator has access to:
- **Input Data**: All data from `input_data.data`
- **Summary Data**: All data from `input_data.summary_data`
- **Previous Step Results**: Results from earlier steps in the pipeline

## Testing Conditions

### Unit Testing
```python
from doc.proc.utils.secure_condition_evaluator import evaluate_condition

def test_my_condition():
    test_data = {
        "document_type": {
            "primary_type": "pdf",
            "confidence": 0.95
        }
    }
    
    condition = "document_type.primary_type == 'pdf' and document_type.confidence > 0.8"
    result = evaluate_condition(condition, test_data)
    assert result is True
```

### Validation Testing
```python
from doc.proc.utils.secure_condition_evaluator import validate_condition

def test_condition_validation():
    condition = "document_type.primary_type == 'pdf'"
    errors = validate_condition(condition)
    assert len(errors) == 0  # No validation errors
```

## Migration Guide

### From Static Conditions
If you were using static boolean flags:
```yaml
# Old approach
- name: process_pdfs
  step_catalog_id: pdf_processor
  enabled: true  # Always runs
```

```yaml
# New approach
- name: process_pdfs
  step_catalog_id: pdf_processor
  condition: "document_type.primary_type == 'pdf'"  # Conditional execution
```

### From Script-Based Conditions
If you were using external scripts or complex logic:
```python
# Old approach - external script
if document_type == 'pdf' and confidence > 0.8:
    run_pdf_processor()
```

```yaml
# New approach - secure condition
- name: process_pdfs
  step_catalog_id: pdf_processor
  condition: "document_type.primary_type == 'pdf' and document_type.confidence > 0.8"
```

## Conclusion

The secure condition evaluation system provides a powerful, safe way to implement dynamic workflow control in your document processing pipelines. By using this system, you can:

1. **Improve Efficiency**: Only run steps when necessary
2. **Enhance Security**: Prevent code injection attacks
3. **Increase Flexibility**: Easily modify conditions without code changes
4. **Maintain Performance**: Optimized evaluation with caching
5. **Ensure Reliability**: Comprehensive error handling and validation

This system replaces the need for external scripts or complex conditional logic while maintaining the security and performance requirements of production document processing workflows.
