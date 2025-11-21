"""
AI Search Indexing Pipeline Example

This script demonstrates how to:
1. Extract content from documents
2. Write extracted content to Azure AI Search index
3. Make documents searchable
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
    """Main function to run the AI Search indexing pipeline."""
    
    # Get the current directory
    example_dir = Path(__file__).parent
    
    # Paths to configuration files
    service_catalog_path = example_dir.parent.parent / 'service_catalog.yaml'
    step_catalog_path = example_dir.parent.parent / 'step_catalog.yaml'
    pipeline_config_path = example_dir / 'pipeline_config.yaml'
    
    logger.info("=" * 80)
    logger.info("AI Search Indexing Pipeline Example")
    logger.info("=" * 80)
    
    try:
        # Create pipeline from configuration files
        logger.info("Loading pipeline configuration...")
        pipeline = await create_pipeline_from_files(
            pipeline_name='ai_search_indexer',
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
        
        # Create sample documents to index
        documents = [
            Document(
                id="idx_doc_001",
                id=ContentIdentifier(
                        canonical_id="idx_doc_001",
                        unique_id="idx_doc_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.pdf",
                    ),
                data={
                    "source": "technical_docs",
                    "category": "manual",
                    "description": "Technical documentation to be indexed"
                }
            )
        ]
        
        # Create pipeline input
        pipeline_input = PipelineInput(documents=documents)
        
        logger.info(f"\nProcessing and indexing {len(documents)} document(s)...")
        
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
        
        # Track indexing statistics
        total_chunks_indexed = 0
        documents_indexed = 0
        documents_failed = 0
        
        # Display document results
        logger.info(f"\nDocument Indexing Results ({len(result.document_results)}):")
        for idx, doc_result in enumerate(result.document_results, 1):
            logger.info(f"\n  Document {idx}: {doc_result.document_id}")
            logger.info(f"    Result: {doc_result.result}")
            logger.info(f"    Elapsed Time: {doc_result.elapsed_time_secs:.2f}s")
            
            if doc_result.result == "Succeeded":
                documents_indexed += 1
            else:
                documents_failed += 1
            
            # Display step results
            logger.info(f"    Step Results:")
            for step_result in doc_result.step_results:
                status_icon = "✓" if step_result.result == "Succeeded" else "✗" if step_result.result == "Failed" else "○"
                logger.info(f"      {status_icon} {step_result.step_name}: {step_result.result}")
                
                # Special handling for search index writer
                if step_result.step_name == "search_index_writer" and step_result.result == "Succeeded":
                    if doc_result.data and "chunks" in doc_result.data:
                        num_chunks = len(doc_result.data["chunks"])
                        total_chunks_indexed += num_chunks
                        logger.info(f"        Indexed {num_chunks} chunks to search index")
                
                if step_result.error:
                    logger.error(f"        Error: {step_result.error}")
            
            # Display extracted chunks info
            if doc_result.data and "chunks" in doc_result.data:
                chunks = doc_result.data["chunks"]
                logger.info(f"    Total chunks extracted: {len(chunks)}")
        
        # Save results to file
        output_file = example_dir / "indexing_results.json"
        with open(output_file, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        
        logger.info(f"\nFull results saved to: {output_file}")
        
        # Display indexing summary
        logger.info("\n" + "=" * 80)
        logger.info("Indexing Summary")
        logger.info("=" * 80)
        logger.info(f"Total Documents Processed: {len(documents)}")
        logger.info(f"Documents Successfully Indexed: {documents_indexed}")
        logger.info(f"Documents Failed: {documents_failed}")
        logger.info(f"Total Chunks Indexed: {total_chunks_indexed}")
        logger.info(f"Success Rate: {(documents_indexed / len(documents) * 100):.1f}%")
        
        if total_chunks_indexed > 0:
            logger.info(f"\n✓ Successfully indexed {total_chunks_indexed} searchable chunks")
            logger.info(f"  Documents are now searchable in Azure AI Search index")
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
