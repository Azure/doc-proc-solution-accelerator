import base64
from datetime import datetime, timezone
import hashlib
import os
import re
import logging
import json
from typing import List, Dict, Set

from azure.ai.inference.models import (
        SystemMessage,
        UserMessage
    )

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.models.docproc_state import DocProcState
from doc.proc.models.docproc_artifact import DocProcArtifact, DocProcArtifactType

logger = logging.getLogger("doc.proc.step.content_extractor") # need to specify the logger name as this module is loaded dynamically

class ContentExtractorStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

    async def get_document(self, content_identifier: ContentIdentifier, context: "PipelineExecutionContext") -> dict:
        """
        Retrieve a document by its content identifier.
        """
        document = await context.pipeline.get_document(content_identifier)
        return document
    
    async def process_document(self, document, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState):

        try:
            source = document.get("source_name")

            if not source:
                logger.error(f"No source found in document: {document}.")
                raise StepExecutionError(f"No source found in document: {document}.")

            # Find the source by name by iterating
            source_instance = None
            for src in context.sources:
                if src["instance"].name == source:
                    source_instance = src["instance"]
                    break

            if not source_instance:
                logger.error(f"No source instance found for: {document['source_name']}.")
                raise StepExecutionError(f"No source instance found for: {document['source_name']}.")

            content = await source_instance.get_content(document["content_uri"])

            if not content:
                logger.error(f"No content found for: {document['content_uri']}.")
                raise StepExecutionError(f"No content found for: {document['content_uri']}.")

            content_metadata = await source_instance.get_content_metadata(document["content_uri"])

            if not content_metadata:
                logger.error(f"No content metadata found for: {document['content_uri']}.")

            content_metadata_security = await source_instance.get_content_security(document["content_uri"])

            if not content_metadata_security:
                logger.error(f"No content metadata security found for: {document['content_uri']}.")

            # Process the content and metadata as needed
            # ...

            if content:
                document["content"] = base64.b64encode(content)
                document["encoding"] = "base64"

            if content_metadata:
                document["metadata"] = content_metadata

            if content_metadata_security:
                document["metadata_security"] = content_metadata_security

            state.artifacts.append(DocProcArtifact(
                canonical_id=request.content_identifier.canonical_id,
                type=DocProcArtifactType.ExtractedText,
                position=1,
                data=base64.b64encode(content),
                size=len(content) if content else 0,
            ))

            state.artifacts.append(DocProcArtifact(
                canonical_id=request.content_identifier.canonical_id,
                type=DocProcArtifactType.ExtractedMetadata,
                position=1,
                data=json.dumps(content_metadata),
                size=len(content_metadata) if content_metadata else 0,
            ))

            state.artifacts.append(DocProcArtifact(
                canonical_id=request.content_identifier.canonical_id,
                type=DocProcArtifactType.ExtractedSecurity,
                position=1,
                data=json.dumps(content_metadata_security),
                size=len(content_metadata_security) if content_metadata_security else 0,
            ))

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

        document = await self.get_document(request.content_identifier, context)
        state.content_identifier.metadata = document
        await self.process_document(document, context, request, state)
        input_data.data['documents'] = [document]

        return input_data