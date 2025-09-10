from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import yaml
import os

from app.models.execution import (
    ActivityLog, ActivityType
)
from app.services.cosmos_db_service import CosmosDBService
from app.db.cosmos import CosmosDb


class ActivityLogService(CosmosDBService):
    """Service for managing activity logs"""

    def __init__(self, db: CosmosDb):
        super().__init__(db, "activity_logs")
        self._config_cache = None
    
    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate activity log item"""
        required_fields = ["id", "name", "timestamp", "status", "message"]
        return all(field in item for field in required_fields)
    
    async def log_activity(self, batch_execution_id: str, activity_type: ActivityType, 
                          status: str, message: str, **kwargs) -> ActivityLog:
        """Log an activity"""

        activity_id = f"activity_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"

        activity = ActivityLog(
            id=activity_id,
            name=f"{activity_type.value}_{activity_id}",
            batch_execution_id=batch_execution_id,
            activity_type=activity_type,
            status=status,
            message=message,
            details=kwargs.get("details", {}),
            error_message=kwargs.get("error_message"),
            duration_ms=kwargs.get("duration_ms"),
            metadata=kwargs.get("metadata", {})
        )
        
        # Store in activities container
        await self.create(activity.model_dump())
        
        return activity


    async def get_batch_activities(self, batch_id: str, limit: int = 50) -> List[ActivityLog]:
        """Get activities for a batch execution"""

        query = "SELECT * FROM c WHERE c.batch_execution_id = @batch_id ORDER BY c.timestamp DESC"
        parameters = [{"name": "@batch_id", "value": batch_id}]
        
        activities_data = await self.list_all(query, parameters)
        
        # Limit results
        if limit > 0:
            activities_data = activities_data[:limit]
        
        return [ActivityLog(**activity) for activity in activities_data]