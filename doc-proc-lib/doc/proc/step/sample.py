import logging
from typing import List

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepInputOutput


logger = logging.getLogger("doc.proc.step.sample_step")

class SampleStep(StepBase):

    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, debug_mode: bool = False, services: List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, debug_mode=debug_mode, services=services, settings=settings, **kwargs)


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your document step logic here
        logger.info(f"Running SampleStep: {self.name} with input data: {input_data}")
        
        sample_summary = "This is a sample step that processes input data and returns updated output data."

        sample_data = {
            "sample_key": "sample_value",
            "sample_summary": "This is a sample summary",
            "sample_data": "This is sample data"
        }

        # Return the updated StepInputOutput
        return StepInputOutput(summary_data={**input_data.summary_data, **sample_summary}, 
                               data={**input_data.data, **sample_data})