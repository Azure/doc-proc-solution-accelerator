import logging
from typing import List

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase
from doc.proc.step.step_config import StepInstanceConfig
from doc.proc.models import StepExecutionError, Document


logger = logging.getLogger("doc.proc.step.sample_step")

#TODO: fix this
class SampleStep(StepBase):

    def __init__(self, instance_config: StepInstanceConfig, **kwargs):
        super().__init__(instance_config=instance_config, **kwargs)


    async def run(self, input_data: Document, context: "PipelineExecutionContext", **kwargs) -> Document:
        # Implement your document step logic here
        logger.debug(f"Running SampleStep: {self.name} with input data: {input_data}")
        
        _stats = {
            "total_documents": 0,
            "successful_documents": 0,
            "failed_documents": 0,
        }

        documents = input_data.data.get("documents", [])
        if not documents or not isinstance(documents, list):
            logger.warning("No documents found in input data.")
            return Document(summary_data={f"{self.name}_stats": _stats}, data={"documents": []})
        
        _stats["total_documents"] = len(documents)
        
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

                _stats["successful_documents"] += 1
                logger.info(f"Successfully processed document: {document}")

            except Exception as e:
                logger.error(f"Error processing document {document}: {e}")
                _stats["failed_documents"] += 1

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
