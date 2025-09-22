from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from .base import BaseService
from ..db.cosmos import CosmosDb
from ..models.execution import PipelineExecutionResult, DocumentResult


class PipelineExecutionService(BaseService):
    """Service for managing pipeline execution results operations"""

    def __init__(self, db: CosmosDb, container_name: str = "pipeline_executions"):
        super().__init__(db, container_name)

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate pipeline execution result item"""
        required_fields = ["id", "batch_execution_id", "pipeline_name", "result"]
        return all(field in item for field in required_fields)
    
    async def get_pipeline_execution_by_id(self, execution_id: str) -> Optional[PipelineExecutionResult]:
        """Get pipeline execution result by ID"""
        execution_data = await self.get_by_id(execution_id)
        return PipelineExecutionResult(**execution_data) if execution_data else None
    
    async def list_pipeline_executions(
        self, 
        batch_execution_id: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[PipelineExecutionResult]:
        """List pipeline executions with optional filters"""
        where_conditions = []
        parameters = []
        
        if batch_execution_id:
            where_conditions.append("c.batch_execution_id = @batch_execution_id")
            parameters.append({"name": "@batch_execution_id", "value": batch_execution_id})
        
        if pipeline_name:
            where_conditions.append("c.pipeline_name = @pipeline_name")
            parameters.append({"name": "@pipeline_name", "value": pipeline_name})
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        query = f"""
        SELECT * FROM c 
        WHERE {where_clause} 
        ORDER BY c.created_at DESC 
        OFFSET {offset} LIMIT {limit}
        """
        
        execution_data = await self.list_all(query, parameters)
        return [PipelineExecutionResult(**execution) for execution in execution_data]
    
    async def get_pipeline_executions_by_batch(self, batch_execution_id: str) -> List[PipelineExecutionResult]:
        """Get all pipeline executions for a specific batch"""
        query = "SELECT * FROM c WHERE c.batch_execution_id = @batch_execution_id ORDER BY c.created_at DESC"
        parameters = [{"name": "@batch_execution_id", "value": batch_execution_id}]
        
        execution_data = await self.list_all(query, parameters)
        return [PipelineExecutionResult(**execution) for execution in execution_data]
    
    async def get_recent_pipeline_executions(self, pipeline_name: Optional[str] = None, limit: int = 20, time_range: Optional[str] = "last_24h") -> List[PipelineExecutionResult]:
        """Get recent pipeline executions within specified time range"""
        from datetime import timedelta
        
        # Calculate the cutoff datetime based on time_range
        now = datetime.now(timezone.utc)
        time_deltas = {
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        if time_range not in time_deltas:
            time_range = "24h"  # Default fallback

        cutoff_time = now - time_deltas[time_range]
        cutoff_timestamp = cutoff_time.isoformat()
        
        if pipeline_name:
            where_clause = "c.pipeline_name = @pipeline_name AND c.started_at >= @cutoff_time"
            parameters = [
                {"name": "@pipeline_name", "value": pipeline_name},
                {"name": "@cutoff_time", "value": cutoff_timestamp}
            ]
        else:
            where_clause = "c.started_at >= @cutoff_time"
            parameters = [{"name": "@cutoff_time", "value": cutoff_timestamp}]
        
        query = f"""
        SELECT * FROM c 
        WHERE {where_clause}
        ORDER BY c.started_at DESC
        OFFSET 0 LIMIT {limit}
        """
        
        execution_data = await self.list_all(query, parameters)
        return [PipelineExecutionResult(**execution) for execution in execution_data]
    
    async def get_pipeline_execution_stats(self, pipeline_name: Optional[str] = None) -> Dict[str, Any]:
        """Get pipeline execution statistics"""
        where_clause = ""
        parameters = []
        
        if pipeline_name:
            where_clause = "WHERE c.pipeline_name = @pipeline_name"
            parameters = [{"name": "@pipeline_name", "value": pipeline_name}]
        
        # Get total counts and success rate
        # query = f"""
        # select count(c.result) as total_executions,
        #     sum(c.result = 'Succeeded' ? 1:0) as successful_executions,
        #     sum(c.result = 'Failed' ? 1:0) as failed_executions,
        #     sum(c.result = 'PartialSucceeded' ? 1:0) as partial_succeessful_executions,
        #     AVG(c.elapsed_time_secs) as avg_execution_time_secs
        # from c
        # {where_clause}
        # """
        
        query = f"""
        select *
        from c
        {where_clause}
        """
        
        stats_data = await self.list_all(query, parameters)
        
        if not stats_data or not stats_data[0]:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "partial_succeessful_executions": 0,
                "success_rate": 0.0,
                "avg_execution_time_secs": 0
            }
        
        stats = stats_data[0]
        total = stats.get("total_executions", 0)
        successful = stats.get("successful_executions", 0)
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": stats.get("failed_executions", 0),
            "success_rate": (successful / total * 100) if total > 0 else 0.0,
            "avg_execution_time_secs": stats.get("avg_execution_time_secs", 0) or 0
        }
    
    
    async def delete_pipeline_execution_by_id(self, execution_id: str) -> bool:
        """Delete a pipeline execution result by ID"""
        return await self.delete(execution_id)