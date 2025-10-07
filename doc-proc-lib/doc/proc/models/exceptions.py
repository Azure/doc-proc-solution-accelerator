"""Custom exceptions for the document processing library."""


class StepExecutionError(Exception):
    """
    Custom exception for errors during step execution.
    """
    pass


class ServiceExecutionError(Exception):
    """
    Custom exception for errors during service execution.
    """
    pass


class PipelineExecutionError(Exception):
    """Custom exception for errors during pipeline execution."""
    pass


class PipelineConfigError(Exception):
    """Custom exception for errors in pipeline configuration."""
    pass