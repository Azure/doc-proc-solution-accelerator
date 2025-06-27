from typing import List

from doc.proc.pipeline.pipeline_base import PipelineExecutionContext
from doc.proc.step.step_base import StepBase, StepInputOutput


import pymupdf

class PDFPagesToPNGStep(StepBase):

    def __init__(self, id: str, name: str, enabled: bool, description: str = None, tags: List[str] = None, settings: dict = None, **kwargs):
        super().__init__(id=id, name=name, enabled=enabled, description=description, tags=tags, settings=settings, **kwargs)


    async def run(self, input_data: StepInputOutput, context: "PipelineExecutionContext", **kwargs) -> StepInputOutput:
        # Implement your PDF to PNG conversion logic here
        pdf_file_path = input_data.data.get("input_pdf_file")
        if not pdf_file_path:
            # do nothing
            return StepInputOutput(summary_data=input_data.summary_data, data=input_data.data)
        
        png_output_folder = self.settings.get("png_output_folder", "output_pngs")
        # Create output folder if it doesn't exist
        import os
        os.makedirs(png_output_folder, exist_ok=True)

        pages_to_convert = self.settings.get("num_pages", -1)  # -1 means all pages
        
        doc = pymupdf.open(pdf_file_path)

        if pages_to_convert == -1 or pages_to_convert > len(doc):
            pages_to_convert = len(doc)

        # Prepare a list to store the paths of the saved PNG files
        pages_data = []

        # Iterate through pages and save as PNG
        for page_num in range(0, pages_to_convert):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            pix.save(f'{png_output_folder}/page_{page_num+1}.png')
            pages_data.append({'page_num': page_num+1, 'png': f'{png_output_folder}/page_{page_num+1}.png'})

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