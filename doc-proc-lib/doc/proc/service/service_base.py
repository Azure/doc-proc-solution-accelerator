from abc import abstractmethod


class ServiceExecutionError(Exception):
    """Custom exception for errors during service execution."""
    pass


class ServiceBase:
    """
    Base class for services.
    This class provides a method to get an instance of a service based on the provided settings.
    """

    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        self.name = name
        self.type = type
        self.settings = settings or {}
        self.params = kwargs

        if not self.name:
            raise ValueError("Service name cannot be empty")
        
        if not self.type:
            raise ValueError("Service type cannot be empty")
        

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the service connection.
        This method should be overridden by subclasses to implement specific service tests.
        """
        raise NotImplementedError("Subclasses must implement this method.")