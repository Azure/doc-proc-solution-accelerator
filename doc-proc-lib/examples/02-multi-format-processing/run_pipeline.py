"""
Multi-Format Document Processing Pipeline Example

This script demonstrates how to:
1. Process multiple document formats in a single pipeline
2. Use conditional step execution based on document type
3. Handle batch processing of mixed document types
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
    """Main function to run the multi-format processing pipeline."""
    
    # Paths to configuration files
    service_catalog_path = example_dir.parent.parent / 'service_catalog.yaml'
    step_catalog_path = example_dir.parent.parent / 'step_catalog.yaml'
    pipeline_config_path = example_dir / 'pipeline_config.yaml'
    
    logger.info("=" * 80)
    logger.info("Multi-Format Document Processing Pipeline Example")
    logger.info("=" * 80)
    
    try:
        # Create pipeline from configuration files
        logger.info("Loading pipeline configuration...")
        pipeline = await create_pipeline_from_files(
            pipeline_name='multi_format_processor',
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
            logger.info(f"  {idx}. {step.name} ({step.__class__.__name__}){condition_text}")
        
        # Create sample documents with different formats
        documents = [
            Document(
                id=ContentIdentifier(
                        canonical_id="doc_pdf_001",
                        unique_id="doc_pdf_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.pdf",
                    ),
                data={
                    "source": "local_file",
                    "description": "Sample PDF document"
                }
            ),
            Document(
                id=ContentIdentifier(
                        canonical_id="doc_word_001",
                        unique_id="doc_word_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.docx",
                    ),
                data={
                    "source": "local_file",
                    "description": "Sample Word document"
                }
            ),
            Document(
                id=ContentIdentifier(
                        canonical_id="doc_pptx_001",
                        unique_id="doc_pptx_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.pptx",
                    ),
                data={
                    "source": "local_file",
                    "description": "Sample PowerPoint presentation"
                }
            ),
            Document(
                id=ContentIdentifier(
                        canonical_id="doc_excel_001",
                        unique_id="doc_excel_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.xlsx",
                    ),
                data={
                    "source": "local_file",
                    "description": "Sample Excel spreadsheet"
                }
            )
        ]
        
        # Create pipeline input
        pipeline_input = PipelineInput(documents=documents)
        
        logger.info(f"\nProcessing {len(documents)} document(s) of various formats...")
        logger.info("Documents to process:")
        for doc in documents:
            logger.info(f"  - {doc.id}: {Path(doc.id.path).suffix if doc.id.path else 'blob'}")
        
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
        
        # Display document results grouped by format
        logger.info(f"\nDocument Results ({len(result.document_results)}):")
        for idx, doc_result in enumerate(result.document_results, 1):
            logger.info(f"\n  Document {idx}: {doc_result.document_id}")
            logger.info(f"    Result: {doc_result.result}")
            logger.info(f"    Elapsed Time: {doc_result.elapsed_time_secs:.2f}s")
            
            # Determine which extractor was used
            extractor_used = None
            for step_result in doc_result.step_results:
                if "extractor" in step_result.step_name.lower() and step_result.result == "Succeeded":
                    extractor_used = step_result.step_name
                    break
            
            if extractor_used:
                logger.info(f"    Extractor Used: {extractor_used}")
            
            # Display step results
            logger.info(f"    Step Execution:")
            for step_result in doc_result.step_results:
                status_icon = "✓" if step_result.result == "Succeeded" else "✗" if step_result.result == "Failed" else "○"
                logger.info(f"      {status_icon} {step_result.step_name}: {step_result.result}")
                if step_result.error:
                    logger.error(f"        Error: {step_result.error}")
            
            # Display extracted data
            if doc_result.data:
                if "chunks" in doc_result.data:
                    chunks = doc_result.data["chunks"]
                    logger.info(f"    Extracted {len(chunks)} chunks from document")
                
                # Show document type
                if "document_type" in doc_result.data:
                    doc_type = doc_result.data["document_type"]
                    logger.info(f"    Detected Type: {doc_type.get('primary_type', 'unknown')}")
        
        # Save results to file
        output_file = example_dir / "pipeline_results.json"
        with open(output_file, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        
        logger.info(f"\nFull results saved to: {output_file}")
        
        # Generate summary report
        logger.info("\n" + "=" * 80)
        logger.info("Processing Summary by Document Type")
        logger.info("=" * 80)
        
        type_summary = {}
        for doc_result in result.document_results:
            doc_type = doc_result.data.get("document_type", {}).get("primary_type", "unknown") if doc_result.data else "unknown"
            if doc_type not in type_summary:
                type_summary[doc_type] = {"total": 0, "succeeded": 0, "failed": 0}
            
            type_summary[doc_type]["total"] += 1
            if doc_result.result == "Succeeded":
                type_summary[doc_type]["succeeded"] += 1
            else:
                type_summary[doc_type]["failed"] += 1
        
        for doc_type, stats in type_summary.items():
            logger.info(f"\n{doc_type.upper()}:")
            logger.info(f"  Total: {stats['total']}")
            logger.info(f"  Succeeded: {stats['succeeded']}")
            logger.info(f"  Failed: {stats['failed']}")
            success_rate = (stats['succeeded'] / stats['total'] * 100) if stats['total'] > 0 else 0
            logger.info(f"  Success Rate: {success_rate:.1f}%")
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
