"""
Custom AI Prompt Processing Pipeline Example

This script demonstrates how to:
1. Apply custom AI prompts to document content
2. Generate summaries, sentiment analysis, and extract topics
3. Chain multiple AI analysis steps
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
    """Main function to run the custom AI prompt processing pipeline."""
    
    # Paths to configuration files
    service_catalog_path = example_dir.parent.parent / 'service_catalog.yaml'
    step_catalog_path = example_dir.parent.parent / 'step_catalog.yaml'
    pipeline_config_path = example_dir / 'pipeline_config.yaml'
    
    logger.info("=" * 80)
    logger.info("Custom AI Prompt Processing Pipeline Example")
    logger.info("=" * 80)
    
    try:
        # Create pipeline from configuration files
        logger.info("Loading pipeline configuration...")
        pipeline = await create_pipeline_from_files(
            pipeline_name='custom_ai_processor',
            pipeline_config_path=str(pipeline_config_path),
            step_catalog_path=str(step_catalog_path),
            service_catalog_path=str(service_catalog_path)
        )
        
        logger.info(f"Pipeline '{pipeline.name}' loaded successfully")
        logger.info(f"Description: {pipeline.description}")
        logger.info(f"Number of steps: {len(pipeline.pipeline_execution_steps)}")
        
        # Display configured steps
        logger.info("\nConfigured AI processing steps:")
        for idx, step in enumerate(pipeline.pipeline_execution_steps, 1):
            logger.info(f"  {idx}. {step.name} ({step.__class__.__name__})")
        
        # Create sample documents for AI processing
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
            )
        ]
        
        # Create pipeline input
        pipeline_input = PipelineInput(documents=documents)
        
        logger.info(f"\nProcessing {len(documents)} document(s) with custom AI prompts...")
        
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
        
        # Display document analysis results
        logger.info(f"\nDocument Analysis Results ({len(result.document_results)}):")
        for idx, doc_result in enumerate(result.document_results, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Document {idx}: {doc_result.document_id}")
            logger.info(f"{'=' * 80}")
            logger.info(f"Result: {doc_result.result}")
            logger.info(f"Elapsed Time: {doc_result.elapsed_time_secs:.2f}s")
            
            # Display step execution summary
            logger.info(f"\nStep Execution:")
            for step_result in doc_result.step_results:
                status_icon = "✓" if step_result.result == "Succeeded" else "✗" if step_result.result == "Failed" else "○"
                logger.info(f"  {status_icon} {step_result.step_name}: {step_result.result}")
                if step_result.error:
                    logger.error(f"      Error: {step_result.error}")
            
            # Display AI analysis results
            if doc_result.data:
                logger.info(f"\n{'-' * 80}")
                logger.info("AI Analysis Results:")
                logger.info(f"{'-' * 80}")
                
                # Display summary
                if "chunks" in doc_result.data and doc_result.data["chunks"]:
                    first_chunk = doc_result.data["chunks"][0]
                    
                    if "summary" in first_chunk:
                        logger.info(f"\n📄 DOCUMENT SUMMARY:")
                        logger.info(f"{first_chunk['summary']}")
                    
                    # Display sentiment analysis
                    if "sentiment_analysis" in first_chunk:
                        logger.info(f"\n😊 SENTIMENT ANALYSIS:")
                        try:
                            sentiment = json.loads(first_chunk['sentiment_analysis']) if isinstance(first_chunk['sentiment_analysis'], str) else first_chunk['sentiment_analysis']
                            logger.info(f"  Sentiment: {sentiment.get('sentiment', 'N/A')}")
                            logger.info(f"  Tone: {sentiment.get('tone', 'N/A')}")
                            logger.info(f"  Confidence: {sentiment.get('confidence', 'N/A')}")
                            logger.info(f"  Explanation: {sentiment.get('explanation', 'N/A')}")
                        except:
                            logger.info(f"  {first_chunk['sentiment_analysis']}")
                    
                    # Display topics and entities
                    if "topics_and_entities" in first_chunk:
                        logger.info(f"\n🏷️  TOPICS & ENTITIES:")
                        try:
                            topics_data = json.loads(first_chunk['topics_and_entities']) if isinstance(first_chunk['topics_and_entities'], str) else first_chunk['topics_and_entities']
                            
                            if "topics" in topics_data:
                                logger.info(f"  Topics: {', '.join(topics_data['topics'])}")
                            
                            if "entities" in topics_data:
                                entities = topics_data['entities']
                                for entity_type, entity_list in entities.items():
                                    if entity_list:
                                        logger.info(f"  {entity_type.title()}: {', '.join(entity_list)}")
                        except:
                            logger.info(f"  {first_chunk['topics_and_entities']}")
                
                # Display chunk statistics
                if "chunks" in doc_result.data:
                    chunks = doc_result.data["chunks"]
                    logger.info(f"\n📊 Processing Statistics:")
                    logger.info(f"  Total chunks processed: {len(chunks)}")
                    
                    # Count chunks with AI results
                    chunks_with_summary = sum(1 for c in chunks if "summary" in c)
                    chunks_with_sentiment = sum(1 for c in chunks if "sentiment_analysis" in c)
                    chunks_with_topics = sum(1 for c in chunks if "topics_and_entities" in c)
                    
                    logger.info(f"  Chunks with summaries: {chunks_with_summary}")
                    logger.info(f"  Chunks with sentiment analysis: {chunks_with_sentiment}")
                    logger.info(f"  Chunks with topic extraction: {chunks_with_topics}")
        
        # Save results to file
        output_file = example_dir / "ai_analysis_results.json"
        with open(output_file, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        
        logger.info(f"\n\nFull results saved to: {output_file}")
        
        # Generate AI insights summary
        logger.info("\n" + "=" * 80)
        logger.info("AI Processing Summary")
        logger.info("=" * 80)
        
        total_documents = len(result.document_results)
        successful_documents = sum(1 for dr in result.document_results if dr.result == "Succeeded")
        
        logger.info(f"Total Documents: {total_documents}")
        logger.info(f"Successfully Processed: {successful_documents}")
        logger.info(f"Success Rate: {(successful_documents / total_documents * 100):.1f}%")
        
        logger.info("\n✓ Custom AI analysis complete!")
        logger.info("  Generated summaries, sentiment analysis, and extracted topics")
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
