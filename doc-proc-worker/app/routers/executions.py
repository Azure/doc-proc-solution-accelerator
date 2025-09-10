from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from celery.result import AsyncResult

from app.models.execution import (
    BatchExecutionRequest, BatchExecution, BatchExecutionStatus,
    ActivityLog, StepOutput, BatchStatus, ActivityType
)
from app.services.execution_service import ExecutionService
from app.dependencies import get_execution_service
from app.tasks import execute_pipeline_batch

router = APIRouter()

@router.post("/", response_model=BatchExecution)
async def create_batch_execution(
    request: BatchExecutionRequest,
    service: ExecutionService = Depends(get_execution_service)
):
    """Create a new batch execution"""
    try:
        batch = await service.create_batch_execution(request)
        return batch
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create batch execution: {str(e)}")


@router.post("/{batch_id}/start")
async def start_batch_execution(
    batch_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """Start execution of a batch"""
    try:
        # Get batch execution
        batch = await service.get_batch_execution(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch execution not found")
        
        if batch.status != BatchStatus.PENDING:
            raise HTTPException(
                status_code=400, 
                detail=f"Batch is not in pending status. Current status: {batch.status}"
            )
        
        # Submit to Celery
        task = execute_pipeline_batch.delay(batch_id)
        
        # Update batch with task ID
        await service.update_batch_status(
            batch_id, 
            BatchStatus.RUNNING,
            celery_task_id=task.id
        )
        
        return {
            "message": "Batch execution started successfully",
            "batch_id": batch_id,
            "task_id": task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch execution: {str(e)}")


@router.get("/{batch_id}/status", response_model=BatchExecutionStatus)
async def get_batch_status(
    batch_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """Get status of a batch execution"""
    try:
        batch = await service.get_batch_execution(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch execution not found")
        
        # Calculate progress
        progress = 0.0
        if batch.total_documents > 0:
            progress = ((batch.completed_documents + batch.failed_documents) / batch.total_documents) * 100
        
        # Get recent activities
        recent_activities = await service.get_batch_activities(batch_id, limit=10)
        
        # Determine current step from recent activities
        current_step = None
        for activity in recent_activities:
            if activity.activity_type.value.startswith("step_") and activity.step_name:
                current_step = activity.step_name
                break
        
        return BatchExecutionStatus(
            batch_id=batch_id,
            status=batch.status,
            progress=progress,
            total_documents=batch.total_documents,
            completed_documents=batch.completed_documents,
            failed_documents=batch.failed_documents,
            started_at=batch.started_at,
            estimated_completion=batch.estimated_completion,
            current_step=current_step,
            recent_activities=recent_activities
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")


@router.get("/{batch_id}", response_model=BatchExecution)
async def get_batch_execution(
    batch_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """Get batch execution details"""
    try:
        batch = await service.get_batch_execution(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch execution not found")
        return batch
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch execution: {str(e)}")


@router.get("/", response_model=List[BatchExecution])
async def list_batch_executions(
    status: Optional[BatchStatus] = None,
    pipeline_id: Optional[str] = None,
    service: ExecutionService = Depends(get_execution_service)
):
    """List batch executions with optional filters"""
    try:
        batches = await service.list_batch_executions(status=status, pipeline_id=pipeline_id)
        return batches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list batch executions: {str(e)}")


@router.delete("/{batch_id}")
async def cancel_batch_execution(
    batch_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """Cancel a batch execution"""
    try:
        batch = await service.get_batch_execution(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch execution not found")
        
        if batch.status not in [BatchStatus.PENDING, BatchStatus.RUNNING]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel batch in status: {batch.status}"
            )
        
        # Cancel Celery task if running
        if batch.celery_task_id:
            from ..celery_app import celery_app
            celery_app.control.revoke(batch.celery_task_id, terminate=True)
        
        # Update status
        await service.update_batch_status(batch_id, BatchStatus.CANCELLED)
        
        # Log cancellation
        await service.log_activity(
            batch_execution_id=batch_id,
            activity_type=ActivityType.BATCH_CANCELLED,
            status="cancelled",
            message="Batch execution cancelled by user"
        )
        
        return {"message": "Batch execution cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel batch execution: {str(e)}")


@router.get("/{batch_id}/activities", response_model=List[ActivityLog])
async def get_batch_activities(
    batch_id: str,
    limit: int = 50,
    service: ExecutionService = Depends(get_execution_service)
):
    """Get activities for a batch execution"""
    try:
        activities = await service.get_batch_activities(batch_id, limit=limit)
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch activities: {str(e)}")


@router.get("/{batch_id}/step-outputs", response_model=List[StepOutput])
async def get_batch_step_outputs(
    batch_id: str,
    step_name: Optional[str] = None,
    document_id: Optional[str] = None,
    service: ExecutionService = Depends(get_execution_service)
):
    """Get step outputs for a batch execution"""
    try:
        outputs = await service.get_step_outputs(
            batch_id=batch_id,
            step_name=step_name,
            document_id=document_id
        )
        return outputs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get step outputs: {str(e)}")


@router.get("/{batch_id}/celery-status")
async def get_celery_task_status(
    batch_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """Get Celery task status for a batch execution"""
    try:
        batch = await service.get_batch_execution(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch execution not found")
        
        if not batch.celery_task_id:
            return {"message": "No Celery task associated with this batch"}
        
        # Get Celery task result
        task_result = AsyncResult(batch.celery_task_id)
        
        return {
            "task_id": batch.celery_task_id,
            "status": task_result.status,
            "result": task_result.result if task_result.ready() else None,
            "traceback": task_result.traceback if task_result.failed() else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Celery task status: {str(e)}")


@router.post("/{batch_id}/retry")
async def retry_batch_execution(
    batch_id: str,
    service: ExecutionService = Depends(get_execution_service)
):
    """Retry a failed batch execution"""
    try:
        batch = await service.get_batch_execution(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch execution not found")
        
        if batch.status not in [BatchStatus.FAILED, BatchStatus.CANCELLED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot retry batch in status: {batch.status}"
            )
        
        # Reset batch status
        await service.update_batch_status(
            batch_id,
            BatchStatus.PENDING,
            completed_documents=0,
            failed_documents=0,
            started_at=None,
            completed_at=None,
            celery_task_id=None
        )
        
        # Log retry
        await service.log_activity(
            batch_execution_id=batch_id,
            activity_type=ActivityType.BATCH_RETRY,
            status="pending",
            message="Batch execution reset for retry"
        )
        
        return {"message": "Batch execution reset for retry. Use /start endpoint to begin execution."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry batch execution: {str(e)}")
