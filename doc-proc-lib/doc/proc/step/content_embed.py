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
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState
from doc.proc.models.content_identifier import ContentIdentifier

logger = logging.getLogger("doc.proc.step.content_embed") # need to specify the logger name as this module is loaded dynamically

class ContentEmbedStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState, **kwargs) -> StepInputOutput:

        # Get the source
        document = input_data.data.get("documents", [])[0]
        
        chunks = document.get("chunks")

        if not chunks:
            logger.error(f"No chunks found for: {document['content_uri']}.")
            raise StepExecutionError(message=f"No chunks found for: {document['content_uri']}.", cancel_request=True)

        #embed content
        for chunk in chunks:
            chunk["content"] = chunk.get("text", "")
            chunk["contentVector"] = await self.embed_content(context, chunk["text"])

        return input_data
    
    async def embed_content(self, context, content: str) -> List[float]:
        embed_service = self.get_service(context, self.settings['ai_model_embed_service'], None)
        return embed_service.run_embeddings(content)