from typing import List

from fastapi import APIRouter, HTTPException, Depends

from ..models.dashboard import (
    DashboardData, SystemStats, StatCard, RecentActivity, ProcessingStatus,
    HealthStatus, SystemMetrics, ConnectionInfo, ConnectionTestRequest,
    ConnectionTestResult
)
from ..services.dashboard_service import DashboardService
from ..dependencies import get_dashboard_service

router = APIRouter()


@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    service: DashboardService = Depends(get_dashboard_service)
):
    """Get complete dashboard data"""
    try:
        dashboard_data = await service.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    service: DashboardService = Depends(get_dashboard_service)
):
    """Get system statistics"""
    try:
        stats = await service.get_system_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")


@router.get("/stats/cards", response_model=List[StatCard])
async def get_stat_cards(
    service: DashboardService = Depends(get_dashboard_service)
):
    """Get statistics cards for dashboard"""
    try:
        stats = await service.get_system_stats()
        cards = await service.get_stat_cards(stats)
        return cards
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stat cards: {str(e)}")


@router.get("/activities", response_model=List[RecentActivity])
async def get_recent_activities(
    limit: int = 10,
    service: DashboardService = Depends(get_dashboard_service)
):
    """Get recent system activities"""
    try:
        activities = await service.get_recent_activities(limit=limit)
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent activities: {str(e)}")


@router.get("/status/processing", response_model=ProcessingStatus)
async def get_processing_status(
    service: DashboardService = Depends(get_dashboard_service)
):
    """Get current processing status"""
    try:
        stats = await service.get_system_stats()
        processing_status = await service.get_processing_status(stats)
        return processing_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}")


@router.get("/health", response_model=HealthStatus)
async def get_health_status(
    service: DashboardService = Depends(get_dashboard_service)
):
    """Get system health status"""
    try:
        health = await service.get_health_status()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    service: DashboardService = Depends(get_dashboard_service)
):
    """Get system performance metrics"""
    try:
        metrics = await service.get_system_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.get("/connections", response_model=List[ConnectionInfo])
async def get_connections(
    service: DashboardService = Depends(get_dashboard_service)
):
    """Get connection information"""
    try:
        connections = await service.get_connections()
        return connections
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connections: {str(e)}")


@router.post("/connections/test", response_model=ConnectionTestResult)
async def test_connection(
    request: ConnectionTestRequest,
    service: DashboardService = Depends(get_dashboard_service)
):
    """Test a connection"""
    try:
        result = await service.test_connection(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test connection: {str(e)}")
