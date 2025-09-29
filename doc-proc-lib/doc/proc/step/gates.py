import logging
import json

from typing import List, Dict, Set

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput, StepInstanceConfig
from doc.proc.models.docproc_request import DocProcRequest
from doc.proc.models.content_identifier import ContentIdentifier
from doc.proc.models.docproc_state import DocProcState

from azure.ai.inference.models import (
        SystemMessage,
        UserMessage
    )

logger = logging.getLogger("doc.proc.step.gates") # need to specify the logger name as this module is loaded dynamically

class GatesStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)
        
        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}

        self.system_prompt_name = self.settings.get("system_prompt_name", "gates_research_schema")
        if not self.system_prompt_name:
            logger.error("System prompt not found in settings.")
            raise StepExecutionError("System prompt not found in settings.")
        
        prompt_doc = self.cosmos.get_document('prompts', self.system_prompt_name)

        if not prompt_doc or 'system_prompt' not in prompt_doc:
            logger.error(f"System prompt '{self.system_prompt_name}' not found in CosmosDB.")
            raise StepExecutionError(f"System prompt '{self.system_prompt_name}' not found in CosmosDB.")

        self.system_prompt = prompt_doc['system_prompt']

        self.max_completion_tokens = self.settings.get("max_completion_tokens", 4000)
        self.temperature = self.settings.get("temperature", 1.0)
        self.top_p = self.settings.get("top_p", 1.0)
        self.frequency_penalty = self.settings.get("frequency_penalty", 0.0)
        self.presence_penalty = self.settings.get("presence_penalty", 0.0)

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

            ai_model_inference_service = self.get_ai_inference_service(context)

            chat_completion_messages = [
                    SystemMessage(content=self.system_prompt.replace("{content}", content)),
                ]
                        
            response = ai_model_inference_service.run_chat_completion(
                            messages=chat_completion_messages,
                            max_completion_tokens=self.max_completion_tokens,
                            temperature=self.temperature,
                            top_p=self.top_p,
                            frequency_penalty=self.frequency_penalty,
                            presence_penalty=self.presence_penalty
                        )
                        
            ai_response = response.choices[0].message.content

            jData = json.loads(ai_response.replace("```json", "").replace("```", "").strip())

            for key in jData:
                document['metadata'][key] = jData[key]

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

        document = input_data.data.get('document', {})
        
        if not document:
            document = await self.get_document(input_data.content_identifier, context)

        await self.process_document(document, context)
        return input_data
    
    def get_ai_inference_service(self, context: "PipelineExecutionContext"):
        """
        Get the AI Model Inference Service from the context.
        
        :param context: PipelineExecutionContext instance.
        :return: AI Model Inference Service instance.
        """

        for name in self.services:
            cs = context.get_service(name)
            if cs and cs.type == 'azure_ai_inference':
                return cs

        for service in context.services:
            instance = service['instance']
            if instance and instance.type == 'azure_ai_inference':
                return instance

        return None