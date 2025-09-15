from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from ..db.cosmos import CosmosDb
from ..models.execution import ActivityLog, ActivityType
from .base import BaseService


class ActivityLogService(BaseService):
    """Service for managing activity logs"""

    def __init__(self, db: CosmosDb):
        super().__init__(db, "activity_logs")

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate activity log item"""
        required_fields = ["id", "batch_execution_id", "activity_type", "status"]
        return all(field in item for field in required_fields)

    async def log_activity(
        self,
        batch_execution_id: str,
        activity_type: ActivityType,
        status: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> ActivityLog:
        """Log an activity"""
        
        activity_id = f"{batch_execution_id}_{activity_type.value}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        
        activity = ActivityLog(
            id=activity_id,
            name=f"Activity: {activity_type.value}",
            batch_execution_id=batch_execution_id,
            activity_type=activity_type,
            status=status,
            message=message,
            details=details or {},
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        saved_activity = await self.create(activity.model_dump())
        return ActivityLog(**saved_activity)

    async def get_batch_activities(
        self, 
        batch_execution_id: str, 
        limit: Optional[int] = None
    ) -> List[ActivityLog]:
        """Get activities for a batch execution"""
        query = "SELECT * FROM c WHERE c.batch_execution_id = @batch_id ORDER BY c.timestamp DESC"
        parameters = [{"name": "@batch_id", "value": batch_execution_id}]
        
        if limit:
            query += f" OFFSET 0 LIMIT {limit}"
        
        items = await self.query(query, parameters)
        return [ActivityLog(**item) for item in items]

    async def get_recent_activities(self, limit: int = 50) -> List[ActivityLog]:
        """Get recent activities across all batches"""
        query = "SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
        parameters = [{"name": "@limit", "value": limit}]
        
        items = await self.query(query, parameters)
        return [ActivityLog(**item) for item in items]
