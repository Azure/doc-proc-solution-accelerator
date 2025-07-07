"""
Example demonstrating secure condition evaluation in document processing pipelines.
"""

from doc.proc.utils.secure_condition_evaluator import evaluate_condition, validate_condition


def main():
    """Demonstrate condition evaluation with example document data."""
    
    # Example document data that would be available during pipeline execution
    document_data = {
        "documents": [
            {
                "file_path": "/path/to/contract.pdf",
                "file_name": "contract.pdf",
                "file_size": 2048576,  # 2MB
                "document_type": {
                    "primary_type": "pdf",
                    "mime_type": "application/pdf",
                    "confidence": 0.95,
                    "category": "pdf",
                    "subtype": "pdf"
                },
                "metadata": {
                    "pages": 12,
                    "author": "Legal Department",
                    "encrypted": False,
                    "creation_date": "2024-01-15",
                    "tags": ["contract", "important", "legal"]
                }
            }
        ]
    }
    
    # Example conditions that might be used in pipeline steps
    conditions = [
        # Simple type check
        "document_type.primary_type == 'pdf'",
        
        # Confidence threshold
        "document_type.confidence > 0.8",
        
        # File size check (files larger than 1MB)
        "file_size >= 1048576",
        
        # Multiple document types
        "document_type.category in ['pdf', 'office_document']",
        
        # Tag-based processing
        "'important' in metadata.tags",
        
        # Filename pattern matching
        "file_name ends_with '.pdf'",
        
        # Complex logical condition
        "document_type.primary_type == 'pdf' and document_type.confidence > 0.8 and file_size < 5242880",
        
        # Metadata checks
        "metadata.encrypted == false and metadata.pages > 5",
        
        # Array access
        "metadata.tags[0] == 'contract'",
        
        # Empty/null checks
        "metadata.author is_not_empty"
    ]
    
    print("=== Secure Condition Evaluation Demo ===\n")
    
    # First, let's validate all conditions
    print("1. Validating Conditions:")
    print("-" * 40)
    
    for i, condition in enumerate(conditions, 1):
        errors = validate_condition(condition)
        status = "✓ Valid" if not errors else f"✗ Invalid: {', '.join(errors)}"
        print(f"{i:2d}. {condition}")
        print(f"    {status}")
    
    print("\n2. Evaluating Conditions Against Document Data:")
    print("-" * 50)
    
    # Extract the first document for evaluation
    first_doc = document_data["documents"][0]
    
    # Evaluate each condition
    for i, condition in enumerate(conditions, 1):
        try:
            result = evaluate_condition(condition, first_doc)
            status = "✓ TRUE" if result else "✗ FALSE"
            print(f"{i:2d}. {condition}")
            print(f"    Result: {status}")
        except Exception as e:
            print(f"{i:2d}. {condition}")
            print(f"    Error: {e}")
    
    print("\n3. Practical Pipeline Examples:")
    print("-" * 35)
    
    # Example pipeline step conditions
    pipeline_examples = [
        {
            "step_name": "PDF Text Extractor",
            "condition": "document_type.primary_type == 'pdf'",
            "description": "Only extract text from PDF documents"
        },
        {
            "step_name": "High-Quality OCR",
            "condition": "document_type.confidence > 0.9 and file_size < 10485760",
            "description": "Use advanced OCR for high-confidence, reasonably-sized documents"
        },
        {
            "step_name": "Legal Document Processor",
            "condition": "'legal' in metadata.tags or 'contract' in metadata.tags",
            "description": "Special processing for legal documents"
        },
        {
            "step_name": "Large File Handler",
            "condition": "file_size >= 10485760",
            "description": "Special handling for files larger than 10MB"
        },
        {
            "step_name": "Security Scanner",
            "condition": "document_type.primary_type == 'pdf' and metadata.encrypted == false",
            "description": "Scan unencrypted PDFs for security issues"
        }
    ]
    
    for example in pipeline_examples:
        result = evaluate_condition(example["condition"], first_doc)
        status = "WILL RUN" if result else "WILL SKIP"
        print(f"Step: {example['step_name']}")
        print(f"Condition: {example['condition']}")
        print(f"Description: {example['description']}")
        print(f"Status: {status}")
        print()
    
    print("4. Security Features Demo:")
    print("-" * 26)
    
    # Demonstrate security features by showing what gets blocked
    malicious_attempts = [
        "document_type.__class__.__name__ == 'dict'",
        "file_name == 'test.pdf'; import os; os.system('ls')",
        "eval('1+1') == 2",
        "__import__('os').system('rm -rf /')"
    ]
    
    print("The following potentially dangerous conditions are blocked:")
    for attempt in malicious_attempts:
        try:
            result = evaluate_condition(attempt, first_doc)
            print(f"✗ SECURITY FAILURE: '{attempt}' was not blocked!")
        except Exception as e:
            print(f"✓ BLOCKED: '{attempt}' - {str(e)}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
