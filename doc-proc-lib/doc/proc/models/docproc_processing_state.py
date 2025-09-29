import enum

class DocProcProcessingState(enum.Enum):

    NEW = "new"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
