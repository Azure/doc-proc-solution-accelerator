import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from celery import current_task
import traceback
import sys
import os

# Add the doc-proc-lib to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib"))

from .celery_app import celery_app
from .models.execution import BatchExecution, ActivityLog, ActivityType, BatchStatus, DocumentReference, StepOutput
from .services.execution_service import ExecutionService
from .dependencies import get_cosmos_db
from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.step.step_base import StepInputOutput

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="doc_proc_backend.tasks.execute_pipeline_batch")
def execute_pipeline_batch(self, batch_execution_id: str) -> Dict[str, Any]:
    """
    Celery task to execute a pipeline batch.
    
    Args:
        batch_execution_id: ID of the batch execution to process
        
    Returns:
        Dict containing execution results
    """
    try:
        # Run the async execution in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_execute_pipeline_batch_async(batch_execution_id, self.request.id))
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to execute pipeline batch {batch_execution_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update batch status to failed
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_handle_batch_failure(batch_execution_id, str(e)))
            loop.close()
        except Exception as update_error:
            logger.error(f"Failed to update batch status after failure: {str(update_error)}")
        
        raise


@celery_app.task(bind=True, name="doc_proc_backend.tasks.process_single_document")
def process_single_document(self, batch_execution_id: str, pipeline_instance_id: str, 
                          document_ref: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task to process a single document through a pipeline.
    
    Args:
        batch_execution_id: ID of the batch execution
        pipeline_instance_id: ID of the pipeline instance
        document_ref: Document reference dict
        
    Returns:
        Dict containing processing results
    """
    try:
        # Run the async processing in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_process_single_document_async(
                batch_execution_id, pipeline_instance_id, document_ref, self.request.id
            ))
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to process document {document_ref.get('blob_name', 'unknown')}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Log the failure
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_handle_document_failure(
                batch_execution_id, document_ref, str(e)
            ))
            loop.close()
        except Exception as update_error:
            logger.error(f"Failed to log document failure: {str(update_error)}")
        
        raise


async def _execute_pipeline_batch_async(batch_execution_id: str, task_id: str) -> Dict[str, Any]:
    """Async function to execute a pipeline batch."""
    
    db = get_cosmos_db()
    execution_service = ExecutionService(db)
    
    # Get batch execution
    batch = await execution_service.get_batch_execution(batch_execution_id)
    if not batch:
        raise ValueError(f"Batch execution {batch_execution_id} not found")
    
    # Update batch status to running
    await execution_service.update_batch_status(
        batch_execution_id, 
        BatchStatus.RUNNING,
        celery_task_id=task_id,
        started_at=datetime.utcnow()
    )
    
    # Log batch start activity
    await execution_service.log_activity(
        batch_execution_id=batch_execution_id,
        activity_type=ActivityType.BATCH_STARTED,
        status="started",
        message=f"Batch execution started with {batch.total_documents} documents",
        details={"task_id": task_id, "pipeline_id": batch.pipeline_instance_id}
    )
    
    try:
        # Get pipeline instance and load pipeline
        pipeline = await execution_service.load_pipeline(batch.pipeline_instance_id)
        
        completed_documents = 0
        failed_documents = 0
        step_outputs = []
        
        # Process each document
        for doc_ref in batch.documents:
            try:
                # Create input data for the document
                input_data = StepInputOutput(
                    summary_data={
                        "batch_id": batch_execution_id,
                        "document_ref": doc_ref.model_dump(),
                        "pipeline_id": batch.pipeline_instance_id
                    },
                    data={
                        "documents": [{
                            "container_name": doc_ref.container_name,
                            "blob_name": doc_ref.blob_name,
                            "url": doc_ref.url,
                            "content_type": doc_ref.content_type,
                            "size_bytes": doc_ref.size_bytes
                        }]
                    }
                )
                
                # Execute pipeline for this document
                result = await pipeline.run(input_data)
                
                # Store step outputs
                for step_result in result.step_execution_results:
                    step_output = StepOutput(
                        step_name=step_result.step_name,
                        step_instance_id=step_result.step_name,  # TODO: Get actual step instance ID
                        document_id=doc_ref.blob_name,
                        output_data=result.data,
                        summary_data=result.summary_data,
                        execution_time_ms=int(step_result.elapsed_time_secs * 1000),
                        status=step_result.result,
                        error_message=step_result.error_message
                    )
                    await execution_service.store_step_output(step_output)
                    step_outputs.append(step_output)
                
                if result.result in ["Succeeded", "PartialSucceeded"]:
                    completed_documents += 1
                    await execution_service.log_activity(
                        batch_execution_id=batch_execution_id,
                        activity_type=ActivityType.DOCUMENT_PROCESSED,
                        document_id=doc_ref.blob_name,
                        status="completed",
                        message=f"Document processed successfully",
                        details={"result_status": result.result}
                    )
                else:
                    failed_documents += 1
                    await execution_service.log_activity(
                        batch_execution_id=batch_execution_id,
                        activity_type=ActivityType.DOCUMENT_FAILED,
                        document_id=doc_ref.blob_name,
                        status="failed",
                        message=f"Document processing failed",
                        error_message=result.reason,
                        details={"result_status": result.result}
                    )
                
                # Update progress
                await execution_service.update_batch_progress(
                    batch_execution_id, completed_documents, failed_documents
                )
                
            except Exception as doc_error:
                failed_documents += 1
                logger.error(f"Failed to process document {doc_ref.blob_name}: {str(doc_error)}")
                
                await execution_service.log_activity(
                    batch_execution_id=batch_execution_id,
                    activity_type=ActivityType.DOCUMENT_FAILED,
                    document_id=doc_ref.blob_name,
                    status="failed",
                    message=f"Document processing failed with exception",
                    error_message=str(doc_error),
                    details={"exception_type": type(doc_error).__name__}
                )
        
        # Complete the batch
        final_status = BatchStatus.COMPLETED if failed_documents == 0 else BatchStatus.COMPLETED
        await execution_service.update_batch_status(
            batch_execution_id,
            final_status,
            completed_at=datetime.utcnow(),
            completed_documents=completed_documents,
            failed_documents=failed_documents
        )
        
        # Log batch completion
        await execution_service.log_activity(
            batch_execution_id=batch_execution_id,
            activity_type=ActivityType.BATCH_COMPLETED,
            status="completed",
            message=f"Batch execution completed. Processed: {completed_documents}, Failed: {failed_documents}",
            details={
                "total_documents": batch.total_documents,
                "completed_documents": completed_documents,
                "failed_documents": failed_documents,
                "step_outputs_count": len(step_outputs)
            }
        )
        
        return {
            "batch_id": batch_execution_id,
            "status": final_status.value,
            "completed_documents": completed_documents,
            "failed_documents": failed_documents,
            "total_step_outputs": len(step_outputs)
        }
        
    except Exception as e:
        await _handle_batch_failure(batch_execution_id, str(e))
        raise


async def _process_single_document_async(batch_execution_id: str, pipeline_instance_id: str, 
                                       document_ref: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    """Async function to process a single document."""
    
    db = get_cosmos_db()
    execution_service = ExecutionService(db)
    
    doc_ref = DocumentReference(**document_ref)
    
    try:
        # Load pipeline
        pipeline = await execution_service.load_pipeline(pipeline_instance_id)
        
        # Create input data
        input_data = StepInputOutput(
            summary_data={
                "batch_id": batch_execution_id,
                "document_ref": doc_ref.model_dump(),
                "pipeline_id": pipeline_instance_id,
                "task_id": task_id
            },
            data={
                "documents": [doc_ref.model_dump()]
            }
        )
        
        # Execute pipeline
        result = await pipeline.run(input_data)
        
        # Store step outputs
        step_outputs = []
        for step_result in result.step_execution_results:
            step_output = StepOutput(
                step_name=step_result.step_name,
                step_instance_id=step_result.step_name,
                document_id=doc_ref.blob_name,
                output_data=result.data,
                summary_data=result.summary_data,
                execution_time_ms=int(step_result.elapsed_time_secs * 1000),
                status=step_result.result,
                error_message=step_result.error_message
            )
            await execution_service.store_step_output(step_output)
            step_outputs.append(step_output)
        
        # Log document processing
        if result.result in ["Succeeded", "PartialSucceeded"]:
            await execution_service.log_activity(
                batch_execution_id=batch_execution_id,
                activity_type=ActivityType.DOCUMENT_PROCESSED,
                document_id=doc_ref.blob_name,
                status="completed",
                message="Document processed successfully",
                details={"result_status": result.result, "task_id": task_id}
            )
        else:
            await execution_service.log_activity(
                batch_execution_id=batch_execution_id,
                activity_type=ActivityType.DOCUMENT_FAILED,
                document_id=doc_ref.blob_name,
                status="failed",
                message="Document processing failed",
                error_message=result.reason,
                details={"result_status": result.result, "task_id": task_id}
            )
        
        return {
            "document_id": doc_ref.blob_name,
            "status": result.result,
            "step_outputs_count": len(step_outputs)
        }
        
    except Exception as e:
        await _handle_document_failure(batch_execution_id, doc_ref.model_dump(), str(e))
        raise


async def _handle_batch_failure(batch_execution_id: str, error_message: str):
    """Handle batch execution failure."""
    db = get_cosmos_db()
    execution_service = ExecutionService(db)
    
    await execution_service.update_batch_status(
        batch_execution_id,
        BatchStatus.FAILED,
        completed_at=datetime.utcnow()
    )
    
    await execution_service.log_activity(
        batch_execution_id=batch_execution_id,
        activity_type=ActivityType.BATCH_FAILED,
        status="failed",
        message="Batch execution failed",
        error_message=error_message
    )


async def _handle_document_failure(batch_execution_id: str, document_ref: Dict[str, Any], error_message: str):
    """Handle document processing failure."""
    db = get_cosmos_db()
    execution_service = ExecutionService(db)
    
    await execution_service.log_activity(
        batch_execution_id=batch_execution_id,
        activity_type=ActivityType.DOCUMENT_FAILED,
        document_id=document_ref.get("blob_name", "unknown"),
        status="failed",
        message="Document processing failed",
        error_message=error_message
    )
