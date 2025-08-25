from .source_base import SourceBase
from doc.proc.step.step_base import StepInstanceConfig, StepBase, StepInputOutput
from doc.proc.models.content_identifier import ContentIdentifier

class CosmosSource(SourceBase):
    """Data source for loading data from Azure Cosmos DB."""
    def __init__(self, id, name, type, settings: dict):
        super().__init__(id, name, type, settings)
        self.cosmos_client = self._initialize_cosmos_client()

    def _initialize_cosmos_client(self):
        """Initialize the Azure Cosmos DB client."""
        # Implement Azure Cosmos DB client initialization here
        pass

    async def get_document(self, content_identifier : ContentIdentifier):
        return await self.get_content(content_identifier.canonical_id)

    async def load_data(self) -> StepInputOutput:
        """Load data from Azure Cosmos DB."""
        # Implement data loading logic from Azure Cosmos DB here
        pass
