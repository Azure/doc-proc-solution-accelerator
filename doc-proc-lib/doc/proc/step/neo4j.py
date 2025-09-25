import logging
import networkx as nx
import pandas as pd
import numpy as np
import html
import re

from collections.abc import Mapping
from typing import List, Dict, Set, cast, Any

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.models.docproc_state import DocProcState

from neo4j import GraphDatabase, basic_auth

logger = logging.getLogger("doc.proc.step.neo4j") # need to specify the logger name as this module is loaded dynamically

log = logging.getLogger(__name__)

from dependencies import get_config
config = get_config()

from connectors.cosmosdb import CosmosDBClient
cosmos = CosmosDBClient(config)

class Neo4jStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        uri = self.settings.get("neo4j_uri", "bolt://localhost:7687")
        user = self.settings.get("neo4j_user", "neo4j")
        password = self.settings.get("neo4j_password", "Seattle123")

        self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
    
    async def get_document(self, content_identifier: ContentIdentifier, context: "PipelineExecutionContext") -> dict:
        """
        Retrieve a document by its content identifier.
        """
        document = await context.pipeline.get_document(content_identifier)
        return document
    
    async def process_document(self, document, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState):

        try:
            content = self._get_content(document)

            with self.driver.session() as session:
                #add all entities to neo4j
                if 'graphrag_entities' in document['metadata']:
                    for entity in document['metadata']['graphrag_entities']:
                        if 'title' in entity and 'type' in entity:
                            session.execute_write(
                                self.create_entity,
                                name=entity['title'],
                                type=entity['type'],
                                description=entity.get('description', ''),
                                source_id=entity.get('source_id', '')
                            )

                #add relationships to neo4j
                if 'graphrag_relationships' in document['metadata']:
                    for relation in document['metadata']['graphrag_relationships']:
                        if 'source' in relation and 'target' in relation:
                            session.execute_write(
                                self.create_relationship,
                                source=relation['source'],
                                target=relation['target'],
                                weight=relation.get('weight', 1.0),
                                description=relation.get('description', ''),
                                source_id=relation.get('source_id', ''),
                                relationship=relation.get('relationship', 'RELATED_TO')
                            )

        except Exception as e:
            message = f"Error processing document {document['id']}: {e}"
            logger.error(message)
            raise StepExecutionError(message)
    
    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState) -> Dict:
        """
        Process a single document to extract content.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: Dictionary with processing statistics.
        """

        document = input_data.data.get('documents', [])[0]
        if not document:
            document = await self.get_document(request.content_identifier, context)

        state.content_identifier.metadata = document
        await self.process_document(document, context, request, state)
        input_data.data['documents'] = [document]

        return input_data
    
    def clean_str(input: Any) -> str:
        """Clean an input string by removing HTML escapes, control characters, and other unwanted characters."""
        # If we get non-string input, just give it back
        if not isinstance(input, str):
            return input

        result = html.unescape(input.strip())
        # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
        return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)

    def _unpack_descriptions(data: Mapping) -> list[str]:
        value = data.get("description", None)
        return [] if value is None else value.split("\n")

    def _unpack_source_ids(data: Mapping) -> list[str]:
        value = data.get("source_id", None)
        return [] if value is None else value.split(", ")
    
    def create_entity(self, tx, name: str, type: str, description: str, source_id: str):
        tx.run(
            "MERGE (e:Entity {name: $name}) "
            "SET e.type = $type, e.description = $description, e.source_id = $source_id",
            name=name, type=type, description=description, source_id=source_id
        )

    def create_relationship(self, tx, source: str, target: str, weight: float, description: str, source_id: str, relationship: str="RELATED_TO"):
        tx.run(
            "MATCH (a:Entity {name: $source}), (b:Entity {name: $target}) "
            "MERGE (a)-[r:$relationship]->(b) "
            "SET r.weight = $weight, r.description = $description, r.source_id = $source_id",
            source=source, target=target, relationship=relationship, weight=weight, description=description, source_id=source_id
        )