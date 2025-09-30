import asyncio
import logging
import uuid
import os
import sys
import traceback
import yaml
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.managers.pipeline_manager import PipelineManager

from app.proxy.cosmos import CosmosDb
from app.models.execution import (
    BatchExecution, BatchStatus, ActivityType,
    StepOutput, BatchExecutionRequest
)
from doc.proc.pipeline.pipeline_base import Pipeline, PipelineExecutionResult
from doc.proc.step.step_base import StepInputOutput

logger = logging.getLogger("doc-proc-worker.app.execution_manager")

class ExecutionManager():
    """Manages pipeline execution operations"""

    def __init__(self, 
                 db: CosmosDb, 
                 pipeline_manager: PipelineManager, 
                 batch_executions_container_name:str = "batch_executions",
                 pipeline_executions_container_name:str = "pipeline_executions"
                ):
        
        self._db = db
        self._batch_executions_container_name = batch_executions_container_name
        self._pipeline_executions_container_name = pipeline_executions_container_name
        self._pipeline_manager = pipeline_manager

    
    async def execute_batch(self, batch_execution_request: BatchExecutionRequest) -> bool:
        """Execute a batch"""

        if not batch_execution_request or not batch_execution_request.documents:
            raise ValueError("Invalid batch execution request or no documents to process")
        
        batch_id = batch_execution_request.source_batch_id
        if not batch_id or batch_id.strip() == "":
            raise ValueError("Batch execution request must have a valid source_batch_id")
        
        try:
            logger.debug(f"Starting execution for batch {batch_id} with {len(batch_execution_request.documents)} documents")
            
            # Create batch execution
            batch = await self._create_batch_execution(batch_id, batch_execution_request)
        

            logger.debug(f"Batch {batch.id} created with status {batch.status}.")

            # Load pipeline
            logger.debug(f"Loading pipeline {batch.pipeline_name} for batch {batch.id}")
            
            pipeline = await self._pipeline_manager.load_pipeline(batch.pipeline_name)
            if not pipeline:
                raise RuntimeError(f"Pipeline {batch.pipeline_name} not found or could not be loaded.")

          
            # Wait for all tasks to complete and collect results
            pipeline_execution_result = await self._process_batch(batch, pipeline)

            # Store the result in the database
            _stored_pipeline_execution = await self._store_pipeline_execution_result(batch_id=batch.id, 
                                                                                     vault_id=batch.vault_id,
                                                                                     pipeline_execution_result=pipeline_execution_result)


            # Complete the batch
            final_status = BatchStatus.COMPLETED
            await self._update_completion_batch_status(
                batch_id=batch.id,
                status=final_status,
                stored_pipeline_execution_id=_stored_pipeline_execution.get("id", ""),
                pipeline_execution_result=pipeline_execution_result,
            )
            
            return True

        except Exception as e:
            await self._update_batch_status(
                batch_id=batch_id,
                status=BatchStatus.FAILED,
                completed_at=datetime.now(timezone.utc).isoformat(),
                errors=[str(e), traceback.format_exc()]
            )

            return False

    async def _process_batch(self, batch: BatchExecution, pipeline: Pipeline) -> PipelineExecutionResult:
        """Process the batch and return results"""
        
        # Create input data for the batch
        input_data = StepInputOutput(
                            summary_data={
                                "batch_id": batch.id,
                                "pipeline": pipeline.name
                            },
                            data={
                                "documents": batch.documents
                            }
                        )
            
        # Execute pipeline for this batch
        result = await pipeline.run(input_data)
        
        with open(f"./tmp/{batch.id}_result.json", 'w') as f:
            f.write(result.model_dump_json())
        
        return result


    async def _store_pipeline_execution_result(self, batch_id:str, vault_id: str, pipeline_execution_result: PipelineExecutionResult) -> Dict[str, Any]:
        """Store pipeline execution result"""
        
        result_id = f"exec_{pipeline_execution_result.pipeline_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"

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
        output_data["vault_id"] = vault_id

        return self._db.upsert(container=self._pipeline_executions_container_name, item=output_data)

    
    async def _create_batch_execution(self, batch_id: str, request: BatchExecutionRequest) -> BatchExecution:
        """Create a new batch execution"""
                
        # Create batch execution
        batch = BatchExecution(
            id=batch_id,
            status=BatchStatus.RUNNING,
            pipeline_name=request.pipeline_name,
            vault_id=request.vault_id,
            documents=request.documents,
            total_documents=len(request.documents),
            source_batch_id=request.source_batch_id,
            submitted_at=datetime.now(timezone.utc).isoformat(),
            started_at=datetime.now(timezone.utc).isoformat(),
            metadata=request.metadata
        )
        
        # Save to database
        saved_batch = self._db.upsert(self._batch_executions_container_name, batch.model_dump())
        
        return BatchExecution(**saved_batch)
    

    async def _update_batch_status(self, batch_id: str, status: BatchStatus, **kwargs) -> bool:
        """Update batch execution status"""
        batch_data = self._db.get(container=self._batch_executions_container_name, id=batch_id)
        if not batch_data:
            return False
        
        batch_data["status"] = status.value
        batch_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update specific fields if provided
        for key, value in kwargs.items():
            if key in ["submitted_at", "started_at", "completed_at",
                      "completed_documents", "failed_documents", "results", "errors", "metadata"]:
                batch_data[key] = value
        
        self._db.upsert(container=self._batch_executions_container_name, item=batch_data)
        return True
    
    
    async def _update_completion_batch_status(self, batch_id: str, status: BatchStatus, 
                                                    stored_pipeline_execution_id: str,
                                                    pipeline_execution_result: PipelineExecutionResult,
                                                    **kwargs) -> bool:
        """Update batch execution status on completion"""
        batch_data = self._db.get(container=self._batch_executions_container_name, id=batch_id)
        if not batch_data:
            return False
        
        batch_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        batch_data["status"] = status.value
        batch_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update specific fields if provided
        for key, value in kwargs.items():
            if key in ["submitted_at", "started_at", "completed_at", "metadata"]:
                batch_data[key] = value
        
        
        # Update statistics from pipeline execution result
        successful_documents = pipeline_execution_result.summary_stats.get("successful_documents", 0)
        failed_documents = pipeline_execution_result.summary_stats.get("failed_documents", 0)
        
        # Update statistics from pipeline execution result
        batch_data["pipeline_execution_id"] = stored_pipeline_execution_id
        batch_data["successful_documents"] = successful_documents
        batch_data["failed_documents"] = failed_documents
        
        # update status of individual documents if available
        _pipeline_execution_result = pipeline_execution_result.model_dump()
        if "document_results" in _pipeline_execution_result:
            document_results = _pipeline_execution_result.get("document_results", [])
            for doc_result in document_results:
                if "document_id" in doc_result and "result" in doc_result:
                    doc_id = doc_result["document_id"]
                    doc_status = doc_result["result"]
                    doc_reason = doc_result.get("reason", "")
                    doc_elapsed_time = doc_result.get("elapsed_time_secs", 0.0)
                    
                    if doc_status == 'Failed' and doc_reason in [None, ""]:
                        # get the last step result with failure reason
                        step_results = doc_result.get("step_results", [])
                        if step_results:
                            # find the step with failure
                            _step = next((s for s in step_results if s.get("result") == "Failed"), None)
                            doc_reason = _step.get("reason", "Unknown error") if _step else "Unknown error"

                    # Find the document in the batch and update its status
                    for batch_doc in batch_data.get("documents", []):
                        if batch_doc.get("id", "") == doc_id:
                            batch_doc["status"] = doc_status
                            batch_doc["reason"] = doc_reason
                            batch_doc["elapsed_time_secs"] = doc_elapsed_time
                            break
        
        self._db.upsert(container=self._batch_executions_container_name, item=batch_data)
        return True