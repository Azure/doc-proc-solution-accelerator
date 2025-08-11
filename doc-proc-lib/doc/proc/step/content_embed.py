import base64
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

logger = logging.getLogger("doc.proc.step.content_embed") # need to specify the logger name as this module is loaded dynamically

class ContentEmbedStep(StepBase):

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
            
            chunks = document.get("chunks")

            if not chunks:
                logger.error(f"No chunks found for: {document['content_uri']}.")
                raise StepExecutionError(f"No chunks found for: {document['content_uri']}.")

            #embed content
            for chunk in chunks:
                chunk["content"] = chunk.get("text", "")
                chunk["contentVector"] = await self.embed_content(context, chunk["text"])

        return input_data
    
    async def embed_content(self, context, content: str) -> List[float]:
        embed_service = self.get_service(context, self.settings['ai_model_embed_service'], None)
        return embed_service.run_embeddings(content)