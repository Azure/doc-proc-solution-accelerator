"""
Conditional Step Execution Pipeline Example

This script demonstrates how to:
1. Configure conditional step execution
2. Use different conditions for different document types
3. Track which steps executed for each document
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
    """Main function to run the conditional execution pipeline."""
    
    # Paths to configuration files
    service_catalog_path = example_dir.parent.parent / 'service_catalog.yaml'
    step_catalog_path = example_dir.parent.parent / 'step_catalog.yaml'
    pipeline_config_path = example_dir / 'pipeline_config.yaml'
    
    logger.info("=" * 80)
    logger.info("Conditional Step Execution Pipeline Example")
    logger.info("=" * 80)
    
    try:
        # Create pipeline from configuration files
        logger.info("Loading pipeline configuration...")
        pipeline = await create_pipeline_from_files(
            pipeline_name='conditional_processor',
            pipeline_config_path=str(pipeline_config_path),
            step_catalog_path=str(step_catalog_path),
            service_catalog_path=str(service_catalog_path)
        )
        
        logger.info(f"Pipeline '{pipeline.name}' loaded successfully")
        logger.info(f"Description: {pipeline.description}")
        logger.info(f"Number of steps: {len(pipeline.pipeline_execution_steps)}")
        
        # Display configured steps with their conditions
        logger.info("\nConfigured steps with conditions:")
        for idx, step in enumerate(pipeline.pipeline_execution_steps, 1):
            condition = getattr(step, 'condition', None)
            if condition:
                logger.info(f"  {idx}. {step.name}")
                logger.info(f"      Condition: {condition}")
            else:
                logger.info(f"  {idx}. {step.name} (always executes)")
        
        # Create sample documents with different properties to trigger different conditions
        documents = [
            # Small PDF, no priority - will trigger basic PDF processing
            Document(
                id=ContentIdentifier(
                        canonical_id="cond_doc_001",
                        unique_id="cond_doc_001",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.pdf",
                    ),
                data={ # simulate metadata for condition evaluation
                    "source": "local",
                    "description": "Small PDF document",
                    "file_size": 512000,  # 500KB
                    "metadata": {
                        "priority": "normal",
                        "tags": ["general"]
                    }
                }
            ),
            
            # Large PDF, high priority - will trigger multiple conditional steps
            Document(
                id=ContentIdentifier(
                        canonical_id="cond_doc_002",
                        unique_id="cond_doc_002",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.pdf",
                    ),
                data={ # simulate metadata for condition evaluation
                    "source": "local",
                    "description": "Large high-priority PDF",
                    "file_size": 2048000,  # 2MB
                    "metadata": {
                        "priority": "high",
                        "tags": ["important", "financial"]
                    }
                }
            ),
            
            # Word document, normal priority
            Document(
                id=ContentIdentifier(
                        canonical_id="cond_doc_003",
                        unique_id="cond_doc_003",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.docx",
                    ),
                data={ # simulate metadata for condition evaluation
                    "source": "local",
                    "description": "Word document",
                    "file_size": 1536000,  # 1.5MB
                    "metadata": {
                        "priority": "normal",
                        "tags": ["report"]
                    }
                }
            ),
            
            # Financial PDF with specific tags
            Document(
                id=ContentIdentifier(
                        canonical_id="cond_doc_004",
                        unique_id="cond_doc_004",
                        source_id="local_file_source",
                        source_name="local_file",
                        source_type="local_file",
                        path=f"{example_dir.parent}/sample_files/sample.pdf",
                    ),
                data={ # simulate metadata for condition evaluation
                    "source": "local",
                    "description": "Financial statement",
                    "file_size": 800000,  # 800KB
                    "metadata": {
                        "priority": "high",
                        "tags": ["financial", "quarterly"]
                    }
                }
            )
        ]
        
        # Create pipeline input
        pipeline_input = PipelineInput(documents=documents)
        
        logger.info(f"\nProcessing {len(documents)} document(s) with conditional steps...")
        logger.info("\nDocument overview:")
        for doc in documents:
            size_mb = doc.data.get("file_size", 0) / 1024 / 1024
            priority = doc.data.get("metadata", {}).get("priority", "normal")
            tags = ", ".join(doc.data.get("metadata", {}).get("tags", []))
            logger.info(f"  • {doc.id}: {size_mb:.2f}MB, Priority: {priority}, Tags: {tags}")
        
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
        
        # Display detailed document results with condition evaluation
        logger.info(f"\nDetailed Document Results ({len(result.document_results)}):")
        for idx, doc_result in enumerate(result.document_results, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Document {idx}: {doc_result.document_id}")
            logger.info(f"{'=' * 80}")
            logger.info(f"Overall Result: {doc_result.result}")
            logger.info(f"Elapsed Time: {doc_result.elapsed_time_secs:.2f}s")
            
            # Categorize steps by execution status
            executed_steps = []
            skipped_steps = []
            failed_steps = []
            
            for step_result in doc_result.step_results:
                if step_result.result == "Succeeded":
                    executed_steps.append(step_result.step_name)
                elif step_result.result == "Skipped":
                    skipped_steps.append(step_result.step_name)
                elif step_result.result == "Failed":
                    failed_steps.append(step_result.step_name)
            
            # Display executed steps
            if executed_steps:
                logger.info(f"\n✓ Executed Steps ({len(executed_steps)}):")
                for step_name in executed_steps:
                    logger.info(f"  • {step_name}")
            
            # Display skipped steps
            if skipped_steps:
                logger.info(f"\n○ Skipped Steps ({len(skipped_steps)}) - Conditions not met:")
                for step_name in skipped_steps:
                    logger.info(f"  • {step_name}")
            
            # Display failed steps
            if failed_steps:
                logger.info(f"\n✗ Failed Steps ({len(failed_steps)}):")
                for step_name in failed_steps:
                    step_result = next(sr for sr in doc_result.step_results if sr.step_name == step_name)
                    logger.info(f"  • {step_name}: {step_result.error}")
            
            # Display processing results
            if doc_result.data:
                logger.info(f"\nProcessing Results:")
                
                # Document type
                if "document_type" in doc_result.data:
                    doc_type = doc_result.data["document_type"]
                    logger.info(f"  Type: {doc_type.get('primary_type', 'unknown')}")
                    logger.info(f"  Confidence: {doc_type.get('confidence', 0):.2f}")
                
                # File size
                if "file_size" in doc_result.data:
                    size_mb = doc_result.data["file_size"] / 1024 / 1024
                    logger.info(f"  Size: {size_mb:.2f} MB")
                
                # Extracted chunks
                if "chunks" in doc_result.data:
                    chunks = doc_result.data["chunks"]
                    logger.info(f"  Extracted Chunks: {len(chunks)}")
                    
                    # Show which custom analyses were performed
                    analyses = []
                    if chunks and isinstance(chunks, list) and len(chunks) > 0:
                        sample_chunk = chunks[0]
                        if "large_file_summary" in sample_chunk:
                            analyses.append("Large File Summary")
                        if "priority_analysis" in sample_chunk:
                            analyses.append("Priority Analysis")
                        if "detailed_analysis" in sample_chunk:
                            analyses.append("Detailed Analysis")
                        if "financial_analysis" in sample_chunk:
                            analyses.append("Financial Analysis")
                    
                    if analyses:
                        logger.info(f"  AI Analyses: {', '.join(analyses)}")
        
        # Save results to file
        output_file = example_dir / "conditional_execution_results.json"
        with open(output_file, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        
        logger.info(f"\n\nFull results saved to: {output_file}")
        
        # Generate condition execution summary
        logger.info("\n" + "=" * 80)
        logger.info("Conditional Execution Summary")
        logger.info("=" * 80)
        
        # Count step execution across all documents
        step_execution_count = {}
        for doc_result in result.document_results:
            for step_result in doc_result.step_results:
                step_name = step_result.step_name
                if step_name not in step_execution_count:
                    step_execution_count[step_name] = {"executed": 0, "skipped": 0, "failed": 0}
                
                if step_result.result == "Succeeded":
                    step_execution_count[step_name]["executed"] += 1
                elif step_result.result == "Skipped":
                    step_execution_count[step_name]["skipped"] += 1
                elif step_result.result == "Failed":
                    step_execution_count[step_name]["failed"] += 1
        
        logger.info("\nStep Execution Frequency:")
        for step_name, counts in step_execution_count.items():
            total = counts["executed"] + counts["skipped"] + counts["failed"]
            exec_rate = (counts["executed"] / total * 100) if total > 0 else 0
            logger.info(f"\n{step_name}:")
            logger.info(f"  Executed: {counts['executed']}/{total} ({exec_rate:.1f}%)")
            logger.info(f"  Skipped: {counts['skipped']}")
            logger.info(f"  Failed: {counts['failed']}")
        
        logger.info("\n✓ Conditional execution demonstration complete!")
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
