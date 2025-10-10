import logging
from typing import Any, Dict, List, Optional
import yaml
import os

from app.proxy.cosmos import CosmosDb

from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.pipeline.pipeline_config import PipelineConfig, PipelineSettingsConfig, ServiceInstanceConfig
from doc.proc.source.source_instance_config import SourceInstanceConfig
from doc.proc.step.step_base import StepInstanceConfig
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_config import ServiceConfig
from doc.proc.source.source_config import SourceConfig

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
                 source_instances_container_name: str = "source_instances"):
        
        self._db = db
        self._pipelines_container_name = pipelines_container_name
        self._step_catalog_container_name = step_catalog_container_name
        self._service_catalog_container_name = service_catalog_container_name
        self._step_instances_container_name = step_instances_container_name
        self._service_instances_container_name = service_instances_container_name
        self._source_catalog_container_name = source_catalog_container_name
        self._source_instances_container_name = source_instances_container_name
        
        self._pipeline_factory = None
        self._pipeline_cache = {}
        
        logger.info(f"PipelineManager initialized with pipelines_container: {pipelines_container_name}, step_catalog_container: {step_catalog_container_name}, service_catalog_container: {service_catalog_container_name}")

    async def __initialize_factory(self):
        if not self._pipeline_factory:
            
            # Load step and service catalogs
            step_catalog_config = await self._load_step_catalog_from_db()
            service_catalog_config = await self._load_service_catalog_from_db()
            source_catalog_config = await self._load_source_catalog_from_db()
            
            from doc.proc.pipeline.pipeline_factory import PipelineFactory
            self._pipeline_factory = PipelineFactory(step_catalog_config=step_catalog_config,
                                                     service_catalog_config=service_catalog_config,
                                                     source_catalog_config=source_catalog_config)


    async def load_pipeline(self, pipeline_name: str) -> Optional[Pipeline]:
        """Load a pipeline by name"""
        if pipeline_name in self._pipeline_cache:
            return self._pipeline_cache[pipeline_name]
        
        await self.__initialize_factory()
        
        # Load step, service and source instances
        service_instances = await self._load_service_instances_from_db()
        step_instances = await self._load_step_instances_from_db(service_instances=service_instances)
        source_instances = await self._load_source_instances_from_db()
        
        # Create pipeline config
        pipeline_config = await self._load_pipeline_config(pipeline_name, step_instances, service_instances, source_instances)
        
        if pipeline_config:
            pipeline = await self._pipeline_factory.create_pipeline(pipeline_config=pipeline_config)
            # Cache the pipeline
            self._pipeline_cache[pipeline_name] = pipeline
            return pipeline

        return None

    
    async def _get_pipeline_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a pipeline instance by name from Cosmos DB"""
        query = "SELECT * FROM c WHERE c.name = @name"
        parameters = [{"name": "@name", "value": name}]
        results = self._db.list(container=self._pipelines_container_name, query=query, parameters=parameters)
        return results[0] if results else None


    async def _load_pipeline_config(self, pipeline_name:str, step_instances:List[StepInstanceConfig], service_instances:List[ServiceInstanceConfig], source_instances:List[SourceInstanceConfig]) -> PipelineConfig:
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
        _steps_ids = pipeline_definitions[0].get("steps", [])
        _execution_sequence = pipeline_definitions[0].get("execution_sequence", [])
        if not _name or not _settings:
            raise ValueError(f"Pipeline definition is missing required fields: name or settings.")

        _pipeline_name = _name
        _pipeline_description = _description
        _pipeline_version = _version
        _pipeline_settings = PipelineSettingsConfig(**_settings)

        # find step instances for this pipeline from the provided step_instances list
        # - filter step_instances where instance.id is in _steps
        _pipeline_step_instances = [instance for instance in step_instances if instance.id in _steps_ids]
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
                                         source_instances=source_instances)


        return pipeline_config

    async def _load_step_instances_from_db(self, service_instances: List[ServiceInstanceConfig]) -> List[StepInstanceConfig]:
        """Load step instances from Cosmos DB"""
        query = "SELECT * FROM c"
        step_instances = self._db.list(container=self._step_instances_container_name, query=query)
        
        # Extract service instance names from step instances
        service_instances_dict = {instance.id: instance for instance in service_instances}
        for item in step_instances:
            if "services" in item and item["services"] and isinstance(item["services"], list):
                linked_services = []
                for service_id in item["services"]:
                    if service_id in service_instances_dict:
                        linked_services.append(service_instances_dict[service_id].name)
                    else:
                        raise ValueError(f"Service instance with id '{service_id}' referenced in step instance '{item.get('name', '')}' not found in provided service instances.")
                    
                item["services"] = linked_services
        return [StepInstanceConfig(**item) for item in step_instances]
    
    async def _load_step_catalog_from_db(self) -> List[StepConfig]:
        """Load step catalog from Cosmos DB"""
        query = "SELECT * FROM c"
        step_definitions = self._db.list(container=self._step_catalog_container_name, query=query)
        return [StepConfig.from_dict(step) for step in step_definitions]
    
    async def _load_service_instances_from_db(self) -> List[ServiceInstanceConfig]:
        """Load service instances from Cosmos DB"""
        query = "SELECT * FROM c"
        results = self._db.list(container=self._service_instances_container_name, query=query)
        return [ServiceInstanceConfig(**item) for item in results]
    
    async def _load_service_catalog_from_db(self) -> List[ServiceConfig]:
        """Load service catalog from Cosmos DB"""
        query = "SELECT * FROM c"
        service_definitions = self._db.list(container=self._service_catalog_container_name, query=query)
        return [ServiceConfig.from_dict(service) for service in service_definitions]
    
    async def _load_source_instances_from_db(self) -> List[SourceInstanceConfig]:
        """Load source instances from Cosmos DB"""
        query = "SELECT * FROM c"
        results = self._db.list(container=self._source_instances_container_name, query=query)
        return [SourceInstanceConfig(**item) for item in results]
    
    async def _load_source_catalog_from_db(self) -> List[SourceConfig]:
        """Load source catalog from Cosmos DB"""
        query = "SELECT * FROM c"
        source_definitions = self._db.list(container=self._source_catalog_container_name, query=query)
        return [SourceConfig.from_dict(source) for source in source_definitions]
    