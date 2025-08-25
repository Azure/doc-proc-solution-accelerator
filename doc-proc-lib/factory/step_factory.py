from doc.proc.step.step_base import StepInstanceConfig, StepBase
from doc.proc.models.docproc_step import DocProcStep

class StepFactory():

    @staticmethod
    def create_step(step_data):

        step_instance_config = StepInstanceConfig(**step_data)

        # Create a step instance based on the provided step_data
        return StepBase(**step_instance_config)
    
    @staticmethod
    def create_step_from_DocProc_step(step_data : DocProcStep):

        step_instance = {
            "step_catalog_id": step_data.id,
            "name": step_data.id,
            "parameters": step_data.parameters
        }

        step_instance_config = StepInstanceConfig(**step_instance)

        # Create a step instance based on the provided step_data
        return StepBase(**step_instance_config)