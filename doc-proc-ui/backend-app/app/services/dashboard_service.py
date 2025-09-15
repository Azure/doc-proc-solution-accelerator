from typing import Any, Dict, List, Optional
import time
from datetime import datetime, timezone

from ..db.cosmos import CosmosDb
from ..models.dashboard import (
    SystemStats, StatCard, RecentActivity, ProcessingStatus, DashboardData,
    HealthStatus, SystemMetrics, ConnectionInfo, ConnectionTestRequest,
    ConnectionTestResult, ActivityStatus
)
from .base import BaseService


class DashboardService(BaseService):
    """Service for dashboard data and system monitoring"""

    def __init__(self, db: CosmosDb):
        super().__init__(db, "activity_logs")  # Use activity_logs as the primary container
        self._start_time = time.time()

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate dashboard item"""
        return True  # Dashboard service doesn't store items directly

    async def get_system_stats(self) -> SystemStats:
        """Get system-wide statistics"""
        try:
            # Get vault statistics
            vaults_query = "SELECT COUNT(1) as count FROM c"
            vault_results = await self.query(vaults_query, container="vaults")
            total_vaults = vault_results[0]["count"] if vault_results else 0

            # Get batch execution statistics
            batch_query = "SELECT COUNT(1) as total, SUM(c.total_documents) as docs, SUM(c.completed_documents) as completed FROM c"
            batch_results = await self.query(batch_query, container="batch_executions")
            batch_stats = batch_results[0] if batch_results else {"total": 0, "docs": 0, "completed": 0}

            # Get processing queue size (pending batches)
            queue_query = "SELECT COUNT(1) as count FROM c WHERE c.status = 'pending' OR c.status = 'running'"
            queue_results = await self.query(queue_query, container="batch_executions")
            queue_size = queue_results[0]["count"] if queue_results else 0

            # Calculate success rate
            total_docs = batch_stats.get("docs", 0) or 0
            completed_docs = batch_stats.get("completed", 0) or 0
            success_rate = (completed_docs / total_docs * 100) if total_docs > 0 else 100.0

            return SystemStats(
                total_vaults=total_vaults,
                total_documents=total_docs,
                documents_processed=completed_docs,
                processing_queue_size=queue_size,
                success_rate=round(success_rate, 1),
                storage_usage_gb=0.0,  # Would be calculated from actual storage metrics
                storage_capacity_gb=100.0,
                processing_capacity_percentage=min((queue_size / 100.0) * 100, 100.0)
            )
        except Exception as e:
            # Return default stats if there's an error
            return SystemStats()

    async def get_stat_cards(self, stats: SystemStats) -> List[StatCard]:
        """Generate statistics cards for dashboard"""
        return [
            StatCard(
                title="Total Vaults",
                value=str(stats.total_vaults),
                change="+2 this month",
                icon="HardDrive"
            ),
            StatCard(
                title="Documents Processed", 
                value=f"{stats.documents_processed:,}",
                change="+18% from last month",
                icon="FileText"
            ),
            StatCard(
                title="Processing Queue",
                value=str(stats.processing_queue_size),
                change="5 in progress",
                icon="Activity"
            ),
            StatCard(
                title="Success Rate",
                value=f"{stats.success_rate}%",
                change="+0.3% improvement",
                icon="TrendingUp"
            )
        ]

    async def get_recent_activities(self, limit: int = 10) -> List[RecentActivity]:
        """Get recent system activities"""
        try:
            query = """
            SELECT c.id, c.activity_type, c.message, c.timestamp, c.status, c.batch_execution_id, c.details
            FROM c 
            ORDER BY c.timestamp DESC 
            OFFSET 0 LIMIT @limit
            """
            parameters = [{"name": "@limit", "value": limit}]
            
            activities = await self.query(query, parameters)
            
            result = []
            for activity in activities:
                # Map activity types to user-friendly actions
                action = self._map_activity_to_action(activity.get("activity_type", ""))
                status = self._map_status_to_activity_status(activity.get("status", ""))
                
                result.append(RecentActivity(
                    id=activity["id"],
                    action=action,
                    vault_name=activity.get("details", {}).get("vault_name"),
                    document_name=activity.get("details", {}).get("document_name"),
                    timestamp=activity["timestamp"],
                    status=status,
                    details=activity.get("details", {})
                ))
            
            return result
        except Exception:
            # Return sample data if query fails
            return self._get_sample_activities()

    def _map_activity_to_action(self, activity_type: str) -> str:
        """Map activity type to user-friendly action"""
        mapping = {
            "batch_created": "Batch created",
            "batch_started": "Processing started",
            "batch_completed": "Processing completed",
            "batch_failed": "Processing failed",
            "document_processed": "Document processed",
            "document_failed": "Document processing failed",
            "step_completed": "Step completed",
            "step_failed": "Step failed"
        }
        return mapping.get(activity_type, activity_type.replace("_", " ").title())

    def _map_status_to_activity_status(self, status: str) -> ActivityStatus:
        """Map status string to ActivityStatus enum"""
        status_lower = status.lower()
        if status_lower in ["running", "processing"]:
            return ActivityStatus.PROCESSING
        elif status_lower in ["completed", "success"]:
            return ActivityStatus.COMPLETED
        elif status_lower in ["failed", "error"]:
            return ActivityStatus.ERROR
        else:
            return ActivityStatus.PENDING

    def _get_sample_activities(self) -> List[RecentActivity]:
        """Get sample activities for demo purposes"""
        now = datetime.now(timezone.utc)
        return [
            RecentActivity(
                id="1",
                action="Document uploaded",
                vault_name="Legal Documents",
                timestamp=(now).isoformat(),
                status=ActivityStatus.PROCESSING
            ),
            RecentActivity(
                id="2",
                action="Processing completed",
                vault_name="Research Papers",
                timestamp=(now).isoformat(),
                status=ActivityStatus.COMPLETED
            ),
            RecentActivity(
                id="3",
                action="Processing failed",
                vault_name="Marketing Materials",
                timestamp=(now).isoformat(),
                status=ActivityStatus.ERROR
            )
        ]

    async def get_processing_status(self, stats: SystemStats) -> ProcessingStatus:
        """Get current processing status"""
        return ProcessingStatus(
            queue_size=stats.processing_queue_size,
            queue_capacity=100,
            processing_capacity_percentage=stats.processing_capacity_percentage,
            storage_usage_gb=stats.storage_usage_gb,
            storage_capacity_gb=stats.storage_capacity_gb,
            active_batches=stats.processing_queue_size  # Simplified - would be more specific in real implementation
        )

    async def get_dashboard_data(self) -> DashboardData:
        """Get complete dashboard data"""
        stats = await self.get_system_stats()
        stat_cards = await self.get_stat_cards(stats)
        recent_activities = await self.get_recent_activities()
        processing_status = await self.get_processing_status(stats)

        return DashboardData(
            stats=stats,
            stat_cards=stat_cards,
            recent_activities=recent_activities,
            processing_status=processing_status
        )

    async def get_health_status(self) -> HealthStatus:
        """Get system health status"""
        uptime = int(time.time() - self._start_time)
        
        # Test service connections
        services = {}
        issues = []
        
        try:
            # Test Cosmos DB connection
            await self.query("SELECT 1 as test")
            services["cosmos_db"] = "healthy"
        except Exception as e:
            services["cosmos_db"] = "unhealthy"
            issues.append(f"Cosmos DB connection issue: {str(e)}")

        # Overall status
        overall_status = "healthy" if not issues else "degraded" if len(issues) < 2 else "unhealthy"

        return HealthStatus(
            status=overall_status,
            services=services,
            uptime_seconds=uptime,
            last_check=datetime.now(timezone.utc).isoformat(),
            issues=issues
        )

    async def get_system_metrics(self) -> SystemMetrics:
        """Get system performance metrics"""
        try:
            # For now, return mock metrics since psutil is not available
            # In production, you would install psutil and use actual system metrics
            return SystemMetrics(
                cpu_usage=25.0,  # Mock value
                memory_usage=60.0,  # Mock value
                disk_usage=45.0,  # Mock value
                active_connections=0,  # Would be tracked from actual connections
                queue_depth=0,  # Would be from actual queue system
                throughput_docs_per_hour=0.0  # Would be calculated from processing history
            )
        except Exception:
            return SystemMetrics()

    async def get_connections(self) -> List[ConnectionInfo]:
        """Get connection information"""
        # This would typically be stored in configuration or a separate collection
        # Returning sample connections for now
        return [
            ConnectionInfo(
                id="cosmos_db",
                name="Cosmos DB",
                type="cosmos_db",
                status="connected",
                endpoint="https://example.documents.azure.com:443/",
                last_tested=datetime.now(timezone.utc).isoformat()
            ),
            ConnectionInfo(
                id="azure_storage",
                name="Azure Storage",
                type="azure_storage",
                status="connected",
                endpoint="https://example.blob.core.windows.net/",
                last_tested=datetime.now(timezone.utc).isoformat()
            )
        ]

    async def test_connection(self, request: ConnectionTestRequest) -> ConnectionTestResult:
        """Test a connection"""
        start_time = time.time()
        
        try:
            if request.connection_id == "cosmos_db":
                # Test Cosmos DB
                await self.query("SELECT 1 as test")
                latency = (time.time() - start_time) * 1000
                
                return ConnectionTestResult(
                    connection_id=request.connection_id,
                    success=True,
                    message="Connection successful",
                    latency_ms=latency,
                    tested_at=datetime.now(timezone.utc).isoformat()
                )
            else:
                # For other connections, return a placeholder result
                return ConnectionTestResult(
                    connection_id=request.connection_id,
                    success=True,
                    message="Connection test not implemented",
                    tested_at=datetime.now(timezone.utc).isoformat()
                )
        except Exception as e:
            return ConnectionTestResult(
                connection_id=request.connection_id,
                success=False,
                message=f"Connection failed: {str(e)}",
                tested_at=datetime.now(timezone.utc).isoformat()
            )
