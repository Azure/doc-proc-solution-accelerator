"""
Basic PDF Processing Pipeline Example

This script demonstrates how to:
1. Load a pipeline from YAML configuration
2. Create document input
3. Execute the pipeline
4. Process results
"""

import asyncio
import sys
import os
import logging
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
    """Main function to run the PDF processing pipeline."""
    
    # Paths to configuration files
    # Note: We use the shared catalogs from the parent doc-proc-lib directory
    service_catalog_path = example_dir.parent.parent / 'service_catalog.yaml'
    step_catalog_path = example_dir.parent.parent / 'step_catalog.yaml'
    pipeline_config_path = example_dir / 'pipeline_config.yaml'
    
    logger.info("=" * 80)
    logger.info("Basic PDF Processing Pipeline Example")
    logger.info("=" * 80)
    
    try:
        # Create pipeline from configuration files
        logger.info("Loading pipeline configuration...")
        pipeline = await create_pipeline_from_files(
            pipeline_name='basic_pdf_processor',
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
            logger.info(f"  {idx}. {step.name} ({step.__class__.__name__})")
        
        # Create sample document input
        # You can specify either file_path or blob_details
        documents = [
            Document(
                id=ContentIdentifier(
                        canonical_id="doc_pdf_001",
                        unique_id="doc_pdf_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.pdf",
                    )
            )
        ]
        
        # Alternative: Process from blob storage
        # documents = [
        #     Document(
        #         id="doc_002",
        #         blob_details={
        #             "container": "documents",
        #             "blob": "samples/document.pdf"
        #         },
        #         data={
        #             "source": "azure_blob",
        #             "description": "PDF from blob storage"
        #         }
        #     )
        # ]
        
        # Create pipeline input
        pipeline_input = PipelineInput(documents=documents)
        
        logger.info(f"\nProcessing {len(documents)} document(s)...")
        
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
        
        # Display document results
        logger.info(f"\nDocument Results ({len(result.document_results)}):")
        for idx, doc_result in enumerate(result.document_results, 1):
            logger.info(f"\n  Document {idx}: {doc_result.document_id}")
            logger.info(f"    Result: {doc_result.result}")
            logger.info(f"    Elapsed Time: {doc_result.elapsed_time_secs:.2f}s")
            
            # Display step results
            logger.info(f"    Step Results:")
            for step_result in doc_result.step_results:
                logger.info(f"      - {step_result.step_name}: {step_result.result}")
                if step_result.error:
                    logger.error(f"        Error: {step_result.error}")
            
            # Display extracted data
            if doc_result.data and "chunks" in doc_result.data:
                chunks = doc_result.data["chunks"]
                logger.info(f"    Extracted {len(chunks)} chunks from document")
                
                # Show first chunk as sample
                if chunks:
                    logger.info(f"    Sample chunk (first page):")
                    first_chunk = chunks[0]
                    if "markdown_text" in first_chunk:
                        preview = first_chunk["markdown_text"][:200]
                        logger.info(f"      {preview}...")
        
        # Save results to file
        output_file = example_dir / "pipeline_results.json"
        with open(output_file, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        
        logger.info(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
