from typing import List

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepInputOutput


class DocumentTransformerStep(StepBase):
    
    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, settings=settings, **kwargs)


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your document transformation logic here

        # For demonstration, let's assume we transform the text from a document
        document_text = input_data.data.get("extracted_text")
        if not document_text:
            # If no text is provided, we can return an empty StepInputOutput or raise an error
            return StepInputOutput(summary_data={**input_data.summary_data}, data={**input_data.data})

        # Here you would typically apply some transformation logic to the document text
        # For this example, we'll just simulate a transformation
        transformed_text = document_text.upper()  # Example transformation: convert text to uppercase

        return StepInputOutput(summary_data={**input_data.summary_data, "transformed_text": transformed_text}, 
                               data={**input_data.data, "transformed_text": transformed_text})