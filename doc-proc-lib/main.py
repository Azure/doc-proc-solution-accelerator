import asyncio
from colorama import Fore, Style, init
from dotenv import load_dotenv
import logging

from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.pipeline.pipeline_config import PipelineConfig
from doc.proc.step.step_base import StepInputOutput
from doc.proc.step.step_config import StepConfig
from doc.proc.service.service_config import ServiceConfig

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

    formatter = ColorFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)


async def main():

    # Example usage of PipelineConfig
    yaml_str = ''
    
    with open('pipeline_config.yaml', 'r') as file:
        yaml_str = file.read()

    try:
        pipeline_config = PipelineConfig.from_yaml(yaml_str)[0]  # Assuming the first pipeline in the YAML is the one we want
        logger.info(f"Pipeline configuration loaded successfully.")
        logger.debug(f"Pipeline configuration: {pipeline_config}")

        # Load services configuration
        service_config = ServiceConfig.from_yaml(yaml_str)
        logger.info(f"Service configuration loaded successfully.")
        logger.debug(f"Service configuration: {service_config}")

        # Load steps configuration
        step_config = StepConfig.from_yaml(yaml_str)
        logger.info(f"Step configuration loaded successfully.")
        logger.debug(f"Step configuration: {step_config}")

        pipeline = await Pipeline.create(pipeline_config=pipeline_config, 
                                        services_config=service_config,
                                        steps_config=step_config)


        logger.info(f"Pipeline '{pipeline.name}' loaded successfully with {len(pipeline.pipeline_execution_steps)} execution steps.")

        # Run the pipeline
        input_data = StepInputOutput(summary_data={}, data={ "input_pdf_file": "/Users/nadeemis/temp/Emirates Group Annual Report 2024-2025.pdf" })
        result = await pipeline.run(input_data=input_data)
        logger.info(f"Pipeline '{pipeline.name}' executed successfully.")
        logger.debug(f"Result: {result}")
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {e}.")
        logger.error("Pipeline execution failed. Please check the logs for more details.")


if __name__ == "__main__":
    
    try:
        setup_logging(logger)
        asyncio.run(main())

    except ValueError as e:
        logger.error(f"Error: {e}. Please check your configuration.")