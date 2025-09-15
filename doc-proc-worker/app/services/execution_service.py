import asyncio
import os
import sys
import traceback
import yaml
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.services.cosmos_db_service import CosmosDBService
from app.services.pipeline_service import PipelineService
from app.services.activity_log_service import ActivityLogService

from app.db.cosmos import CosmosDb
from app.models.execution import (
    BatchExecution, BatchStatus, ActivityType,
    StepOutput, BatchExecutionRequest
)
from doc.proc.pipeline.pipeline_base import Pipeline, PipelineExecutionResult
from doc.proc.step.step_base import StepInputOutput


class ExecutionService(CosmosDBService):
    """Service for managing pipeline execution operations"""

    def __init__(self, db: CosmosDb, pipeline_service: PipelineService, activity_log_service: ActivityLogService):
        super().__init__(db, "batch_executions")
        self._pipeline_service = pipeline_service
        self._activity_log_service = activity_log_service

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate batch execution item"""
        required_fields = ["id", "name", "pipeline_name", "documents"]
        return all(field in item for field in required_fields)
    
    async def create_batch_execution(self, request: BatchExecutionRequest) -> BatchExecution:
        """Create a new batch execution"""
        
        # Generate batch ID
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{len(request.documents)}_docs"
        
        # Create batch execution
        batch = BatchExecution(
            id=batch_id,
            name=request.batch_name or f"Batch execution for {request.pipeline_name}",
            pipeline_name=request.pipeline_name,
            documents=request.documents,
            total_documents=len(request.documents),
            priority=request.priority,
            metadata=request.metadata
        )
        
        # Save to database
        saved_batch = await self.create(batch.model_dump())
        
        # Log creation activity
        await self._activity_log_service.log_activity(
            batch_execution_id=batch_id,
            activity_type=ActivityType.BATCH_CREATED,
            status="Created",
            message=f"Batch execution created with {len(request.documents)} documents",
            details={
                "pipeline_name": request.pipeline_name,
                "document_count": len(request.documents),
                "priority": request.priority
            }
        )
        
        return BatchExecution(**saved_batch)
    
    
    async def get_batch_execution(self, batch_id: str) -> Optional[BatchExecution]:
        """Get batch execution by ID"""
        batch_data = await self.get_by_id(batch_id)
        return BatchExecution(**batch_data) if batch_data else None


    async def execute_batch(self, batch_id: str, task_id: str) -> bool:
        """Execute a batch"""
        # Get batch execution
        batch = await self.get_batch_execution(batch_id=batch_id)
        if not batch:
            raise ValueError(f"Batch execution {batch_id} not found")
        
        try:
            # Update batch status to running
            await self.update_batch_status(
                batch_id,
                BatchStatus.RUNNING,
                celery_task_id=task_id,
                started_at=datetime.now(timezone.utc).isoformat()
            )
        
            # Log batch start activity
            await self._activity_log_service.log_activity(
                batch_execution_id=batch_id,
                activity_type=ActivityType.BATCH_STARTED,
                status="Started",
                message=f"Batch execution started with {batch.total_documents} documents",
                details={"task_id": task_id, "pipeline": batch.pipeline_name}
            )
        
            # Load pipeline
            pipeline = await self._pipeline_service.load_pipeline(batch.pipeline_name)
            if not pipeline:
                raise RuntimeError(f"Pipeline {batch.pipeline_name} not found")

          
            # Wait for all tasks to complete and collect results
            pipeline_execution_result = await self._process_batch(batch, pipeline, batch_id)

            # Store the result in the database
            await self._store_pipeline_execution_result(batch_id, pipeline_execution_result)

            successful_documents = pipeline_execution_result.summary_stats.get("successful_documents", 0)
            failed_documents = pipeline_execution_result.summary_stats.get("failed_documents", 0)

            # Complete the batch
            final_status = BatchStatus.FAILED if pipeline_execution_result.result == "Failed" else BatchStatus.COMPLETED
            await self.update_batch_status(
                batch_id,
                final_status,
                completed_at=datetime.now(timezone.utc).isoformat(),
                completed_documents=successful_documents,
                failed_documents=failed_documents
            )
            
            # Log batch completion
            await self._activity_log_service.log_activity(
                batch_execution_id=batch_id,
                activity_type=ActivityType.BATCH_COMPLETED,
                status="completed",
                message=f"Batch execution completed. Processed: {successful_documents}, Failed: {failed_documents}",
                details={
                    "total_documents": batch.total_documents,
                    "completed_documents": successful_documents,
                    "failed_documents": failed_documents
                }
            )
            
            return True

        except Exception as e:
            await self.update_batch_status(
                batch_id=batch_id,
                status=BatchStatus.FAILED,
                completed_at=datetime.now(timezone.utc).isoformat(),
                errors=[str(e), traceback.format_exc()]
            )

            await self._activity_log_service.log_activity(
                batch_execution_id=batch_id,
                activity_type=ActivityType.BATCH_FAILED,
                status="Failed",
                message="Batch execution failed",
                error_message=str(e)
            )

            return False

    async def _process_batch(self, batch: BatchExecution, pipeline: Pipeline, batch_id: str) -> PipelineExecutionResult:
        """Process the batch and return results"""
        
        # Create input data for the batch
        input_data = StepInputOutput(
                            summary_data={
                                "batch_id": batch_id,
                                "pipeline": pipeline.name
                            },
                            data={
                                "documents": batch.documents
                            }
                        )
            
        # Execute pipeline for this batch
        result = await pipeline.run(input_data)
        with open(f"./tmp/{batch_id}_result.json", 'w') as f:
            f.write(result.model_dump_json())
        return result

    async def update_batch_status(self, batch_id: str, status: BatchStatus, **kwargs) -> bool:
        """Update batch execution status"""
        batch_data = await self.get_by_id(batch_id)
        if not batch_data:
            return False
        
        batch_data["status"] = status.value
        batch_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update specific fields if provided
        for key, value in kwargs.items():
            if key in ["celery_task_id", "submitted_at", "started_at", "completed_at",
                      "completed_documents", "failed_documents", "results", "errors", "metadata"]:
                batch_data[key] = value
        
        await self.update(batch_data)
        return True
    
    async def _store_pipeline_execution_result(self, batch_id:str, pipeline_execution_result: PipelineExecutionResult) -> bool:
        """Store pipeline execution result"""
        from app.dependencies import get_cosmos_db_service
        pipeline_results_service = get_cosmos_db_service("pipeline_executions")

        result_id = f"result_{pipeline_execution_result.pipeline_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"

        output_data = pipeline_execution_result.model_dump()
        
        # clean up the data field for each document
        for doc_result in output_data.get("document_results", []):
            # remove all fields except id and file_path
            doc_result_data = doc_result.get("data", {})
            for k in list(doc_result_data.keys()):
                if k not in ["id", "file_path"]:
                    doc_result_data.pop(k)

        output_data["id"] = result_id
        output_data["batch_execution_id"] = batch_id

        await pipeline_results_service.create(output_data)
        return True
    
    async def list_batch_executions(self, status: Optional[BatchStatus] = None, 
                                   pipeline_id: Optional[str] = None) -> List[BatchExecution]:
        """List batch executions with optional filters"""
        where_conditions = []
        parameters = []
        
        if status:
            where_conditions.append("c.status = @status")
            parameters.append({"name": "@status", "value": status.value})
        
        if pipeline_id:
            where_conditions.append("c.pipeline_instance_id = @pipeline_id")
            parameters.append({"name": "@pipeline_id", "value": pipeline_id})
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        query = f"SELECT * FROM c WHERE {where_clause} ORDER BY c.created_at DESC"
        
        batch_data = await self.list_all(query, parameters)
        return [BatchExecution(**batch) for batch in batch_data]
