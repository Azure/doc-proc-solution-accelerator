import logging
from typing import List, Dict, Set

from flair.data import Sentence
from flair.nn import Classifier

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.models.docproc_state import DocProcState

logger = logging.getLogger("doc.proc.step.flair") # need to specify the logger name as this module is loaded dynamically

class FlairStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.tagger = Classifier.load("hunflair2")

    async def get_document(self, content_identifier: ContentIdentifier, context: "PipelineExecutionContext") -> dict:
        """
        Retrieve a document by its content identifier.
        """
        document = await context.pipeline.get_document(content_identifier)
        return document
    
    async def process_document(self, document, context: "PipelineExecutionContext"):

        try:
            content = self._get_content(document)
            #content_metadata = await self._get_content_metadata(document)
            #content_metadata_security = await self._get_content_security(document)

            sentence = Sentence(content)
            self.tagger.predict(sentence)
            
            metadata = document.get("metadata", {})
            tags = []
            keys = []
            for entity in sentence.get_spans("ner"):    
                if entity.tag + entity.text in keys:
                    continue
                
                tags.append({
                    "title": entity.text,
                    "type": entity.tag,
                    "confidence": entity.score
                })
                
                keys.append(entity.tag+entity.text)

            metadata["entity_ids"] = tags

        except Exception as e:
            message = f"Error processing document {document['id']}: {e}"
            logger.error(message)
            raise StepExecutionError(message)

    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> Dict:
        """
        Process a single document to extract content.
        
        :param document: Document dictionary containing file path and other metadata.
        :param context: PipelineExecutionContext instance.
        :param ai_model_inference_service: AI Model Inference Service instance.
        :return: Dictionary with processing statistics.
        """

        #https://flairnlp.github.io/flair/master/tutorial/tutorial-hunflair2/overview.html
        document = input_data.data.get('document', {})
        
        if not document:
            document = await self.get_document(input_data.content_identifier, context)
        
        await self.process_document(document, context)

        return input_data