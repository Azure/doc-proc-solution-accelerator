import asyncio
from typing import List
from colorama import Fore, Style, init
from dotenv import load_dotenv
import logging

# from doc.proc.pipeline.pipeline_base import Pipeline
from doc.proc.pipeline.pipeline_config import PipelineConfig
# from doc.proc.step.step_base import StepInputOutput
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


async def load_services_catalog_config(services_catalog_yaml_file: str) -> ServiceConfig:

    # Example usage of ServiceConfig
    yaml_str = ''

    with open(services_catalog_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load services configuration
        service_catalog = ServiceConfig.from_yaml(yaml_str)
        logger.info(f"Service configuration loaded successfully.")
        logger.debug(f"Service configuration: {service_catalog}")
        
        return service_catalog
        
    except Exception as e:
        logger.error(f"Error loading service catalog: {e}")


async def load_step_catalog_config(step_catalog_yaml_file: str) -> StepConfig:

    # Example usage of ServiceConfig
    yaml_str = ''

    with open(step_catalog_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load steps configuration
        step_catalog = StepConfig.from_yaml(yaml_str)
        logger.info(f"Step configuration loaded successfully.")
        logger.debug(f"Step configuration: {step_catalog}")

        return step_catalog

    except Exception as e:
        logger.error(f"Error loading service catalog: {e}")


async def load_pipeline_config(pipeline_config_yaml_file: str, service_catalog: List[ServiceConfig] = None, step_catalog: List[StepConfig] = None) -> "PipelineConfig":
    """Load pipeline configuration from a YAML file."""
    
    yaml_str = ''

    with open(pipeline_config_yaml_file, 'r') as file:
        yaml_str = file.read()

    try:
        # Load pipeline configuration
        pipeline_config = PipelineConfig.from_yaml(yaml_str, services_catalog=service_catalog, step_catalog=step_catalog)
        logger.info(f"Pipeline configuration loaded successfully.")
        logger.debug(f"Pipeline configuration: {pipeline_config}")

        return pipeline_config

    except Exception as e:
        logger.error(f"Error loading pipeline configuration: {e}")


async def main():

    # Load services catalog configuration
    services_catalog_yaml_file = 'service_catalog.yaml'
    service_catalog_config = await load_services_catalog_config(services_catalog_yaml_file)


    # Load steps catalog configuration
    step_catalog_yaml_file = 'step_catalog.yaml'
    step_catalog_config = await load_step_catalog_config(step_catalog_yaml_file)


    # Load pipeline configuration
    pipeline_config_yaml_file = 'pipeline_config.yaml'
    pipeline_config = await load_pipeline_config(pipeline_config_yaml_file, service_catalog_config, step_catalog_config)

    # # Example usage of PipelineConfig
    # yaml_str = ''
    
    # with open('pipeline_config.yaml', 'r') as file:
    #     yaml_str = file.read()
    #
    # try:
    #     

    #     pipeline = await Pipeline.create(pipeline_config=pipeline_config, 
    #                                     services_config=service_config,
    #                                     steps_config=step_config)


    #     logger.info(f"Pipeline '{pipeline.name}' loaded successfully with {len(pipeline.pipeline_execution_steps)} execution steps.")

    #     # Run the pipeline
    #     input_data = StepInputOutput(summary_data={}, data={ "input_pdf_file": "/Users/nadeemis/temp/Emirates Group Annual Report 2024-2025.pdf" })
    #     result = await pipeline.run(input_data=input_data)
    #     logger.info(f"Pipeline '{pipeline.name}' executed successfully.")
    #     logger.debug(f"Result: {result}")
        
    # except Exception as e:
    #     logger.error(f"Error executing pipeline: {e}.")
    #     logger.error("Pipeline execution failed. Please check the logs for more details.")


if __name__ == "__main__":
    
    try:
        setup_logging(logger)
        asyncio.run(main())

    except ValueError as e:
        logger.error(f"Error: {e}. Please check your configuration.")