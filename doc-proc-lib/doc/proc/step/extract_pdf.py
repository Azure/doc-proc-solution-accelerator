from typing import List

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepInputOutput


class PDFExtractorStep(StepBase):

    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, settings=settings, **kwargs)


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your PDF extraction logic here
        
        # For demonstration, let's assume we extract text from a PDF file
        pdf_file_path = input_data.data.get("input_pdf_file")
        if not pdf_file_path:
            # do nothing
            return StepInputOutput(summary_data=input_data.summary_data, data=input_data.data)
        
        # Here you would typically use a library like PyPDF2 or pdfminer to extract text from the PDF
        # For this example, we'll just simulate the extraction
        # Simulated extraction result
        extracted_text = "This is the extracted text from the PDF."

        # Return the updated StepInputOutput
        return StepInputOutput(summary_data={**input_data.summary_data, "extracted_text": extracted_text}, data={**input_data.data, "extracted_text": extracted_text})