import base64
import hashlib
import os
import re
import logging
import json
from typing import List, Dict, Set

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig

logger = logging.getLogger("doc.proc.step.content_chunker") # need to specify the logger name as this module is loaded dynamically

class ContentChunkerStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}


    async def run(self, input_data: dict, context: "PipelineExecutionContext") -> Dict:
        """
        Process a single document to extract content.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: Dictionary with processing statistics.
        """

        # Get the source
        documents = input_data.data.get("documents", [])

        for document in documents:
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
                
            # Process the content and metadata as needed
            # ...

            if content:
                document["content"] = content

            if content_metadata:
                document["metadata"] = content_metadata

        return input_data