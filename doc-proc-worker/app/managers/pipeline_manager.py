import logging
from typing import Any, Dict, List, Optional
import yaml
import os

from app.proxy.cosmos import CosmosDb

from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.pipeline.pipeline_config import PipelineConfig, PipelineSettingsConfig, ServiceInstanceConfig
from doc.proc.step.step_base import StepInstanceConfig
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_config import ServiceConfig
from doc.proc.source.source_config import SourceConfig
from doc.proc.source.source_base import SourceInstanceConfig

logger = logging.getLogger("doc-proc-worker.app.pipeline_manager")

class PipelineManager():
    """Manages pipeline operations"""
    
    def __init__(self, 
                 db: CosmosDb, 
                 pipelines_container_name: str = "pipelines",
                 step_catalog_container_name: str = "step_catalog",
                 step_instances_container_name: str = "step_instances",
                 service_catalog_container_name: str = "service_catalog",
                 service_instances_container_name: str = "service_instances",
                 source_catalog_container_name: str = "source_catalog",
                 source_instances_container_name: str = "source_instances"
                 ):
        
        self._db = db
        self._pipelines_container_name = pipelines_container_name
        self._step_catalog_container_name = step_catalog_container_name
        self._service_catalog_container_name = service_catalog_container_name
        self._step_instances_container_name = step_instances_container_name
        self._service_instances_container_name = service_instances_container_name
        self._source_instances_container_name = source_instances_container_name
        self._source_catalog_container_name = source_catalog_container_name
        self._config_cache = None
        self._pipeline_cache = {}
    
        logger.info(f"PipelineManager initialized with pipelines_container: {pipelines_container_name}, step_catalog_container: {step_catalog_container_name}, service_catalog_container: {service_catalog_container_name}")
  

    async def load_pipeline(self, pipeline_name: str) -> Optional[Pipeline]:
        """Load a pipeline by name"""
        if pipeline_name in self._pipeline_cache:
            return self._pipeline_cache[pipeline_name]
        
        # Load step and service catalogs
        step_catalog_config = await self._load_step_catalog_from_db()
        service_catalog_config = await self._load_service_catalog_from_db()
        source_catalog_config = await self._load_source_catalog_from_db()
        
        # Load step and service instances
        service_instances = await self._load_service_instances_from_db()
        source_instances = await self._load_source_instances_from_db()
        step_instances = await self._load_step_instances_from_db(service_instances=service_instances, step_catalog_config=step_catalog_config)
                
        # Create pipeline config
        pipeline_config = await self._load_pipeline_config(pipeline_name, step_instances, service_instances, source_instances)
        
        if pipeline_config:
            pipeline = await Pipeline.create(
                pipeline_config=pipeline_config,
                step_catalog_config=step_catalog_config,
                service_catalog_config=service_catalog_config,
                source_catalog_config=source_catalog_config
            )
            
            # Cache the pipeline
            self._pipeline_cache[pipeline_name] = pipeline
            
            return pipeline

        return None

    # async def load_pipeline(self, pipeline_name: str) -> Optional[Pipeline]:
    #     """Load a pipeline by name"""
    #     if pipeline_name in self._pipeline_cache:
    #         return self._pipeline_cache[pipeline_name]
        
    #     # Load step and service catalogs
    #     step_catalog_config = await self._load_step_catalog()
    #     service_catalog_config = await self._load_service_catalog()
            
    #     # Create pipeline config
    #     pipeline_config = await self._load_pipeline_config(step_catalog_config, service_catalog_config)
        
    #     if pipeline_config:
    #         for pipeline in pipeline_config:
    #             if pipeline.name == pipeline_name:
    #                 # Create pipeline instance
    #                 pipeline = await Pipeline.create(
    #                     pipeline_config=pipeline,
    #                     step_catalog_config=step_catalog_config,
    #                     service_catalog_config=service_catalog_config
    #                 )
                    
    #                 # Cache the pipeline
    #                 self._pipeline_cache[pipeline_name] = pipeline
                    
    #                 return pipeline

    #     return None

    # # TODO: make this load from Cosmos DB instead
    # async def _load_pipeline_config(self, step_catalog_config, service_catalog_config) -> List[PipelineConfig]:
    #     """Load pipeline config from YAML"""

    #     # load the pipeline config
    #     config_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/pipeline_config.yaml")
    #     try:
    #         with open(config_path, 'r') as file:
    #             yaml_str = file.read()
    #         return PipelineConfig.from_yaml(yaml_str, step_catalog_config=step_catalog_config, service_catalog_config=service_catalog_config)
    #     except FileNotFoundError:
    #         raise

    # # TODO: make this load from Cosmos DB instead
    # async def _load_step_catalog(self) -> List[StepConfig]:
    #     """Load step catalog from YAML"""
    #     catalog_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/step_catalog.yaml")
    #     try:
    #         with open(catalog_path, 'r') as file:
    #             yaml_str = file.read()
    #         return StepConfig.from_yaml(yaml_str)
    #     except FileNotFoundError:
    #         raise

    # # TODO: make this load from Cosmos DB instead
    # async def _load_service_catalog(self) -> List[ServiceConfig]:
    #     """Load service catalog from YAML"""
    #     catalog_path = os.path.join(os.path.dirname(__file__), "../../../doc-proc-lib/service_catalog.yaml")
    #     try:
    #         with open(catalog_path, 'r') as file:
    #             yaml_str = file.read()
    #         return ServiceConfig.from_yaml(yaml_str)
    #     except FileNotFoundError:
    #         raise

    
    
    async def _get_pipeline_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a pipeline instance by name from Cosmos DB"""
        query = "SELECT * FROM c WHERE c.name = @name"
        parameters = [{"name": "@name", "value": name}]
        results = self._db.list(container=self._pipelines_container_name, query=query, parameters=parameters)
        return results[0] if results else None

    async def _load_pipeline_config(self, pipeline_name:str, step_instances:List[StepInstanceConfig], 
                                    service_instances:List[ServiceInstanceConfig],
                                    source_instances:List[SourceInstanceConfig]) -> PipelineConfig:
        """Load pipeline config from Cosmos DB"""
        query = "SELECT * FROM c WHERE c.name = @name"
        parameters = [{"name": "@name", "value": pipeline_name}]
        pipeline_definitions = self._db.list(container=self._pipelines_container_name, query=query, parameters=parameters)
        if not pipeline_definitions:
            return None
        
        _name = pipeline_definitions[0].get("name", "")
        _description = pipeline_definitions[0].get("description", "")
        _version = pipeline_definitions[0].get("version", "")
        _settings = pipeline_definitions[0].get("settings", {})
        _steps = pipeline_definitions[0].get("steps", [])
        _steps_ids = {}
        for step in _steps:
            _steps_ids[step['name']] = ""

        _execution_sequence = pipeline_definitions[0].get("execution_sequence", [])
        if not _name or not _settings:
            raise ValueError(f"Pipeline definition is missing required fields: name or settings.")

        _pipeline_name = _name
        _pipeline_description = _description
        _pipeline_version = _version
        _pipeline_settings = PipelineSettingsConfig(**_settings)

        # find step instances for this pipeline from the provided step_instances list
        # - filter step_instances where instance.id is in _steps
        _pipeline_step_instances = [instance for instance in step_instances if instance.name in _steps_ids]
        if len(_pipeline_step_instances) != len(_steps_ids):
            raise ValueError(f"Pipeline '{_pipeline_name}' has step instances that could not be found in the provided step instances. Expected {len(_steps_ids)} but found {len(_pipeline_step_instances)}. Please ensure all step instances are provided.")

        # find service instances for this pipeline from the provided service_instances list
        # - filter service_instances where instance.id is in any of the step instances' services
        _service_instance_names = set()
        for step_instance in _pipeline_step_instances:
            step_instance.services and len(step_instance.services) > 0 and _service_instance_names.update(step_instance.services)

        _pipeline_service_instances = [instance for instance in service_instances if instance.name in _service_instance_names]
        if len(_pipeline_service_instances) != len(_service_instance_names):
            raise ValueError(f"Pipeline '{_pipeline_name}' has service instances that could not be found in the provided service instances. Expected {len(_service_instance_names)} but found {len(_pipeline_service_instances)}. Please ensure all service instances are provided.")

        # find the execution sequence for this pipeline from the provided step_instances list
        # use instance name in execution sequence, as the Pipeline uses instance names
        _pipeline_execution_sequence = [instance.name for _step_id in _execution_sequence for instance in _pipeline_step_instances if instance.id == _step_id]
        

        # create PipelineConfig
        pipeline_config = PipelineConfig(name=_pipeline_name,
                                         description=_pipeline_description,
                                         version=_pipeline_version,
                                         steps=_pipeline_step_instances,
                                         execution_sequence=_pipeline_execution_sequence,
                                         settings=_pipeline_settings,
                                         service_instances=_pipeline_service_instances,
                                         source_instances=source_instances
                                            )


        return pipeline_config

    async def _load_step_instances_from_db(self, 
                                           service_instances: List[ServiceInstanceConfig],
                                        step_catalog_config: List[StepConfig]
                                           ) -> List[StepInstanceConfig]:
        """Load step instances from Cosmos DB"""
        query = "SELECT * FROM c"
        step_instances = self._db.list(container=self._step_instances_container_name, query=query)
        
        # Extract service instance names from step instances
        service_instances_dict = {instance.id: instance for instance in service_instances}
        for item in step_instances:
            
            #get the default config
            step_config = next((step for step in step_catalog_config if step.id == item.get("step_catalog_id")), None)

            if step_config and step_config.settings_schema:
                for setting in step_config.settings_schema:
                    for key in setting[1]:
                        sub_setting = setting[1][key]
                        if item.get("settings") is None:
                            item["settings"] = {}
                        if key not in item["settings"]:
                            item["settings"][key] = sub_setting.default

            if "services" in item and item["services"] and isinstance(item["services"], list):
                linked_services = []
                for service_id in item["services"]:
                    if service_id in service_instances_dict:
                        linked_services.append(service_instances_dict[service_id].name)
                    else:
                        raise ValueError(f"Service instance with id '{service_id}' referenced in step instance '{item.get('name', '')}' not found in provided service instances.")
                    
                item["services"] = linked_services
        return [StepInstanceConfig(**item) for item in step_instances]
    
    # TODO: cache the loaded config
    async def _load_step_catalog_from_db(self) -> List[StepConfig]:
        """Load step catalog from Cosmos DB"""
        query = "SELECT * FROM c"
        step_definitions = self._db.list(container=self._step_catalog_container_name, query=query)
        return [StepConfig.from_dict(step) for step in step_definitions]

    async def _load_source_catalog_from_db(self) -> List[SourceConfig]:
        """Load source catalog from Cosmos DB"""
        query = "SELECT * FROM c"
        source_definitions = self._db.list(container=self._source_catalog_container_name, query=query)
        return [SourceConfig.from_dict(source) for source in source_definitions]

    # TODO: cache the loaded config
    async def _load_service_instances_from_db(self) -> List[ServiceInstanceConfig]:
        """Load service instances from Cosmos DB"""
        query = "SELECT * FROM c"
        results = self._db.list(container=self._service_instances_container_name, query=query)
        return [ServiceInstanceConfig(**item) for item in results]

    async def _load_source_instances_from_db(self) -> List[SourceInstanceConfig]:
        """Load source instances from Cosmos DB"""
        query = "SELECT * FROM c"
        results = self._db.list(container=self._source_instances_container_name, query=query)
        return [SourceInstanceConfig(**item) for item in results]

    # TODO: cache the loaded config
    async def _load_service_catalog_from_db(self) -> List[ServiceConfig]:
        """Load service catalog from Cosmos DB"""
        query = "SELECT * FROM c"
        service_definitions = self._db.list(container=self._service_catalog_container_name, query=query)
    
        return [ServiceConfig.from_dict(service) for service in service_definitions]
    
    
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
