#!/usr/bin/env python3
"""
Test script for the PowerPoint Text Extractor Step

This script demonstrates how to use the PowerPointTextExtractorStep class
to extract text from PowerPoint documents.

Usage:
    python test_pptx_extractor.py

Note: Requires python-pptx package to be installed:
    pip install python-pptx
"""

import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from doc.proc.step.pptx_text_extractor import PowerPointTextExtractorStep
    from doc.proc.step.step_base import StepInputOutput
    
    # Example configuration for the PowerPoint text extractor
    config = {
        "id": "pptx_extractor_001",
        "name": "PowerPoint Text Extractor",
        "enabled": True,
        "description": "Extract text and images from PowerPoint documents",
        "tags": ["text-extraction", "powerpoint", "presentation", "document-processing"],
        "fail_step_on_document_error": False,
        "debug_mode": True,
        "services": ["azure_ai_inference"],
        "settings": {
            "png_output_folder": "output_images",
            "extract_images": True,
            "extract_tables": True,
            "extract_shapes": True,
            "num_slides": -1,  # Process all slides
            "prompts": {
                "system": "You are a presentation analysis assistant. Extract text and describe images from the provided presentation slide.",
                "user": "Please extract all text content and describe any images you see in this presentation slide. Format your response with ==Extracted-Text== and ==End-Extracted-Text== tags around the text, and ==Image-Descriptions== and ==End-Image-Descriptions== tags around image descriptions."
            },
            "max_completion_tokens": 4000,
            "temperature": 0.1,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
    }
    
    # Create the step instance
    pptx_extractor = PowerPointTextExtractorStep(**config)
    
    print("PowerPoint Text Extractor Step initialized successfully!")
    print(f"Step ID: {pptx_extractor.id}")
    print(f"Step Name: {pptx_extractor.name}")
    print(f"Extract Images: {pptx_extractor.extract_images}")
    print(f"Extract Tables: {pptx_extractor.extract_tables}")
    print(f"Extract Shapes: {pptx_extractor.extract_shapes}")
    print(f"Slides to Convert: {pptx_extractor.slides_to_convert}")
    print(f"PNG Output Folder: {pptx_extractor.png_output_folder}")
    print(f"Debug Mode: {pptx_extractor.debug_mode}")
    
    # Example of how to structure input data
    sample_input = StepInputOutput(
        summary_data={"total_files": 1},
        data={
            "documents": [
                {
                    "file_path": "/path/to/sample.pptx",
                    "file_name": "sample.pptx",
                    "file_size": 2048,
                    "file_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                }
            ]
        }
    )
    
    print("\nExample input data structure:")
    print(f"Documents: {len(sample_input.data['documents'])}")
    print(f"First document: {sample_input.data['documents'][0]}")
    
    print("\nPowerPoint Text Extractor Step is ready to process presentations!")
    print("To use it, provide PowerPoint documents in the input data structure shown above.")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to install the required dependencies:")
    print("pip install python-pptx")
    print("Also ensure that the doc.proc modules are available in the Python path.")
except Exception as e:
    print(f"Error initializing PowerPoint Text Extractor: {e}")
