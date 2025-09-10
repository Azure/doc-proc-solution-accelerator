from typing import Any, Dict, List, Optional
import yaml
import os

from app.services.cosmos_db_service import CosmosDBService
from app.db.cosmos import CosmosDb

from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.pipeline.pipeline_config import PipelineConfig
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_config import ServiceConfig

class PipelineService(CosmosDBService):
    """Service for managing pipeline operations"""
    
    def __init__(self, db: CosmosDb):
        super().__init__(db, "pipelines")
        self._config_cache = None
        self._pipeline_cache = {}
    
    async def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate pipeline item"""
        required_fields = ["id", "name", "steps", "execution_sequence"]
        return all(field in item for field in required_fields)
    
    # async def get_config(self) -> Dict[str, Any]:
    #     """Load pipeline configuration from YAML file"""
    #     if self._config_cache is None:
    #         config_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/pipeline_config.yaml")
    #         print(f"Loading pipeline configuration from {config_path}")
    #         try:
    #             with open(config_path, 'r') as file:
    #                 self._config_cache = yaml.safe_load(file)
    #         except FileNotFoundError:
    #             self._config_cache = {"pipelines": [], "service_instances": []}
    #     return self._config_cache
    
    # async def get_pipeline_config(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
    #     """Get pipeline definition from config by name"""
    #     config = await self.get_config()
    #     for pipeline in config.get("pipelines", []):
    #         if pipeline.get("name") == pipeline_name:
    #             return pipeline
    #     return None

    async def load_pipeline(self, pipeline_name: str) -> Optional[Pipeline]:
        """Load a pipeline by name"""
        if pipeline_name in self._pipeline_cache:
            return self._pipeline_cache[pipeline_name]
        
        # Load step and service catalogs
        step_catalog_config = await self._load_step_catalog()
        service_catalog_config = await self._load_service_catalog()
            
        # Create pipeline config
        pipeline_config = await self._load_pipeline_config(step_catalog_config, service_catalog_config)
        
        if pipeline_config:
            for pipeline in pipeline_config:
                if pipeline.name == pipeline_name:
                    # Create pipeline instance
                    pipeline = await Pipeline.create(
                        pipeline_config=pipeline,
                        step_catalog_config=step_catalog_config,
                        service_catalog_config=service_catalog_config
                    )
                    
                    # Cache the pipeline
                    self._pipeline_cache[pipeline_name] = pipeline
                    
                    return pipeline

        return None

    # TODO: make this load from Cosmos DB instead
    async def _load_pipeline_config(self, step_catalog_config, service_catalog_config) -> List[PipelineConfig]:
        """Load pipeline config from YAML"""

        # load the pipeline config
        config_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/pipeline_config.yaml")
        try:
            with open(config_path, 'r') as file:
                yaml_str = file.read()
            return PipelineConfig.from_yaml(yaml_str, step_catalog_config=step_catalog_config, service_catalog_config=service_catalog_config)
        except FileNotFoundError:
            raise

    # TODO: make this load from Cosmos DB instead
    async def _load_step_catalog(self) -> List[StepConfig]:
        """Load step catalog from YAML"""
        catalog_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/step_catalog.yaml")
        try:
            with open(catalog_path, 'r') as file:
                yaml_str = file.read()
            return StepConfig.from_yaml(yaml_str)
        except FileNotFoundError:
            raise

    # TODO: make this load from Cosmos DB instead
    async def _load_service_catalog(self) -> List[ServiceConfig]:
        """Load service catalog from YAML"""
        catalog_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/service_catalog.yaml")
        try:
            with open(catalog_path, 'r') as file:
                yaml_str = file.read()
            return ServiceConfig.from_yaml(yaml_str)
        except FileNotFoundError:
            raise

    # async def list_config_pipelines(self) -> List[Dict[str, Any]]:
    #     """List all pipelines from configuration"""
    #     config = await self.get_config()
    #     return config.get("pipelines", [])
    
    # async def get_service_instances(self) -> List[Dict[str, Any]]:
    #     """Get all service instances from configuration"""
    #     config = await self.get_config()
    #     return config.get("service_instances", [])
    
    # async def create_pipeline_instance(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
    #     """Create a pipeline instance based on configuration"""
    #     config_pipeline = await self.get_pipeline_by_name(pipeline_data.get("config_name"))
    #     if config_pipeline:
    #         # Use configuration as base
    #         instance = {
    #             "id": pipeline_data.get("name", config_pipeline.get("name")),
    #             "name": pipeline_data.get("name", config_pipeline.get("name")),
    #             "description": config_pipeline.get("description"),
    #             "version": config_pipeline.get("version"),
    #             "steps": config_pipeline.get("steps", []),
    #             "execution_sequence": config_pipeline.get("execution_sequence", []),
    #             "settings": {**config_pipeline.get("settings", {}), **pipeline_data.get("settings", {})},
    #             "config_name": pipeline_data.get("config_name"),
    #             "status": pipeline_data.get("status", "active"),
    #             "created_at": pipeline_data.get("created_at"),
    #             "updated_at": pipeline_data.get("updated_at")
    #         }
    #     else:
    #         # Create custom pipeline
    #         instance = {
    #             "id": pipeline_data.get("name"),
    #             "name": pipeline_data.get("name"),
    #             "description": pipeline_data.get("description", ""),
    #             "version": pipeline_data.get("version", "1.0"),
    #             "steps": pipeline_data.get("steps", []),
    #             "execution_sequence": pipeline_data.get("execution_sequence", []),
    #             "settings": pipeline_data.get("settings", {}),
    #             "status": pipeline_data.get("status", "active"),
    #             "created_at": pipeline_data.get("created_at"),
    #             "updated_at": pipeline_data.get("updated_at")
    #         }
        
    #     if await self.validate_item(instance):
    #         return await self.create(instance)
    #     else:
    #         raise ValueError("Invalid pipeline instance data")
    
    # async def get_pipeline_steps(self, pipeline_id: str) -> List[Dict[str, Any]]:
    #     """Get all steps for a specific pipeline"""
    #     pipeline = await self.get_by_id(pipeline_id)
    #     if pipeline:
    #         return pipeline.get("steps", [])
    #     return []
    
    # async def update_pipeline_status(self, pipeline_id: str, status: str) -> Optional[Dict[str, Any]]:
    #     """Update pipeline status"""
    #     pipeline = await self.get_by_id(pipeline_id)
    #     if pipeline:
    #         pipeline["status"] = status
    #         pipeline["updated_at"] = pipeline.get("updated_at")  # This should be set by the caller
    #         return await self.update(pipeline)
    #     return None
    
    # async def get_pipelines_by_status(self, status: str) -> List[Dict[str, Any]]:
    #     """Get all pipelines with a specific status"""
    #     query = "SELECT * FROM c WHERE c.status = @status"
    #     parameters = [{"name": "@status", "value": status}]
    #     return await self.list_all(query, parameters)
