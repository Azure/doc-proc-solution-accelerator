import logging

from azure.core.exceptions import AzureError
from typing import Dict, Optional, Any, List

from tenacity import retry, wait_random_exponential, stop_after_attempt, RetryError

from doc.proc.service.service_base import ServiceBase, ServiceExecutionError
from dependencies import get_config

from sqlalchemy.orm import Session
from sqlalchemy import String, column, select, text, Index, Text, create_engine, event, Integer, Float, Column
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from connectors.postgres import PostgresClient

from pgvector.sqlalchemy import Vector
from psycopg2.extensions import register_adapter, AsIs

logger = logging.getLogger("doc.proc.service.postgres_service") # need to specify the logger name as this module is loaded dynamically

config = get_config()
class PostgresService(ServiceBase):
    """PostgreSQL service for managing database operations."""

    def __init__(self, name: str, type: str, settings:dict, **kwargs):
        super().__init__(name=name, type=type, settings=settings, **kwargs)

        settings = self._parse_settings(settings)
        self.host = self._parse_env(settings.get('host'))
        self.username = self._parse_env(settings.get('username'))
        self.password = self._parse_env(settings.get('password'))
        self.sslmode = self._parse_env(settings.get('sslmode', 'require'))
        self.credential_type = self._parse_env(settings.get('auth_type'))
        self.credential_key = ''
        self.database = self._parse_env(settings.get('database', 'graphrag'))
        self.table = self._parse_env(settings.get('table', 'vectors'))
        self.app_identity_name = self._parse_env(settings.get("app_identity_name", None))
        self.endpoint = f"https://{self.host}"
        self.initialize = self._parse_env(settings.get('initialize', False))
        self.engine = None

        # Validate database
        if self.database in ['', None]:
            raise ValueError("Settings key 'database' is required")

        logger.info(f"Initializing PostgresService with host: {self.host}, database: {self.database}, table: {self.table}, auth_type: {self.credential_type}")

        self.postgres_client = PostgresClient(**settings) 
        self.postgres_client.connect()

        logger.info(f"PostgresClient connected successfully.")
        
        if self.initialize:
            self.postgres_client.initialize(settings) 

        def adapt_dict(dict_var):
            return dict_var

        register_adapter(dict, adapt_dict)

        logger.info(f"PostgresService initialized successfully.")

    @retry(
        stop=stop_after_attempt(5)
    )
    async def get_auth_header_for_http_request(self):
        """Get the authentication header based on the credential type."""
        if self.credential_type == 'azure_key_credential':
            return {"api-key": self.api_key}
        elif self.credential_type == 'default_azure_credential':
            self._get_credentials()
            access_token = await self.aiocredential.get_token("https://ossrdbms-aad.database.windows.net/.default")
            return {"Authorization": f"Bearer {access_token.token}"}
        
        return {}

    async def test_connection(self) -> bool:
        """Test the connection to the Azure AI Search service."""
        try:
            self.postgres_client.connect()
            return True
        
        except Exception as e:
            logger.error(f"Failed to connect to Azure AI Search Service: {str(e)}")
            raise ServiceExecutionError(f"Failed to connect to Azure AI Search Service: {str(e)}")

    async def parse_document(self, document: dict) -> dict:
        """Parse and transform a document before indexing."""
        # Implement any necessary parsing or transformation logic here
        if 'id' not in document:
            raise ValueError("Document must have an 'id' field.")

        if 'parent_id' not in document:
            document['parent_id'] = str(document['parent_id'])
        
        if 'human_readable_id' not in document:
            document['human_readable_id'] = str(document['id'])

        if 'n_tokens' not in document:
            document['n_tokens'] = len(document['content'].split())

        if 'document_ids' not in document:
            document['document_ids'] = []

        if 'entity_ids' not in document:
            document['entity_ids'] = []

        if 'relationship_ids' not in document:
            document['relationship_ids'] = []

        if 'caption_vector' not in document:
            document['caption_vector'] = None

        return document
    
    def build_graph(self):
        #get all the entities and relationships from database
        sql = """
        select parent_id, entity_id, relationship_id
        from public.vectors
        """
        # Execute the SQL query and build the graph
        with Session(self.postgres_client.engine) as session:
            with session.connection() as conn:
                cur = conn.cursor()
                cur.execute(sql)
                rows = cur.fetchall()
                for row in rows:
                    # Process each row and build the graph
                    parent_id, entity_id, relationship_id = row
                    self.graph.add_edge(parent_id, entity_id, relationship_id=relationship_id)

    async def write_documents(self, database_name: str, documents: List[dict]) -> dict:
        """Write documents to the specified Postgres database."""
        if not documents:
            logger.warning("No documents to write to Postgres.")
            return

        try:
            with Session(self.postgres_client.engine) as session:
                
                insert_query = text("""
                        INSERT INTO public.{table_name} (id, parent_id, human_readable_id, chunk_id, content, n_tokens, length, document_ids, entity_ids, relationship_ids, content_vector)
                        VALUES (:id, :parent_id, :human_readable_id, :chunk_id, :content, :n_tokens, :length, :document_ids, :entity_ids, :relationship_ids, :content_vector)
                        ON CONFLICT (id) DO UPDATE SET
                            parent_id = EXCLUDED.parent_id,
                            human_readable_id = EXCLUDED.human_readable_id,
                            content = EXCLUDED.content,
                            n_tokens = EXCLUDED.n_tokens,
                            length = EXCLUDED.length,
                            document_ids = EXCLUDED.document_ids,
                            entity_ids = EXCLUDED.entity_ids,
                            relationship_ids = EXCLUDED.relationship_ids,
                            content_vector = EXCLUDED.content_vector
                    """.format(table_name=self.table))

                for document in documents:
                    try:
                        if not isinstance(document, dict):
                            logger.error(f"Invalid document format: {document}. Each document must be a dictionary.")
                            raise ValueError("Each document must be a dictionary.")

                        document = await self.parse_document(document)

                        item = session.query(RagItem).filter_by(id=document.get('id')).first()

                        if item:
                            # Update existing item
                            for key, value in document.items():
                                setattr(item, key, value)
                        else:
                            # Create new item
                            item = RagItem(**document)
                            session.add(item)

                        session.commit()
                    except Exception as e:
                        session.rollback()
                        logger.error(f"Error writing document ID {document.get('id', 'unknown')} to Postgres '{database_name}': {str(e)}")
                
                #self.insert_batch(conn, batch, self.database, insert_query)
                
        except Exception as e:
            logger.error(f"Error writing documents to Postgres '{database_name}': {str(e)}")
            raise ServiceExecutionError(f"Error writing documents to Postgres '{database_name}': {str(e)}")

    async def delete_documents(self, database_name: str, key_field: str, key_values: List[str]):
        """
        Deletes multiple documents from the specified Postgres database.

        Parameters:
            database_name (str): The name of the Postgres database.
            key_field (str): The name of the key field in the database.
            key_values (List[str]): A list of key values identifying the documents to delete.
        """
        if not key_values:
            logging.warning("[postgres] No key values provided for deletion.")
            return

        try:
            with Session(self.postgres_client.engine) as session:
                delete_query = text(f"DELETE FROM {database_name} WHERE {key_field} = :key_value")
                
                for key_value in key_values:
                    session.execute(delete_query, {"key_value": key_value})
                
                session.commit()
        except Exception as e:
            logging.error(f"[postgres] Unexpected error while deleting documents from '{database_name}': {e}")

    async def search_documents(
        self,
        database_name: str,
        search_text: str = "*",
        filter_field: Optional[str] = None,
        filter_value: Optional[Any] = None,
        filter_operator: str = "eq",
        select_fields: Optional[List[str]] = None,
        top: int = 10,
        skip: int = 0,
        order_by: Optional[str] = None,
        filter_str: Optional[str] = None  # <-- Add this
    ) -> Dict[str, Any]:
        client = await self.get_search_client(database_name)
        try:
            # Construct the filter string only if filter_str is not provided
            if filter_str is None and filter_field and filter_value is not None:
                if isinstance(filter_value, str):
                    escaped_value = filter_value.replace("'", "''")
                    filter_str = f"{filter_field} {filter_operator} '{escaped_value}'"
                else:
                    filter_str = f"{filter_field} {filter_operator} {filter_value}"

            search_kwargs = {
                "search_text": search_text,
                "filter": filter_str,
                "order_by": order_by,
                "search_mode": SearchMode.ALL,
                "skip": skip
            }

            if select_fields:
                search_kwargs["select"] = select_fields

            if top > 0:
                search_kwargs["top"] = top
            else:
                search_kwargs["top"] = 1000

            results = await client.search(**search_kwargs)
            documents = []
            async for result in results:
                documents.append(result)
                if top > 0 and len(documents) >= top:
                    break

            return {
                "count": len(documents),
                "documents": documents
            }

        except AzureError as e:
            logging.error(f"[postgres] AzureError while searching documents in '{database_name}': {e}")
            return {"count": 0, "documents": [], "error": str(e)}
        except Exception as e:
            logging.error(f"[postgres] Unexpected error while searching documents in '{database_name}': {e}")
            return {"count": 0, "documents": [], "error": str(e)}

    def delete_item(self, database_name, item):
        body = self.create_item_body(item)
        return self.call_search_api(self.search_service, self.api_version, f"indexes", f"{database_name}/docs/index", "delete", self.config.credential, body)

    def create_item(self, database_name, item):
        body = self.create_item_body(item)
        return self.call_search_api(self.search_service, self.api_version, f"indexes", f"{database_name}/docs/index", "post", self.config.credential, body)
    
# Define the models
class Base(DeclarativeBase):
    pass

class RagItem(Base):
    __tablename__ = "vectors"
    __table_args__ = {'extend_existing': True}
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    parent_id: Mapped[str] = mapped_column(Text, nullable=True)
    human_readable_id: Mapped[str] = mapped_column(Text, nullable=True)
    metadata_storage_path: Mapped[str] = mapped_column(Text, nullable=True)
    metadata_storage_name: Mapped[str] = mapped_column(Text, nullable=True)
    metadata_storage_last_modified: Mapped[str] = mapped_column(Text, nullable=True)
    metadata_security_id: Mapped[str] = mapped_column(Text, nullable=True)
    chunk_id: Mapped[int] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    image_captions: Mapped[str] = mapped_column(Text, nullable=True)
    page: Mapped[int] = mapped_column(Integer, nullable=True)
    offset: Mapped[float] = mapped_column(Float, nullable=True)
    length: Mapped[int] = mapped_column(Integer, nullable=True)
    n_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(Text, nullable=True)
    filepath: Mapped[str] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    related_items: Mapped[str] = mapped_column(Text, nullable=True)
    related_files: Mapped[str] = mapped_column(Text, nullable=True)
    data = Column(JSONB, nullable=True)
    document_ids = Column(JSONB, nullable=True)
    entity_ids = Column(JSONB, nullable=True)
    relationship_ids = Column(JSONB, nullable=True)
    content_vector: Mapped[Vector] = mapped_column(Vector(3072), nullable=True)
    caption_vector: Mapped[Vector] = mapped_column(Vector(3072), nullable=True)

    def to_dict(self, include_vectors: bool = False):
        """
        Converts the Item instance to a dictionary representation.
        """
        model_dict = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        if not include_vectors:
            model_dict.pop("content_vector", None)
            model_dict.pop("caption_vector", None)
        return model_dict

    def to_str_for_rag(self):
        """
        Converts Item to a string representation for Retrieval-Augmented Generation (RAG) usage.
        """
        # data_fields = " ".join([f"{key}:{value}" for key, value in self.data.items()])
        # return f"ID: {self.id} Data: {data_fields}"
        text = self.data.get("text", "")
        truncated_text = text[:800]  # Truncate to 800 characters

        # Include truncated data alongside other fields if necessary
        data_fields = [
            f"{key}:{value}"
            for key, value in self.data.items()
            if key != "text"  # Exclude the large 'text' field
        ]
        data_fields.append(f"text:{truncated_text}")

        page = self.data.get("page")
        data_str = " ".join(data_fields)
        return f"Rank: {page} Data: {data_str}"

    def to_str_for_embedding(self):
        """
        Converts Item to a string representation for embeddings.
        """
        return " ".join([f"{key}: {value}" for key, value in self.data.items() if key != "embedding"])


# Define HNSW index to support vector similarity search
# Use the vector_ip_ops access method (inner product) since these embeddings are normalized

# table_name = Item.__tablename__

# index_ada002 = Index(
#     "hnsw_index_for_innerproduct_{table_name}_embedding_ada002",
#     Item.embedding_ada002,
#     postgresql_using="hnsw",
#     postgresql_with={"m": 16, "ef_construction": 64},
#     postgresql_ops={"embedding_ada002": "vector_ip_ops"},
# )

# index_nomic = Index(
#     f"hnsw_index_for_innerproduct_{table_name}_embedding_nomic",
#     Item.embedding_nomic,
#     postgresql_using="hnsw",
#     postgresql_with={"m": 16, "ef_construction": 64},
#     postgresql_ops={"embedding_nomic": "vector_ip_ops"},
# )

table_name = RagItem.__tablename__