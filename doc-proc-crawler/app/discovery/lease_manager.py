"""
Distributed Worker Lease System

This module implements a lease-based coordination mechanism to ensure
that each source instance is processed by only one worker across all machines.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import socket

from azure.cosmos import exceptions
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient

from doc.proc.providers.credential_provider import get_azure_credential

logger = logging.getLogger(f"doc-proc-crawler.lease_manager")

@dataclass
class WorkerLease:
    """Represents a worker lease for a source instance"""
    source_instance_id: str
    worker_id: str
    machine_id: str
    process_id: str
    acquired_at: datetime
    expires_at: datetime
    renewed_at: datetime
    status: str  # 'active', 'expired', 'released'
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Cosmos DB storage"""
        return {
            'id': f"{self.source_instance_id}_{self.worker_id}",
            'partition_key': self.source_instance_id,
            'source_instance_id': self.source_instance_id,
            'worker_id': self.worker_id,
            'machine_id': self.machine_id,
            'process_id': self.process_id,
            'acquired_at': self.acquired_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'renewed_at': self.renewed_at.isoformat(),
            'status': self.status,
            'type': 'worker_lease'  # Document type for queries
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'WorkerLease':
        """Create WorkerLease from dictionary"""
        return cls(
            source_instance_id=data['source_instance_id'],
            worker_id=data['worker_id'],
            machine_id=data['machine_id'],
            process_id=data['process_id'],
            acquired_at=datetime.fromisoformat(data['acquired_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
            renewed_at=datetime.fromisoformat(data['renewed_at']),
            status=data['status']
        )


class LeaseManager:
    """
    Manages worker leases for source instances using Cosmos DB as coordination storage.
    Ensures only one worker per source instance across all machines.
    """
    
    def __init__(self, cosmos_endpoint: str, database_name: str,
                 container_name: str = "crawl_leases",
                 lease_duration_minutes: int = 10,
                 renewal_interval_minutes: int = 5):
        self.cosmos_endpoint = cosmos_endpoint
        self.database_name = database_name
        self.container_name = container_name
        self.lease_duration = timedelta(minutes=lease_duration_minutes)
        self.renewal_interval = timedelta(minutes=renewal_interval_minutes)
                
        # Machine and process identification
        self.machine_id = socket.gethostname()
        self.process_id = str(os.getpid())
        
        # Cosmos DB client
        self._cosmos_client: Optional[AsyncCosmosClient] = None
        
        # Active leases managed by this instance
        self._active_leases: Dict[str, WorkerLease] = {}
        self._renewal_tasks: Dict[str, asyncio.Task] = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize_cosmos_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Release all active leases
        await self.release_all_leases()
        
        if self._cosmos_client:
            await self._cosmos_client.close()
            
    async def _initialize_cosmos_client(self):
        """Initialize the async Cosmos DB client"""
        if not self._cosmos_client:
            self._cosmos_client = AsyncCosmosClient(
                url=self.cosmos_endpoint,
                credential=get_azure_credential()
            )
            
    async def _get_container(self):
        """Get the leases container, creating it if necessary"""
        if not self._cosmos_client:
            await self._initialize_cosmos_client()
            
        database = self._cosmos_client.get_database_client(self.database_name)
        
        try:
            container = database.get_container_client(self.container_name)
            # Test access to container
            await container.read()
        except exceptions.CosmosResourceNotFoundError:
            # Create container with source_instance_id as partition key
            logger.info(f"Creating worker leases container: {self.container_name}")
            container = await database.create_container(
                id=self.container_name,
                partition_key={'paths': ['/source_instance_id'], 'kind': 'Hash'},
                offer_throughput=400
            )
            
        return container
        
    async def try_acquire_lease(self, source_instance_id: str, worker_id: str = None) -> Optional[WorkerLease]:
        """
        Attempt to acquire a lease for a source instance.
        Returns the lease if successful, None if another worker holds the lease.
        """
        if not worker_id:
            worker_id = f"{self.machine_id}_{self.process_id}_{uuid.uuid4().hex[:8]}"
            
        now = datetime.now(timezone.utc)
        
        try:
            container = await self._get_container()
            
            # Check for existing active lease
            existing_lease = await self._get_active_lease(source_instance_id, container)
            
            if existing_lease:
                # Check if lease is expired
                if existing_lease.expires_at <= now:
                    logger.debug(f"Found expired lease for {source_instance_id}, attempting to acquire")
                    # Try to acquire expired lease
                    return await self._acquire_expired_lease(source_instance_id, worker_id, existing_lease, container)
                else:
                    # Active lease exists, cannot acquire
                    logger.debug(f"Active lease exists for {source_instance_id} (worker: {existing_lease.worker_id})")
                    return None
            
            # No existing lease, try to create new one
            lease = WorkerLease(
                source_instance_id=source_instance_id,
                worker_id=worker_id,
                machine_id=self.machine_id,
                process_id=self.process_id,
                acquired_at=now,
                expires_at=now + self.lease_duration,
                renewed_at=now,
                status='active'
            )
            
            # Attempt to create the lease (this may fail if another worker creates it first)
            try:
                await container.create_item(lease.to_dict())
                
                # Successfully acquired lease
                self._active_leases[source_instance_id] = lease
                
                # Start renewal task
                self._start_renewal_task(source_instance_id)
                
                logger.info(f"Acquired lease for source instance: {source_instance_id}")
                return lease
                
            except exceptions.CosmosResourceExistsError:
                # Another worker created the lease first
                logger.debug(f"Lease creation failed - another worker acquired lease for {source_instance_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error acquiring lease for {source_instance_id}: {e}")
            return None
            
    async def _get_active_lease(self, source_instance_id: str, container) -> Optional[WorkerLease]:
        """Get the active lease for a source instance"""
        try:
            query = """
                SELECT * FROM c 
                WHERE c.source_instance_id = @source_instance_id 
                AND c.type = 'worker_lease'
                AND c.status = 'active'
            """
            
            items = []
            async for item in container.query_items(
                query=query,
                parameters=[{"name": "@source_instance_id", "value": source_instance_id}],
                partition_key=source_instance_id
            ):
                items.append(item)
                
            if items:
                # Should only be one active lease per source instance
                return WorkerLease.from_dict(items[0])
                
        except Exception as e:
            logger.error(f"Error querying active lease for {source_instance_id}: {e}")
            
        return None
        
    async def _acquire_expired_lease(self, source_instance_id: str, worker_id: str, 
                                   existing_lease: WorkerLease, container) -> Optional[WorkerLease]:
        """Attempt to acquire an expired lease"""
        now = datetime.now(timezone.utc)
        
        try:
            # Create new lease
            new_lease = WorkerLease(
                source_instance_id=source_instance_id,
                worker_id=worker_id,
                machine_id=self.machine_id,
                process_id=self.process_id,
                acquired_at=now,
                expires_at=now + self.lease_duration,
                renewed_at=now,
                status='active'
            )
            
            # Use optimistic concurrency to replace the expired lease
            item_id = f"{source_instance_id}_{existing_lease.worker_id}"
            
            # First mark the old lease as expired
            old_lease_dict = existing_lease.to_dict()
            old_lease_dict['status'] = 'expired'
            
            await container.replace_item(
                item=item_id,
                body=old_lease_dict
            )
            
            # Then create the new lease
            await container.create_item(new_lease.to_dict())
            
            # Track the lease
            self._active_leases[source_instance_id] = new_lease
            
            # Start renewal task
            self._start_renewal_task(source_instance_id)

            logger.info(f"Acquired expired lease for source instance: {source_instance_id}")
            return new_lease
            
        except Exception as e:
            logger.error(f"Error acquiring expired lease for {source_instance_id}: {e}")
            return None
            
    def _start_renewal_task(self, source_instance_id: str):
        """Start background task to renew the lease"""
        if source_instance_id in self._renewal_tasks:
            self._renewal_tasks[source_instance_id].cancel()
            
        task = asyncio.create_task(self._renewal_loop(source_instance_id))
        self._renewal_tasks[source_instance_id] = task
        
    async def _renewal_loop(self, source_instance_id: str):
        """Background loop to renew lease"""
        while source_instance_id in self._active_leases:
            try:
                await asyncio.sleep(self.renewal_interval.total_seconds())
                
                if source_instance_id not in self._active_leases:
                    break
                    
                await self._renew_lease(source_instance_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in lease renewal loop for {source_instance_id}: {e}")
                # Continue trying to renew
                await asyncio.sleep(5)
                
    async def _renew_lease(self, source_instance_id: str):
        """Renew a lease"""
        if source_instance_id not in self._active_leases:
            return
            
        lease = self._active_leases[source_instance_id]
        now = datetime.now(timezone.utc)
        
        try:
            container = await self._get_container()
            
            # Update lease expiration
            lease.expires_at = now + self.lease_duration
            lease.renewed_at = now
            
            item_id = f"{source_instance_id}_{lease.worker_id}"
            
            await container.replace_item(
                item=item_id,
                body=lease.to_dict()
            )
            
            logger.debug(f"Renewed lease for source instance: {source_instance_id}")
            
        except Exception as e:
            logger.error(f"Failed to renew lease for {source_instance_id}: {e}")
            # If renewal fails, the lease will expire and another worker can take over
            
    async def release_lease(self, source_instance_id: str):
        """Release a lease"""
        if source_instance_id not in self._active_leases:
            return
            
        lease = self._active_leases[source_instance_id]
        
        try:
            # Cancel renewal task
            if source_instance_id in self._renewal_tasks:
                self._renewal_tasks[source_instance_id].cancel()
                del self._renewal_tasks[source_instance_id]
                
            container = await self._get_container()
            
            # Mark lease as released
            lease.status = 'released'
            item_id = f"{source_instance_id}_{lease.worker_id}"
            
            await container.replace_item(
                item=item_id,
                body=lease.to_dict()
            )
            
            # Remove from active leases
            del self._active_leases[source_instance_id]

            logger.info(f"Released lease for source instance: {source_instance_id}")

        except Exception as e:
            logger.error(f"Error releasing lease for {source_instance_id}: {e}")

    async def release_all_leases(self):
        """Release all active leases"""
        lease_ids = list(self._active_leases.keys())
        for source_instance_id in lease_ids:
            await self.release_lease(source_instance_id)
            
    def get_active_leases(self) -> Dict[str, WorkerLease]:
        """Get all active leases managed by this instance"""
        return self._active_leases.copy()
        
    async def cleanup_expired_leases(self):
        """Cleanup expired leases from the database (maintenance operation)"""
        try:
            container = await self._get_container()
            now = datetime.now(timezone.utc)
            
            # Query for expired leases
            query = """
                SELECT * FROM c 
                WHERE c.type = 'worker_lease' 
                AND c.status = 'active'
                AND c.expires_at < @now
            """
            
            expired_count = 0
            async for item in container.query_items(
                query=query,
                parameters=[{"name": "@now", "value": now.isoformat()}]
            ):
                try:
                    # Mark as expired
                    item['status'] = 'expired'
                    await container.replace_item(item=item['id'], body=item)
                    expired_count += 1
                except Exception as e:
                    logger.error(f"Error cleaning up expired lease {item['id']}: {e}")
                    
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired leases")
                
        except Exception as e:
            logger.error(f"Error during lease cleanup: {e}")