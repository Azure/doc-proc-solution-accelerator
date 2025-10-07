"""
Source Instance Discovery System

This module handles automatic discovery of source instances from Cosmos DB
and manages their lifecycle for distributed crawler workers.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from azure.cosmos import exceptions
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient

from doc.proc.providers.credential_provider import get_azure_credential

# Import from crawler models (which imports from doc-proc-api)
from app.models.crawler import SourceInstance


logger = logging.getLogger(f"doc-proc-crawler.source_discovery")

@dataclass 
class SourceInstanceChange:
    """Represents a change in source instances"""
    instance_id: str
    change_type: str  # 'added', 'removed', 'updated'
    instance: Optional[SourceInstance] = None


class SourceInstanceDiscovery:
    """
    Discovers and monitors source instances from Cosmos DB.
    Detects additions, deletions, and updates to source instances.
    """
    
    def __init__(self, cosmos_endpoint: str, database_name: str, 
                 container_name: str = "source_instances"):
        self.cosmos_endpoint = cosmos_endpoint
        self.database_name = database_name
        self.container_name = container_name
        
        # Track current state
        self._current_instances: Dict[str, SourceInstance] = {}
        self._last_discovery: Optional[datetime] = None
        
        # Cosmos DB client (will be initialized when needed)
        self._cosmos_client: Optional[AsyncCosmosClient] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize_cosmos_client()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._cosmos_client:
            await self._cosmos_client.close()
            
    async def _initialize_cosmos_client(self):
        """Initialize the async Cosmos DB client"""
        if not self._cosmos_client:
            self._cosmos_client = AsyncCosmosClient(
                url=self.cosmos_endpoint, 
                credential=get_azure_credential()
            )
            
    async def discover_source_instances(self) -> List[SourceInstance]:
        """
        Discover all active source instances from Cosmos DB.
        Returns only enabled source instances.
        """
        logger.debug("Discovering source instances from Cosmos DB...")
        
        try:
            if not self._cosmos_client:
                await self._initialize_cosmos_client()
                
            database = self._cosmos_client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            
            # Query for enabled source instances
            query = """
                SELECT * FROM c 
                WHERE c.enabled = true 
                ORDER BY c.created_at DESC
            """
            
            instances = []
            async for item in container.query_items(
                query=query
            ):
                try:
                    # Convert to SourceInstance model
                    instance = SourceInstance(**item)
                    instances.append(instance)
                    logger.debug(f"Found source instance: {instance.id} - {instance.name}")
                except Exception as e:
                    logger.warning(f"Failed to parse source instance {item.get('id', 'unknown')}: {e}")
                    continue

            logger.info(f"Discovered {len(instances)} active source instances")
            return instances
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Source instances container '{self.container_name}' not found")
            return []
        except Exception as e:
            logger.error(f"Failed to discover source instances: {e}")
            raise
            
    async def detect_changes(self) -> List[SourceInstanceChange]:
        """
        Detect changes since last discovery.
        Returns list of changes (additions, removals, updates).
        """
        current_instances = await self.discover_source_instances()
        changes = []
        
        # Convert to dict for easier comparison
        current_dict = {inst.id: inst for inst in current_instances}
        
        # Detect additions and updates
        for instance_id, instance in current_dict.items():
            if instance_id not in self._current_instances:
                # New instance
                changes.append(SourceInstanceChange(
                    instance_id=instance_id,
                    change_type='added',
                    instance=instance
                ))
                logger.info(f"Detected new source instance: {instance_id}")
            else:
                # Check for updates (compare updated_at timestamps)
                old_instance = self._current_instances[instance_id]
                if instance.updated_at != old_instance.updated_at:
                    changes.append(SourceInstanceChange(
                        instance_id=instance_id,
                        change_type='updated', 
                        instance=instance
                    ))
                    logger.info(f"Detected updated source instance: {instance_id}")
        
        # Detect removals (disabled or deleted instances)
        for instance_id in self._current_instances:
            if instance_id not in current_dict:
                changes.append(SourceInstanceChange(
                    instance_id=instance_id,
                    change_type='removed'
                ))
                logger.info(f"Detected removed source instance: {instance_id}")
        
        # Update current state
        self._current_instances = current_dict
        self._last_discovery = datetime.now(timezone.utc)
        
        if changes:
            logger.info(f"Detected {len(changes)} source instance changes")
        else:
            logger.debug("No source instance changes detected")

        return changes
        
    async def get_source_instance(self, instance_id: str) -> Optional[SourceInstance]:
        """Get a specific source instance by ID"""
        try:
            if not self._cosmos_client:
                await self._initialize_cosmos_client()
                
            database = self._cosmos_client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            
            item = await container.read_item(
                item=instance_id,
                partition_key=instance_id
            )
            
            return SourceInstance(**item)
            
        except exceptions.CosmosResourceNotFoundError:
            logger.debug(f"Source instance {instance_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get source instance {instance_id}: {e}")
            return None
            
    def get_current_instances(self) -> Dict[str, SourceInstance]:
        """Get currently known source instances"""
        return self._current_instances.copy()
        
    def get_last_discovery_time(self) -> Optional[datetime]:
        """Get timestamp of last discovery"""
        return self._last_discovery
