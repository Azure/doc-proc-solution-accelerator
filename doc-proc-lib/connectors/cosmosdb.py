import logging

from typing import Dict
from configuration import Configuration

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from tenacity import retry, wait_random_exponential, stop_after_attempt, RetryError
from dependencies import get_config

MAX_RETRIES = 10  # Maximum number of retries for rate limit errors

config = get_config()

class CosmosDBClient:
    """
    CosmosDBClient uses the Cosmos SDK's retry mechanism with exponential backoff.
    The number of retries is controlled by the MAX_RETRIES environment variable.
    Delays between retries start at 0.5 seconds, doubling up to 8 seconds.
    If a rate limit error occurs after retries, the client will retry once more after the retry-after-ms header duration (if the header is present).
    """
    database = None
    client = None

    def __init__(self, settings: Dict = {}):
        """
        Initializes the Cosmos DB client with credentials and endpoint.
        """
        self.config = get_config()
        
        # Get Azure Cosmos DB configuration
        self.db_id = settings.get("DATABASE_ACCOUNT_NAME")
        self.db_name = settings.get("DATABASE_NAME")
        self.db_uri = f"https://{self.db_id}.documents.azure.com:443/"
        self.init_containers = settings.get("INIT_CONTAINERS", [])
        
        from azure.cosmos import CosmosClient
        self.db_client = CosmosClient(self.db_uri, credential=self.config.credential)
        self.database = self.db_client.get_database_client(database=self.db_name)

        #self._ensure_database(self.db_name)

        self.containers = {
            container: self._ensure_container(container) for container in (self.init_containers or [])
        }

    def _ensure_database(self, db_name: str):
        try:
            return self.db_client.create_database_if_not_exists(id=db_name)
        except exceptions.CosmosResourceExistsError:
            return self.db_client.get_database_client(db_name)
        
    def _ensure_container(self, container_name: str, path : str = "/id"):
        try:
            return self.database.create_container_if_not_exists(id=container_name, partition_key=PartitionKey(path=path))
        except exceptions.CosmosResourceExistsError:
            return self.database.get_container_client(container_name)

    @retry(
        stop=stop_after_attempt(5)
    )
    def _init_clients(self):
        from azure.cosmos import CosmosClient
        self.db_client = CosmosClient(self.db_uri, credential=self.config.credential)
        self.db = self.db_client.get_database_client(database=self.db_name)

# 'conversations'
# self.conversation_id
#     conversation
#     logging.info(f"[base_orchestrator] customer sent an inexistent conversation_id, saving new conversation_id")        
#     conversation = await container.create_item(body={"id": self.conversation_id})
# self.conversation_data = self.conversation.get('conversation_data', 
#                             {'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'interactions': []})
# self.history = self.conversation_data.get('history', [])

    async def list_documents(self, container_name) -> list:
        """
        Lists all documents from the given container.
        """
        
        container = self.database.get_container_client(container_name)

        # Correct usage without the outdated argument
        query = "SELECT * FROM c"
        items_iterable = container.query_items(query=query, partition_key=None)

        documents = []
        async for item in items_iterable:
            documents.append(item)

        return documents


    def get_document(self, container, key) -> dict: 
        logging.info(f"[cosmosdb] retrieving document {key} from container {container}")
        container = self.database.get_container_client(container)
        try:
            document = container.read_item(item=key, partition_key=key)
            logging.info(f"[cosmosdb] document {key} retrieved.")
        except Exception as e:
            document = None
            logging.info(f"[cosmosdb] document {key} does not exist.")
        return document

    def create_document(self, container, key, body=None) -> dict: 
        container = self.database.get_container_client(container)
        try:
            if body is None:
                body = {"id": key}
            else:
                body["id"] = key  # ensure the document id is set
            document = container.create_item(body=body)                    
            logging.info(f"[cosmosdb] document {key} created.")
        except Exception as e:
            document = None
            logging.info(f"[cosmosdb] error creating document {key}. Error: {e}")
        return document
            
    async def update_document(self, container, document) -> dict: 
        container = self.database.get_container_client(container)
        try:
            document = container.replace_item(item=document["id"], body=document)
            logging.info(f"[cosmosdb] document updated.")
        except Exception as e:
            document = None
            logging.warning(f"[cosmosdb] could not update document: {e}", exc_info=True)
        return document

    async def upsert_document(self, container, document) -> dict: 
        container = self.database.get_container_client(container)
        try:
            document = container.upsert_item(body=document)
            logging.info(f"[cosmosdb] document upserted.")
        except Exception as e:
            document = None
            logging.warning(f"[cosmosdb] could not upsert document: {e}", exc_info=True)
        return document
        
class AsyncCosmosDBClient:
    """
    CosmosDBClient uses the Cosmos SDK's retry mechanism with exponential backoff.
    The number of retries is controlled by the MAX_RETRIES environment variable.
    Delays between retries start at 0.5 seconds, doubling up to 8 seconds.
    If a rate limit error occurs after retries, the client will retry once more after the retry-after-ms header duration (if the header is present).
    """

    def __init__(self, config:Configuration=None):
        """
        Initializes the Cosmos DB client with credentials and endpoint.
        """
        self.config = config or Configuration()

        # Get Azure Cosmos DB configuration
        self.db_id = self.config.get_value("DATABASE_ACCOUNT_NAME")
        self.db_name = self.config.get_value("DATABASE_NAME")
        self.db_uri = f"https://{self.db_id}.documents.azure.com:443/"
        
        from azure.cosmos.aio import CosmosClient
        self.db_client = CosmosClient(self.db_uri, credential=self.config.credential)
        self.db = self.db_client.get_database_client(database=self.db_name)

# 'conversations'
# self.conversation_id
#     conversation
#     logging.info(f"[base_orchestrator] customer sent an inexistent conversation_id, saving new conversation_id")        
#     conversation = await container.create_item(body={"id": self.conversation_id})
# self.conversation_data = self.conversation.get('conversation_data', 
#                             {'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'interactions': []})
# self.history = self.conversation_data.get('history', [])

    async def list_documents(self, container_name) -> list:
        """
        Lists all documents from the given container.
        """
    
        db = self.db_client.get_database_client(database=self.db_name)
        container = db.get_container_client(container_name)

        # Correct usage without the outdated argument
        query = "SELECT * FROM c"
        items_iterable = container.query_items(query=query, partition_key=None)

        documents = []
        async for item in items_iterable:
            documents.append(item)

        return documents


    async def get_document(self, container, key) -> dict: 
        db = self.db_client.get_database_client(database=self.db_name)
        container = db.get_container_client(container)
        try:
            document = await container.read_item(item=key, partition_key=key)
            logging.info(f"[cosmosdb] document {key} retrieved.")
        except Exception as e:
            document = None
            logging.info(f"[cosmosdb] document {key} does not exist.")
        return document

    async def create_document(self, container, key, body=None) -> dict: 
    
        db = self.db_client.get_database_client(database=self.db_name)
        container = db.get_container_client(container)
        try:
            if body is None:
                body = {"id": key}
            else:
                body["id"] = key  # ensure the document id is set
            document = await container.create_item(body=body)                    
            logging.info(f"[cosmosdb] document {key} created.")
        except Exception as e:
            document = None
            logging.info(f"[cosmosdb] error creating document {key}. Error: {e}")
        return document
            
    async def update_document(self, container, document) -> dict: 
        db = self.db_client.get_database_client(database=self.db_name)
        container = db.get_container_client(container)
        try:
            document = await container.replace_item(item=document["id"], body=document)
            logging.info(f"[cosmosdb] document updated.")
        except Exception as e:
            document = None
            logging.warning(f"[cosmosdb] could not update document: {e}", exc_info=True)
        return document
    
    async def upsert_document(self, container, document) -> dict: 
        db = self.db_client.get_database_client(database=self.db_name)
        container = db.get_container_client(container)
        try:
            document = await container.upsert_item(body=document)
            logging.info(f"[cosmosdb] document upserted.")
        except Exception as e:
            document = None
            logging.warning(f"[cosmosdb] could not update document: {e}", exc_info=True)
        return document
    