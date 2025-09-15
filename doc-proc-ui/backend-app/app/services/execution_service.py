from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from .base import BaseService
from .activity_log_service import ActivityLogService
from ..db.cosmos import CosmosDb
from ..models.execution import (
    BatchExecution, BatchStatus, ActivityType,
    StepOutput, BatchExecutionRequest
)


class ExecutionService(BaseService):
    """Service for managing pipeline execution operations"""

    def __init__(self, db: CosmosDb):
        super().__init__(db, "batch_executions")
        self._activity_log_service = ActivityLogService(db)

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

    async def update_batch_status(
        self,
        batch_id: str,
        status: BatchStatus,
        celery_task_id: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None
    ) -> Optional[BatchExecution]:
        """Update batch execution status"""
        batch = await self.get_batch_execution(batch_id)
        if not batch:
            return None

        # Update fields
        batch.status = status
        if celery_task_id:
            batch.celery_task_id = celery_task_id
        if started_at:
            batch.started_at = started_at
        if completed_at:
            batch.completed_at = completed_at
        if results:
            batch.results = results
        if errors:
            batch.errors = errors

        batch.touch()
        
        updated_batch = await self.update(batch_id, batch.model_dump())
        return BatchExecution(**updated_batch)

    async def get_batch_activities(self, batch_id: str, limit: Optional[int] = None) -> List:
        """Get activities for a batch execution"""
        return await self._activity_log_service.get_batch_activities(batch_id, limit)

    async def list_batch_executions(
        self,
        status: Optional[BatchStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[BatchExecution]:
        """List batch executions with optional filtering"""
        query = "SELECT * FROM c"
        parameters = []
        
        if status:
            query += " WHERE c.status = @status"
            parameters.append({"name": "@status", "value": status.value})
        
        query += " ORDER BY c.created_at DESC"
        
        if limit:
            query += f" OFFSET {offset} LIMIT {limit}"
        
        items = await self.query(query, parameters)
        return [BatchExecution(**item) for item in items]

    async def cancel_batch_execution(self, batch_id: str) -> bool:
        """Cancel a batch execution"""
        batch = await self.get_batch_execution(batch_id)
        if not batch:
            return False

        if batch.status in [BatchStatus.COMPLETED, BatchStatus.CANCELLED, BatchStatus.FAILED]:
            return False  # Cannot cancel already finished batches

        # Update status
        await self.update_batch_status(
            batch_id,
            BatchStatus.CANCELLED,
            completed_at=datetime.now(timezone.utc).isoformat()
        )

        # Log cancellation activity
        await self._activity_log_service.log_activity(
            batch_execution_id=batch_id,
            activity_type=ActivityType.BATCH_CANCELLED,
            status="Cancelled",
            message="Batch execution cancelled by user"
        )

        return True

    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        try:
            # Get overall stats
            total_query = "SELECT COUNT(1) as total FROM c"
            total_result = await self.query(total_query)
            total_executions = total_result[0]["total"] if total_result else 0

            # Get status distribution
            status_query = "SELECT c.status, COUNT(1) as count FROM c GROUP BY c.status"
            status_results = await self.query(status_query)
            
            status_counts = {}
            for result in status_results:
                status_counts[result["status"]] = result["count"]

            return {
                "total_executions": total_executions,
                "status_distribution": status_counts,
                "pending": status_counts.get("pending", 0),
                "running": status_counts.get("running", 0),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
                "cancelled": status_counts.get("cancelled", 0)
            }
        except Exception:
            return {
                "total_executions": 0,
                "status_distribution": {},
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0
            }
    
    
    async def get_batch_execution(self, batch_id: str) -> Optional[BatchExecution]:
        """Get batch execution by ID"""
        batch_data = await self.get_by_id(batch_id)
        return BatchExecution(**batch_data) if batch_data else None

    async def update_batch_status(
        self,
        batch_id: str,
        status: BatchStatus,
        celery_task_id: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None
    ) -> Optional[BatchExecution]:
        """Update batch execution status"""
        batch = await self.get_batch_execution(batch_id)
        if not batch:
            return None

        # Update fields
        batch.status = status
        if celery_task_id:
            batch.celery_task_id = celery_task_id
        if started_at:
            batch.started_at = started_at
        if completed_at:
            batch.completed_at = completed_at
        if results:
            batch.results = results
        if errors:
            batch.errors = errors

        batch.touch()
        
        updated_batch = await self.update(batch_id, batch.model_dump())
        return BatchExecution(**updated_batch)

    async def get_batch_activities(self, batch_id: str, limit: Optional[int] = None) -> List:
        """Get activities for a batch execution"""
        return await self._activity_log_service.get_batch_activities(batch_id, limit)

    async def list_batch_executions(
        self,
        status: Optional[BatchStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[BatchExecution]:
        """List batch executions with optional filtering"""
        query = "SELECT * FROM c"
        parameters = []
        
        if status:
            query += " WHERE c.status = @status"
            parameters.append({"name": "@status", "value": status.value})
        
        query += " ORDER BY c.created_at DESC"
        
        if limit:
            query += f" OFFSET {offset} LIMIT {limit}"
        
        items = await self.query(query, parameters)
        return [BatchExecution(**item) for item in items]

    async def cancel_batch_execution(self, batch_id: str) -> bool:
        """Cancel a batch execution"""
        batch = await self.get_batch_execution(batch_id)
        if not batch:
            return False

        if batch.status in [BatchStatus.COMPLETED, BatchStatus.CANCELLED, BatchStatus.FAILED]:
            return False  # Cannot cancel already finished batches

        # Update status
        await self.update_batch_status(
            batch_id,
            BatchStatus.CANCELLED,
            completed_at=datetime.now(timezone.utc).isoformat()
        )

        # Log cancellation activity
        await self._activity_log_service.log_activity(
            batch_execution_id=batch_id,
            activity_type=ActivityType.BATCH_CANCELLED,
            status="Cancelled",
            message="Batch execution cancelled by user"
        )

        return True

    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        try:
            # Get overall stats
            total_query = "SELECT COUNT(1) as total FROM c"
            total_result = await self.query(total_query)
            total_executions = total_result[0]["total"] if total_result else 0

            # Get status distribution
            status_query = "SELECT c.status, COUNT(1) as count FROM c GROUP BY c.status"
            status_results = await self.query(status_query)
            
            status_counts = {}
            for result in status_results:
                status_counts[result["status"]] = result["count"]

            return {
                "total_executions": total_executions,
                "status_distribution": status_counts,
                "pending": status_counts.get("pending", 0),
                "running": status_counts.get("running", 0),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
                "cancelled": status_counts.get("cancelled", 0)
            }
        except Exception:
            return {
                "total_executions": 0,
                "status_distribution": {},
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0
            }
    
    
    async def get_batch_execution(self, batch_id: str) -> Optional[BatchExecution]:
        """Get batch execution by ID"""
        batch_data = await self.get_by_id(batch_id)
        return BatchExecution(**batch_data) if batch_data else None

    async def update_batch_status(
        self,
        batch_id: str,
        status: BatchStatus,
        celery_task_id: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None
    ) -> Optional[BatchExecution]:
        """Update batch execution status"""
        batch = await self.get_batch_execution(batch_id)
        if not batch:
            return None

        # Update fields
        batch.status = status
        if celery_task_id:
            batch.celery_task_id = celery_task_id
        if started_at:
            batch.started_at = started_at
        if completed_at:
            batch.completed_at = completed_at
        if results:
            batch.results = results
        if errors:
            batch.errors = errors

        batch.touch()
        
        updated_batch = await self.update(batch_id, batch.model_dump())
        return BatchExecution(**updated_batch)

    async def get_batch_activities(self, batch_id: str, limit: Optional[int] = None) -> List:
        """Get activities for a batch execution"""
        return await self._activity_log_service.get_batch_activities(batch_id, limit)

    async def list_batch_executions(
        self,
        status: Optional[BatchStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[BatchExecution]:
        """List batch executions with optional filtering"""
        query = "SELECT * FROM c"
        parameters = []
        
        if status:
            query += " WHERE c.status = @status"
            parameters.append({"name": "@status", "value": status.value})
        
        query += " ORDER BY c.created_at DESC"
        
        if limit:
            query += f" OFFSET {offset} LIMIT {limit}"
        
        items = await self.query(query, parameters)
        return [BatchExecution(**item) for item in items]

    async def cancel_batch_execution(self, batch_id: str) -> bool:
        """Cancel a batch execution"""
        batch = await self.get_batch_execution(batch_id)
        if not batch:
            return False

        if batch.status in [BatchStatus.COMPLETED, BatchStatus.CANCELLED, BatchStatus.FAILED]:
            return False  # Cannot cancel already finished batches

        # Update status
        await self.update_batch_status(
            batch_id,
            BatchStatus.CANCELLED,
            completed_at=datetime.now(timezone.utc).isoformat()
        )

        # Log cancellation activity
        await self._activity_log_service.log_activity(
            batch_execution_id=batch_id,
            activity_type=ActivityType.BATCH_CANCELLED,
            status="Cancelled",
            message="Batch execution cancelled by user"
        )

        return True

    async def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        try:
            # Get overall stats
            total_query = "SELECT COUNT(1) as total FROM c"
            total_result = await self.query(total_query)
            total_executions = total_result[0]["total"] if total_result else 0

            # Get status distribution
            status_query = "SELECT c.status, COUNT(1) as count FROM c GROUP BY c.status"
            status_results = await self.query(status_query)
            
            status_counts = {}
            for result in status_results:
                status_counts[result["status"]] = result["count"]

            return {
                "total_executions": total_executions,
                "status_distribution": status_counts,
                "pending": status_counts.get("pending", 0),
                "running": status_counts.get("running", 0),
                "completed": status_counts.get("completed", 0),
                "failed": status_counts.get("failed", 0),
                "cancelled": status_counts.get("cancelled", 0)
            }
        except Exception:
            return {
                "total_executions": 0,
                "status_distribution": {},
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0
            }
            description=f"Batch execution of {len(request.documents)} documents",
            pipeline_instance_id=request.pipeline_instance_id,
            pipeline_name=pipeline_instance["name"],
            documents=request.documents,
            total_documents=len(request.documents),
            priority=request.priority,
            metadata=request.metadata
        
        
        # Save to database
        saved_batch = await self.create(batch.model_dump())
        
        # Log creation activity
        await self.log_activity(
            batch_execution_id=batch_id,
            activity_type=ActivityType.BATCH_CREATED,
            status="created",
            message=f"Batch execution created with {len(request.documents)} documents",
            details={
                "pipeline_id": request.pipeline_instance_id,
                "pipeline_name": pipeline_instance["name"],
                "document_count": len(request.documents),
                "priority": request.priority
            }
        )
        
        return BatchExecution(**saved_batch)
    
    async def get_batch_execution(self, batch_id: str) -> Optional[BatchExecution]:
        """Get batch execution by ID"""
        batch_data = await self.get_by_id(batch_id)
        return BatchExecution(**batch_data) if batch_data else None
    
    async def update_batch_status(self, batch_id: str, status: BatchStatus, **kwargs) -> bool:
        """Update batch execution status"""
        batch_data = await self.get_by_id(batch_id)
        if not batch_data:
            return False
        
        batch_data["status"] = status.value
        batch_data["updated_at"] = datetime.utcnow()
        
        # Update specific fields if provided
        for key, value in kwargs.items():
            if key in ["celery_task_id", "started_at", "completed_at", "estimated_completion",
                      "completed_documents", "failed_documents", "results", "errors"]:
                batch_data[key] = value
        
        await self.update(batch_data)
        return True
    
    async def update_batch_progress(self, batch_id: str, completed_documents: int, failed_documents: int) -> bool:
        """Update batch execution progress"""
        batch_data = await self.get_by_id(batch_id)
        if not batch_data:
            return False
        
        batch_data["completed_documents"] = completed_documents
        batch_data["failed_documents"] = failed_documents
        batch_data["updated_at"] = datetime.utcnow()
        
        await self.update(batch_data)
        return True
    
    async def log_activity(self, batch_execution_id: str, activity_type: ActivityType, 
                          status: str, message: str, **kwargs) -> ActivityLog:
        """Log an activity"""
        
        activity_id = f"activity_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        activity = ActivityLog(
            id=activity_id,
            name=f"{activity_type.value}_{activity_id}",
            batch_execution_id=batch_execution_id,
            activity_type=activity_type,
            status=status,
            message=message,
            step_name=kwargs.get("step_name"),
            document_id=kwargs.get("document_id"),
            error_message=kwargs.get("error_message"),
            duration_ms=kwargs.get("duration_ms"),
            details=kwargs.get("details", {}),
            metadata=kwargs.get("metadata", {})
        )
        
        # Store in activities container
        activities_service = BaseService(self.db, "activities")
        await activities_service.create(activity.model_dump())
        
        return activity
    
    async def get_batch_activities(self, batch_id: str, limit: int = 50) -> List[ActivityLog]:
        """Get activities for a batch execution"""
        activities_service = BaseService(self.db, "activities")
        
        query = "SELECT * FROM c WHERE c.batch_execution_id = @batch_id ORDER BY c.timestamp DESC"
        parameters = [{"name": "@batch_id", "value": batch_id}]
        
        activities_data = await activities_service.list_all(query, parameters)
        
        # Limit results
        if limit > 0:
            activities_data = activities_data[:limit]
        
        return [ActivityLog(**activity) for activity in activities_data]
    
    async def store_step_output(self, step_output: StepOutput) -> bool:
        """Store step output"""
        step_outputs_service = BaseService(self.db, "step_outputs")
        
        output_id = f"output_{step_output.step_name}_{step_output.document_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        output_data = step_output.model_dump()
        output_data["id"] = output_id
        
        await step_outputs_service.create(output_data)
        return True
    
    async def get_step_outputs(self, batch_id: str, step_name: Optional[str] = None, 
                              document_id: Optional[str] = None) -> List[StepOutput]:
        """Get step outputs for a batch"""
        step_outputs_service = BaseService(self.db, "step_outputs")
        
        # Build query based on filters
        where_conditions = []
        parameters = []
        
        # Note: We'll need to add batch_id to StepOutput model or use a different approach
        # For now, we'll query by step_name and document_id
        
        if step_name:
            where_conditions.append("c.step_name = @step_name")
            parameters.append({"name": "@step_name", "value": step_name})
        
        if document_id:
            where_conditions.append("c.document_id = @document_id")
            parameters.append({"name": "@document_id", "value": document_id})
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        query = f"SELECT * FROM c WHERE {where_clause} ORDER BY c.created_at DESC"
        
        outputs_data = await step_outputs_service.list_all(query, parameters)
        return [StepOutput(**output) for output in outputs_data]
    
    async def load_pipeline(self, pipeline_instance_id: str) -> Pipeline:
        """Load and cache pipeline instance"""
        if pipeline_instance_id in self._pipeline_cache:
            return self._pipeline_cache[pipeline_instance_id]
        
        # Get pipeline instance
        pipeline_service = self._get_pipeline_service()
        pipeline_instance = await pipeline_service.get_by_id(pipeline_instance_id)
        if not pipeline_instance:
            raise ValueError(f"Pipeline instance {pipeline_instance_id} not found")
        
        # Load pipeline configuration from YAML
        config = await self._get_config()
        
        # Find pipeline config by name
        pipeline_config_dict = None
        for pipeline_cfg in config.get("pipelines", []):
            if pipeline_cfg.get("name") == pipeline_instance.get("config_name"):
                pipeline_config_dict = pipeline_cfg
                break
        
        if not pipeline_config_dict:
            raise ValueError(f"Pipeline configuration not found for {pipeline_instance.get('config_name')}")
        
        # Load step and service catalogs
        step_catalog = await self._load_step_catalog()
        service_catalog = await self._load_service_catalog()
        
        # Create pipeline config
        pipeline_config_dict["service_instances"] = config.get("service_instances", [])
        pipeline_config = PipelineConfig(**pipeline_config_dict)
        
        # Create pipeline instance
        pipeline = await Pipeline.create(
            pipeline_config=pipeline_config,
            step_catalog_config=step_catalog,
            service_catalog_config=service_catalog
        )
        
        # Cache the pipeline
        self._pipeline_cache[pipeline_instance_id] = pipeline
        
        return pipeline
    
    async def _get_config(self) -> Dict[str, Any]:
        """Load pipeline configuration from YAML file"""
        if self._config_cache is None:
            config_path = os.path.join(os.path.dirname(__file__), "../../../../doc-proc-lib/pipeline_config.yaml")
            try:
                with open(config_path, 'r') as file:
                    self._config_cache = yaml.safe_load(file)
            except FileNotFoundError:
                self._config_cache = {"pipelines": [], "service_instances": []}
        return self._config_cache
    
    async def _load_step_catalog(self) -> List[StepConfig]:
        """Load step catalog from YAML"""
        catalog_path = os.path.join(os.path.dirname(__file__), "../../../../doc-proc-lib/step_catalog.yaml")
        try:
            with open(catalog_path, 'r') as file:
                catalog_data = yaml.safe_load(file)
            return [StepConfig(**step) for step in catalog_data.get("step_catalog", [])]
        except FileNotFoundError:
            return []
    
    async def _load_service_catalog(self) -> List[ServiceConfig]:
        """Load service catalog from YAML"""
        catalog_path = os.path.join(os.path.dirname(__file__), "../../../../doc-proc-lib/service_catalog.yaml")
        try:
            with open(catalog_path, 'r') as file:
                catalog_data = yaml.safe_load(file)
            return [ServiceConfig(**service) for service in catalog_data.get("services_catalog", [])]
        except FileNotFoundError:
            return []
    
    def _get_pipeline_service(self):
        """Get pipeline service instance"""
        from .pipeline_service import PipelineService
        return PipelineService(self.db)
    
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
