from typing import List
import logging
import base64

from azure.ai.inference.models import (
        SystemMessage,
        UserMessage,
        TextContentItem,
        ImageContentItem,
        ImageUrl,
        ImageDetailLevel,
    )

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput

logger = logging.getLogger(__name__)

class PDFPagePNGToMarkdownStep(StepBase):

    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, services:List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, services=services, settings=settings, **kwargs)

        # Initialize settings with default values if not provided
        if not self.settings:
            self.settings = {}


        # get prompts from settings
        self.prompts = self.settings.get("prompts", {})
        if not self.prompts:
            logger.error("No prompts found in settings.")
            raise StepExecutionError("No prompts found in settings.")

        self.system_prompt = self.prompts.get("system", "")
        if not self.system_prompt:
            logger.error("System prompt not found in settings.")
            raise StepExecutionError("System prompt not found in settings.")

        self.user_prompt = self.prompts.get("user", "")
        if not self.user_prompt:
            logger.error("User prompt not found in settings.")
            raise StepExecutionError("User prompt not found in settings.")

        self.max_completion_tokens = self.settings.get("max_completion_tokens", 4000)
        self.temperature = self.settings.get("temperature", 1.0)
        self.top_p = self.settings.get("top_p", 1.0)
        self.frequency_penalty = self.settings.get("frequency_penalty", 0.0)
        self.presence_penalty = self.settings.get("presence_penalty", 0.0)


    def convert_png_to_base64(self, png_path: str) -> str:
        """
        Convert a PNG file to a base64 encoded string.
        
        :param png_path: Path to the PNG file.
        :return: Base64 encoded string of the PNG file.
        """
        with open(png_path, "rb") as png_file:
            png_data = png_file.read()
            return base64.b64encode(png_data).decode('ascii')
        
    
    def get_ai_inference_service(self, context: "PipelineExecutionContext"):
        """
        Get the AI Model Inference Service from the context.
        
        :param context: PipelineExecutionContext instance.
        :return: AI Model Inference Service instance.
        """

        for name in self.services:
            cs = context.get_service(name)
            print(cs)
            if cs and cs.type == 'azure_ai_inference':
                return cs

        return None


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        
        # get Azure AI Model Inference Service from context
        ai_model_inference_service = self.get_ai_inference_service(context)
        if not ai_model_inference_service:
            logger.error("Azure AI Model Inference Service not found in context.")
            raise StepExecutionError("Azure AI Model Inference Service not found in context.")

        # get the path to the png files from input data
        pages_data = input_data.data.get("pages_data", [])
        if not pages_data:
            logger.error("No pages data found in input data. Cannot proceed with conversion.")
            #do nothing
            raise StepExecutionError("No pages data found in input data. Cannot proceed with conversion.")

        # Convert each PNG file to Markdown using the AI Model Inference Service
        for page_data in pages_data:
            
            if 'png' not in page_data:
                logger.error(f"PNG file path not found in page data: {page_data}. Skipping conversion.")
                continue

            # Call the AI Model Inference Service chat completion method with the PNG file

            # # convert the PNG to base64 string
            # png_base64 = self.convert_png_to_base64(page_data['png'])
            # if not png_base64:
            #     logger.error(f"Failed to convert PNG file {page_data['png']} to base64. Skipping conversion.")
            #     continue
            
            try:    
                # Prepare the chat completion request
                chat_completion_messages = [
                            SystemMessage(content=self.system_prompt),
                            UserMessage([
                                    TextContentItem(text=self.user_prompt),
                                    ImageContentItem(
                                        image_url=ImageUrl.load(
                                            image_file=page_data['png'],
                                            image_format="png",
                                            detail=ImageDetailLevel.HIGH,
                                        ),
                                    ),
                                ],)
                        ]
                

                response = ai_model_inference_service.run_chat_completion(messages=chat_completion_messages,
                                                                                        max_completion_tokens=self.max_completion_tokens,
                                                                                        temperature=self.temperature,
                                                                                        top_p=self.top_p,
                                                                                        frequency_penalty=self.frequency_penalty,
                                                                                        presence_penalty=self.presence_penalty)
                markdown = response.choices[0].message.content
                page_data['markdown'] = markdown

            except Exception as e:
                logger.error(f"Error converting PNG file {page_data['png']} to Markdown: {e}")
                raise StepExecutionError(f"Error converting PNG file {page_data['png']} to Markdown: {e}")


        # Return the updated StepInputOutput
        return StepInputOutput(summary_data=
                                            {
                                                **input_data.summary_data
                                            }, 
                               data=        
                                            {
                                                **input_data.data,
                                                "pages_data": pages_data
                                            })