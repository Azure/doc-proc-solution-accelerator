from typing import Any, Dict, List, Optional
import yaml
import os
import time
import asyncio
from datetime import datetime, timezone
import logging

from app.services.base import BaseService
from app.db.cosmos import CosmosDb

logger = logging.getLogger("doc-proc-ui.app.services.source_catalog")

class SourceCatalogService(BaseService):
    """Service for managing source catalog operations"""

    def __init__(self, db: CosmosDb, 
                       container_name: str = "source_catalog"):
        
        super().__init__(db, container_name)
        self._source_catalog_cache = None

    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate source item against catalog schema"""
        required_fields = ["id", "name", "type"]
        return all(field in item for field in required_fields)
    
    async def _load_catalog_from_yaml(self) -> Dict[str, Any]:
        """Load source catalog from YAML file"""
        catalog_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/source_catalog.yaml")
        catalog = {"sources": []}
        
        try:
            with open(catalog_path, 'r') as file:
                catalog = yaml.safe_load(file)
        except FileNotFoundError as e:
            logger.error(f"Error loading source catalog from path {catalog_path}: {e}")
            raise e
        
        return catalog
        
    async def initialize_source_catalog(self) -> Dict[str, Any]:
        """Initialize sources from catalog if they don't exist"""
        logger.info("Initializing sources from catalog...")
        
        _catalog = await self._load_catalog_from_yaml()
        _sources = _catalog.get("sources", [])

        # Store catalog sources in Cosmos DB for persistence and updates
        result = await self._sync_catalog_sources_to_db(_sources)

        logger.info(f"Added {result.get('created_count', 0)} new sources from catalog to database")

        # run again to get updated count
        catalog_sources = await self.list_catalog_sources()
        self._source_catalog_cache = catalog_sources
        logger.info(f"Total sources in catalog: {len(catalog_sources)}")

        return {
            "created_count": result.get("created_count", 0),
            "total_catalog_sources": len(catalog_sources)
        }

    async def _sync_catalog_sources_to_db(self, catalog_sources: List[Dict[str, Any]]):
        """Sync catalog steps to Cosmos DB catalog container"""
        
        created_count = 0

        for source in catalog_sources:
            source_id = source.get("id")
            existing = await self.get_by_id(source_id)

            # Only update if not exists or version changed
            if not existing or existing.get("version") != source.get("version"):
                source_doc = {
                    **source,
                    "catalog_type": "source_definition",
                    "synced_at": datetime.now(timezone.utc).isoformat()
                }
                await self.update(source_doc)
                created_count += 1

        return {"created_count": created_count}
    
    async def list_catalog_sources(self) -> List[Dict[str, Any]]:
        """List all sources from the catalog"""
        try:
            sources = await self.list_all()
            logger.info(f"Retrieved {len(sources)} sources from catalog")
            return sources
        except Exception as e:
            logger.error(f"Failed to list catalog sources: {e}")
            raise

    async def get_catalog_source_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific source from the catalog by ID"""
        try:
            source = await self.get_by_id(source_id)
            if source:
                logger.info(f"Retrieved source '{source_id}' from catalog")
            else:
                logger.warning(f"Source '{source_id}' not found in catalog")
            return source
        except Exception as e:
            logger.error(f"Failed to get catalog source '{source_id}': {e}")
            raise

    async def get_sources_by_type(self, source_type: str) -> List[Dict[str, Any]]:
        """Get all sources of a specific type"""
        try:
            # Use the query method from BaseService to filter by type
            query = "SELECT * FROM c WHERE c.type = @type"
            parameters = [{"name": "@type", "value": source_type}]
            
            sources = await self.query(query, parameters)
            logger.info(f"Retrieved {len(sources)} sources of type '{source_type}'")
            return sources
        except Exception as e:
            logger.error(f"Failed to get sources by type '{source_type}': {e}")
            raise

    async def get_sources_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Get sources that have any of the specified tags"""
        try:
            # Build query to find sources with any of the specified tags
            tag_conditions = []
            parameters = []
            
            for i, tag in enumerate(tags):
                tag_conditions.append(f"ARRAY_CONTAINS(c.tags, @tag{i})")
                parameters.append({"name": f"@tag{i}", "value": tag})
            
            query = f"SELECT * FROM c WHERE {' OR '.join(tag_conditions)}"
            
            sources = await self.query(query, parameters)
            logger.info(f"Retrieved {len(sources)} sources with tags {tags}")
            return sources
        except Exception as e:
            logger.error(f"Failed to get sources by tags {tags}: {e}")
            raise