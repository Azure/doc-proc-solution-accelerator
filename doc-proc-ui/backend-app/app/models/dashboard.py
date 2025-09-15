from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ActivityStatus(str, Enum):
    """Enum for activity status"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    PENDING = "pending"


class SystemStats(BaseModel):
    """System-wide statistics"""
    total_vaults: int = Field(default=0, description="Total number of vaults")
    total_documents: int = Field(default=0, description="Total number of documents")
    documents_processed: int = Field(default=0, description="Number of processed documents")
    processing_queue_size: int = Field(default=0, description="Number of documents in processing queue")
    success_rate: float = Field(default=0.0, description="Processing success rate percentage")
    storage_usage_gb: float = Field(default=0.0, description="Storage usage in GB")
    storage_capacity_gb: float = Field(default=100.0, description="Storage capacity in GB")
    processing_capacity_percentage: float = Field(default=0.0, description="Processing capacity usage percentage")


class StatCard(BaseModel):
    """Statistics card for dashboard"""
    title: str = Field(..., description="Card title")
    value: str = Field(..., description="Current value")
    change: str = Field(..., description="Change description")
    icon: str = Field(..., description="Icon name")
    trend: Optional[str] = Field(None, description="Trend direction (up/down/neutral)")


class RecentActivity(BaseModel):
    """Recent activity item"""
    id: str = Field(..., description="Activity ID")
    action: str = Field(..., description="Action description")
    vault_name: Optional[str] = Field(None, description="Associated vault name")
    document_name: Optional[str] = Field(None, description="Associated document name")
    timestamp: str = Field(..., description="Activity timestamp")
    status: ActivityStatus = Field(..., description="Activity status")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class ProcessingStatus(BaseModel):
    """Current processing status"""
    queue_size: int = Field(default=0, description="Current queue size")
    queue_capacity: int = Field(default=100, description="Queue capacity")
    processing_capacity_percentage: float = Field(default=0.0, description="Processing capacity usage")
    storage_usage_gb: float = Field(default=0.0, description="Storage usage in GB")
    storage_capacity_gb: float = Field(default=100.0, description="Storage capacity in GB")
    active_batches: int = Field(default=0, description="Number of active batch executions")


class DashboardData(BaseModel):
    """Complete dashboard data"""
    stats: SystemStats = Field(..., description="System statistics")
    stat_cards: List[StatCard] = Field(..., description="Statistics cards")
    recent_activities: List[RecentActivity] = Field(..., description="Recent activities")
    processing_status: ProcessingStatus = Field(..., description="Current processing status")


class HealthStatus(BaseModel):
    """System health status"""
    status: str = Field(..., description="Overall health status")
    services: Dict[str, str] = Field(default_factory=dict, description="Service health statuses")
    uptime_seconds: int = Field(default=0, description="System uptime in seconds")
    last_check: str = Field(..., description="Last health check timestamp")
    issues: List[str] = Field(default_factory=list, description="Current issues")


class SystemMetrics(BaseModel):
    """System metrics for monitoring"""
    cpu_usage: float = Field(default=0.0, description="CPU usage percentage")
    memory_usage: float = Field(default=0.0, description="Memory usage percentage")
    disk_usage: float = Field(default=0.0, description="Disk usage percentage")
    network_io: Dict[str, float] = Field(default_factory=dict, description="Network I/O metrics")
    active_connections: int = Field(default=0, description="Number of active connections")
    queue_depth: int = Field(default=0, description="Current queue depth")
    throughput_docs_per_hour: float = Field(default=0.0, description="Document processing throughput")


class ConnectionInfo(BaseModel):
    """Connection configuration information"""
    id: str = Field(..., description="Connection ID")
    name: str = Field(..., description="Connection name")
    type: str = Field(..., description="Connection type (azure_storage, cosmos_db, etc.)")
    status: str = Field(..., description="Connection status")
    endpoint: Optional[str] = Field(None, description="Connection endpoint")
    last_tested: Optional[str] = Field(None, description="Last connection test timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConnectionTestRequest(BaseModel):
    """Request to test a connection"""
    connection_id: str = Field(..., description="Connection ID to test")


class ConnectionTestResult(BaseModel):
    """Result of a connection test"""
    connection_id: str = Field(..., description="Connection ID")
    success: bool = Field(..., description="Whether the test was successful")
    message: str = Field(..., description="Test result message")
    latency_ms: Optional[float] = Field(None, description="Connection latency in milliseconds")
    tested_at: str = Field(..., description="Test timestamp")
