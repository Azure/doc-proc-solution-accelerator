import base64
import hashlib
import os
import re
import logging
import json
import spacy

from typing import List, Dict, Set

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.docproc_state import DocProcState

logger = logging.getLogger("doc.proc.step.content_chunker") # need to specify the logger name as this module is loaded dynamically

class ContentChunkerStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.nlp = spacy.load('en_core_web_sm')

    async def run(self, input_data: dict, context: "PipelineExecutionContext", request: DocProcRequest, state: DocProcState) -> Dict:
        """
        Process a single document to extract content.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: Dictionary with processing statistics.
        """

        # Get the source
        document = input_data.data.get("documents", [])[0]

        content = document.get("content","")

        doc = self.nlp(content)
        sentences = list(doc.sents)
        chunks = []
        chunk_id = 0

        for sentence in sentences:
            chunk_data = {
                    'chunk_id': len(chunks),
                    'chunk_type': 'page',
                    'chunk_num': len(chunks),
                    'text': sentence,
                    'length' : len(sentence),
                    'size' : len(sentence),
                    'raw_text': sentence
                }
                
            chunks.append(chunk_data)

        document['chunks'] = chunks
            
        return input_data