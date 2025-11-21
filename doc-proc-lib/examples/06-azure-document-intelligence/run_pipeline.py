"""
Azure Document Intelligence Pipeline Example

This script demonstrates how to:
1. Use Azure Document Intelligence for structured extraction
2. Process different document types with prebuilt models
3. Extract tables, key-value pairs, and structured data
"""

import asyncio
import sys
import os
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import doc-proc-lib modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.setup_logger import setup_logging

from doc.proc.pipeline.pipeline_factory import create_pipeline_from_files
from doc.proc.models import Document, ContentIdentifier, PipelineInput

# Get the current directory
example_dir = Path(__file__).parent

# Load environment variables
load_dotenv(f'{example_dir.parent}/.env')

setup_logging()

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the Document Intelligence pipeline."""
    
    # Get the current directory
    example_dir = Path(__file__).parent
    
    # Paths to configuration files
    service_catalog_path = example_dir.parent.parent / 'service_catalog.yaml'
    step_catalog_path = example_dir.parent.parent / 'step_catalog.yaml'
    pipeline_config_path = example_dir / 'pipeline_config.yaml'
    
    logger.info("=" * 80)
    logger.info("Azure Document Intelligence Pipeline Example")
    logger.info("=" * 80)
    
    try:
        # Create pipeline from configuration files
        logger.info("Loading pipeline configuration...")
        pipeline = await create_pipeline_from_files(
            pipeline_name='document_intelligence_processor',
            pipeline_config_path=str(pipeline_config_path),
            step_catalog_path=str(step_catalog_path),
            service_catalog_path=str(service_catalog_path)
        )
        
        logger.info(f"Pipeline '{pipeline.name}' loaded successfully")
        logger.info(f"Description: {pipeline.description}")
        logger.info(f"Number of steps: {len(pipeline.pipeline_execution_steps)}")
        
        # Display configured steps
        logger.info("\nConfigured steps:")
        for idx, step in enumerate(pipeline.pipeline_execution_steps, 1):
            condition = getattr(step, 'condition', None)
            condition_text = f" [Conditional: {condition}]" if condition else ""
            logger.info(f"  {idx}. {step.name}{condition_text}")
        
        # Create sample documents for different document types
        documents = [
            # PDF document - will use layout model
            Document(
                id=ContentIdentifier(
                        canonical_id="di_doc_001",
                        unique_id="di_doc_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.pdf",
                    )
            ),
            
            # Word document - will use layout model
            Document(
                id=ContentIdentifier(
                        canonical_id="di_doc_002",
                        unique_id="di_doc_002",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.docx",
                    )
            )
        ]
        
        # Create pipeline input
        pipeline_input = PipelineInput(documents=documents)
        
        logger.info(f"\nProcessing {len(documents)} document(s) with Azure Document Intelligence...")
        logger.info("\nDocument categories:")
        for doc in documents:
            category = doc.data.get("metadata", {}).get("document_category", "general")
            logger.info(f"  • {doc.id}: {category}")
        
        # Execute the pipeline
        result = await pipeline.run(input_data=pipeline_input)
        
        logger.info("\n" + "=" * 80)
        logger.info("Pipeline Execution Results")
        logger.info("=" * 80)
        logger.info(f"Overall Result: {result.result}")
        logger.info(f"Elapsed Time: {result.elapsed_time_secs:.2f} seconds")
        
        if result.summary_stats:
            logger.info(f"\nSummary Statistics:")
            for key, value in result.summary_stats.items():
                logger.info(f"  {key}: {value}")
        
        # Display detailed extraction results
        logger.info(f"\nDocument Intelligence Extraction Results ({len(result.document_results)}):")
        for idx, doc_result in enumerate(result.document_results, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Document {idx}: {doc_result.document_id}")
            logger.info(f"{'=' * 80}")
            logger.info(f"Result: {doc_result.result}")
            logger.info(f"Elapsed Time: {doc_result.elapsed_time_secs:.2f}s")
            
            # Display step results
            logger.info(f"\nStep Execution:")
            for step_result in doc_result.step_results:
                status_icon = "✓" if step_result.result == "Succeeded" else "✗" if step_result.result == "Failed" else "○"
                logger.info(f"  {status_icon} {step_result.step_name}: {step_result.result}")
                if step_result.error:
                    logger.error(f"      Error: {step_result.error}")
            
            # Display extracted data
            if doc_result.data:
                logger.info(f"\nExtracted Data:")
                
                # Document type
                if "document_type" in doc_result.data:
                    doc_type = doc_result.data["document_type"]
                    logger.info(f"  Document Type: {doc_type.get('primary_type', 'unknown')}")
                
                # Layout extraction results
                if "doc_intell_chunks" in doc_result.data:
                    chunks = doc_result.data["doc_intell_chunks"]
                    logger.info(f"\n  📄 Layout Extraction (prebuilt-layout):")
                    logger.info(f"    Total chunks: {len(chunks)}")
                    
                    if chunks and isinstance(chunks, list):
                        # Count tables and paragraphs
                        tables_count = sum(1 for c in chunks if c.get("has_table", False))
                        paragraphs_count = sum(1 for c in chunks if c.get("has_paragraph", False))
                        
                        logger.info(f"    Tables found: {tables_count}")
                        logger.info(f"    Paragraphs found: {paragraphs_count}")
                        
                        # Show sample content
                        if len(chunks) > 0:
                            sample = chunks[0]
                            if "markdown" in sample:
                                preview = sample["markdown"][:200]
                                logger.info(f"    Sample content: {preview}...")
                
                
        
        # Save results to file
        output_file = example_dir / "doc_intelligence_results.json"
        with open(output_file, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        
        logger.info(f"\n\nFull results saved to: {output_file}")
        
        # Generate extraction summary
        logger.info("\n" + "=" * 80)
        logger.info("Document Intelligence Extraction Summary")
        logger.info("=" * 80)
        
        total_docs = len(result.document_results)
        successful_docs = sum(1 for dr in result.document_results if dr.result == "Succeeded")
        
        logger.info(f"\nTotal Documents: {total_docs}")
        logger.info(f"Successfully Processed: {successful_docs}")
        logger.info(f"Success Rate: {(successful_docs / total_docs * 100):.1f}%")
        
        logger.info("\n✓ Azure Document Intelligence processing complete!")
        logger.info("  Extracted structured data including tables, key-value pairs, and text")
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
