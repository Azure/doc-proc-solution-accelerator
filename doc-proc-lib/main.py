import asyncio
from typing import List
from colorama import Fore, Style, init
from dotenv import load_dotenv
import logging

from doc.proc.pipeline.pipeline_factory import create_pipeline_from_files


init(autoreset=True)

load_dotenv()

logger = logging.getLogger("doc.proc")

def setup_logging(logger: logging.Logger):
    """Setup logging configuration."""
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    class ColorFormatter(logging.Formatter):
        COLORS = {
            logging.DEBUG: Fore.CYAN,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.RED + Style.BRIGHT,
        }
        def format(self, record):
            color = self.COLORS.get(record.levelno, "")
            message = super().format(record)
            return f"{color}{message}{Style.RESET_ALL}"

    formatter = ColorFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)


#####
##### Main function to load and execute the pipeline
#####
async def main():

    # Load services catalog configuration
    services_catalog_yaml_file = 'service_catalog.yaml'
    step_catalog_yaml_file = 'step_catalog.yaml'
    pipeline_config_yaml_file = 'pipeline_config.yaml'

    # Load the pipeline
    try:
        pipeline = await create_pipeline_from_files(pipeline_name='pipeline_1',
                                                    pipeline_config_path=pipeline_config_yaml_file,
                                                    step_catalog_path=step_catalog_yaml_file,
                                                    service_catalog_path=services_catalog_yaml_file)
        #TODO: complete the pipeline execution
        
        # # Run the pipeline
        # input_data = Document(summary_data={}, data={ "documents": generate_documents() })
        
        # result = await pipeline.run(input_data=input_data)
        
        # logger.info(f"Pipeline '{pipeline.name}' executed successfully.")
        # logger.info(f"Pipeline result: {result}")

        # with open(f"pipeline_result.json", 'w') as f:
        #     f.write(result.model_dump_json())

    except Exception as e:
        logger.error(f"Error executing pipeline: {e}.")
        logger.error("Pipeline execution failed. Please check the logs for more details.")

      
def generate_documents():
    """Generate a list of documents to process."""
    # This is a placeholder function. In a real application, this would fetch documents from a source.
    return [
            Document(id="doc_1", 
                     file_path="/Users/nadeemis/temp/Lorem Ipsum Sample Document.pdf"
                     ),
            Document(id="doc_2", 
                     file_path="/Users/nadeemis/temp/Lorem Ipsum Presentation.pptx"
                     ),
            Document(id="doc_3", 
                     blob_details={"container": "documents", "blob": "Lorem Ipsum Sample Document.docx"}
                    )
        ]


if __name__ == "__main__":
    
    try:
        setup_logging(logger)
        asyncio.run(main())

    except ValueError as e:
        logger.error(f"Error: {e}. Please check your configuration.")