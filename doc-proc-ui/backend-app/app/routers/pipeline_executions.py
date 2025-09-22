from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.execution import PipelineExecutionResult
from app.services.pipeline_execution_service import PipelineExecutionService
from app.dependencies import get_pipeline_execution_service
from app.exceptions import ApiException

router = APIRouter(prefix="/api/pipeline-executions", tags=["pipeline-executions"])


@router.get("/", response_model=List[PipelineExecutionResult])
async def list_pipeline_executions(
    batch_execution_id: Optional[str] = Query(None, description="Filter by batch execution ID"),
    pipeline_name: Optional[str] = Query(None, description="Filter by pipeline name"),
    limit: int = Query(50, ge=1, le=600, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """List pipeline executions with optional filters"""
    try:
        executions = await service.list_pipeline_executions(
            batch_execution_id=batch_execution_id,
            pipeline_name=pipeline_name,
            limit=limit,
            offset=offset
        )
        return executions
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to list pipeline executions", details=f"Failed to list pipeline executions: {str(e)}")


@router.get("/recent", response_model=List[PipelineExecutionResult])
async def get_recent_pipeline_executions(
    pipeline_name: Optional[str] = Query(None, description="Filter by pipeline name"),
    limit: int = Query(20, ge=1, le=600, description="Maximum number of results to return"),
    time_range: Optional[str] = Query("24h", description="Time range filter: 1h, 4h, 24h, 7d, 30d"),
    service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Get recent pipeline executions within specified time range"""
    try:
        executions = await service.get_recent_pipeline_executions(pipeline_name=pipeline_name, limit=limit, time_range=time_range)
        return executions
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to get recent pipeline executions", details=f"Failed to get recent pipeline executions: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_pipeline_execution_stats(
    pipeline_name: Optional[str] = Query(None, description="Get stats for specific pipeline"),
    service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Get pipeline execution statistics"""
    try:
        stats = await service.get_pipeline_execution_stats(pipeline_name=pipeline_name)
        return stats
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to get pipeline execution stats", details=f"Failed to get pipeline execution stats: {str(e)}")


@router.get("/batch/{batch_execution_id}", response_model=List[PipelineExecutionResult])
async def get_pipeline_executions_by_batch(
    batch_execution_id: str,
    service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Get all pipeline executions for a specific batch"""
    try:
        executions = await service.get_pipeline_executions_by_batch(batch_execution_id)
        return executions
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to get pipeline executions for batch", details=f"Failed to get pipeline executions for batch: {str(e)}")


@router.get("/{execution_id}", response_model=PipelineExecutionResult)
async def get_pipeline_execution(
    execution_id: str,
    service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Get a specific pipeline execution by ID"""
    try:
        execution = await service.get_pipeline_execution_by_id(execution_id)
        if not execution:
            raise ApiException(status_code=404, message="Pipeline execution not found")
        return execution
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to get pipeline execution", details=f"Failed to get pipeline execution: {str(e)}")


@router.delete("/{execution_id}")
async def delete_pipeline_execution(
    execution_id: str,
    service: PipelineExecutionService = Depends(get_pipeline_execution_service)
):
    """Delete a pipeline execution by ID"""
    try:
        success = await service.delete_pipeline_execution_by_id(execution_id)
        if not success:
            raise ApiException(status_code=404, message="Pipeline execution not found")
        return {"message": "Pipeline execution deleted successfully"}
    except ApiException:
        raise
    except Exception as e:
        raise ApiException(status_code=500, message="Failed to delete pipeline execution", details=f"Failed to delete pipeline execution: {str(e)}")