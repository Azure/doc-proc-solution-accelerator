#!/usr/bin/env python3
"""
Test script for the Word Text Extractor Step

This script demonstrates how to use the WordTextExtractorStep class
to extract text from Word documents.

Usage:
    python test_word_extractor.py

Note: Requires python-docx package to be installed:
    pip install python-docx
"""

import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from doc.proc.step.word_text_extractor import WordTextExtractorStep
    from doc.proc.step.step_base import StepInputOutput
    
    # Example configuration for the Word text extractor
    config = {
        "id": "word_extractor_001",
        "name": "Word Text Extractor",
        "enabled": True,
        "description": "Extract text and images from Word documents",
        "tags": ["text-extraction", "word", "document-processing"],
        "fail_step_on_document_error": False,
        "debug_mode": True,
        "services": ["azure_ai_inference"],
        "settings": {
            "png_output_folder": "output_images",
            "extract_images": True,
            "extract_tables": True,
            "prompts": {
                "system": "You are a document analysis assistant. Extract text and describe images from the provided document page.",
                "user": "Please extract all text content and describe any images you see in this document page. Format your response with ==Extracted-Text== and ==End-Extracted-Text== tags around the text, and ==Image-Descriptions== and ==End-Image-Descriptions== tags around image descriptions."
            },
            "max_completion_tokens": 4000,
            "temperature": 0.1,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
    }
    
    # Create the step instance
    word_extractor = WordTextExtractorStep(**config)
    
    print("Word Text Extractor Step initialized successfully!")
    print(f"Step ID: {word_extractor.id}")
    print(f"Step Name: {word_extractor.name}")
    print(f"Extract Images: {word_extractor.extract_images}")
    print(f"Extract Tables: {word_extractor.extract_tables}")
    print(f"PNG Output Folder: {word_extractor.png_output_folder}")
    print(f"Debug Mode: {word_extractor.debug_mode}")
    
    # Example of how to structure input data
    sample_input = StepInputOutput(
        summary_data={"total_files": 1},
        data={
            "documents": [
                {
                    "file_path": "/path/to/sample.docx",
                    "file_name": "sample.docx",
                    "file_size": 1024,
                    "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                }
            ]
        }
    )
    
    print("\nExample input data structure:")
    print(f"Documents: {len(sample_input.data['documents'])}")
    print(f"First document: {sample_input.data['documents'][0]}")
    
    print("\nWord Text Extractor Step is ready to process documents!")
    print("To use it, provide Word documents in the input data structure shown above.")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to install the required dependencies:")
    print("pip install python-docx")
    print("Also ensure that the doc.proc modules are available in the Python path.")
except Exception as e:
    print(f"Error initializing Word Text Extractor: {e}")
