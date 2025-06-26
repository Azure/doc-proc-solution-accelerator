from typing import List

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepInputOutput


class DocumentLoaderStep(StepBase):
    
    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, settings=settings, **kwargs)


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your document loading logic here

        # For demonstration, let's assume we load text from a document
        document_path = input_data.data.get("file")
        if not document_path:
            # If no document path is provided, we can return an empty StepInputOutput or raise an error
            return StepInputOutput(summary_data={**input_data.summary_data}, data={**input_data.data})
        
        # Here you would typically read the document file
        # For this example, we'll just simulate loading text from a document
        loaded_text = "This is the loaded text from the document."  # Simulated loaded text

        # Return the updated StepInputOutput
        return StepInputOutput(summary_data={**input_data.summary_data, "loaded_text": loaded_text}, 
                               data={**input_data.data, "loaded_text": loaded_text})