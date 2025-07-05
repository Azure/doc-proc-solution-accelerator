import logging
from typing import List

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepExecutionError, StepInputOutput


logger = logging.getLogger("doc.proc.step.sample_step")

class SampleStep(StepBase):

    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, fail_step_on_document_error: bool = False, debug_mode: bool = False, services: List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, fail_step_on_document_error=fail_step_on_document_error, debug_mode=debug_mode, services=services, settings=settings, **kwargs)


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your document step logic here
        logger.debug(f"Running SampleStep: {self.name} with input data: {input_data}")
        
        documents = input_data.data.get("documents", [])
        if not documents or not isinstance(documents, list):
            raise ValueError(f"No documents list found in input data.")

        _stats = {
            "total_documents": len(documents),
            "successful_sample_runs": 0,
            "failed_sample_runs": 0,
        }

        sample_data = {
            "sample_key": "sample_value",
            "sample_summary": "This is a sample summary",
            "sample_data": "This is sample data"
        }

        for document in documents:
            try:
                
                # Simulate processing the document
                logger.debug(f"Processing document: {document}")
                
                # Here you would implement your actual document processing logic
                # For example, extracting text, images, etc.
                
                document["sample_data"] = sample_data  # Add sample data to the document

                _stats["successful_sample_runs"] += 1
                logger.info(f"Successfully processed document: {document}")

            except Exception as e:
                logger.error(f"Error processing document {document}: {e}")
                _stats["failed_sample_runs"] += 1

                if self.fail_step_on_document_error:
                    # If the step is configured to fail on document error, raise an exception
                    raise StepExecutionError(f"Failed to process document {document}: {e}")

        # Return the updated StepInputOutput
        return StepInputOutput(summary_data=
                                    {
                                        **input_data.summary_data, f"{self.name}_stats": _stats
                                    }, 
                               data=
                                    {
                                        **input_data.data
                                    })
