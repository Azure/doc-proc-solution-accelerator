# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the CosmosDB vector store implementation."""
import os
import sys
import csv
import json
import logging
import psycopg2
import numpy as np
import openai
import azure.identity

from typing import Any, TypedDict, Dict

from azure.identity import DefaultAzureCredential

from sqlalchemy import event
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pgvector.sqlalchemy import Vector
from psycopg2.extensions import AsIs, register_adapter

from graphrag.data_model.types import TextEmbedder
from doc.proc.models.vector_store import (
    DEFAULT_VECTOR_SIZE,
    BaseVectorStore,
    VectorStoreDocument,
    VectorStoreSearchResult,
)

from openai import AsyncAzureOpenAI, AsyncOpenAI, AzureOpenAI, OpenAI
from dependencies import get_config
config = get_config()

logger = logging.getLogger("graphrag")
csv.field_size_limit(2147483647)  # Increase CSV field size limit for large text fields
BATCH_SIZE = 100

class ExtraArgs(TypedDict, total=False):
    dimensions: int

class PostgresClient(BaseVectorStore):
    """PostgreSQL vector storage implementation."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.host = kwargs.get("host")
        self.username = kwargs.get("username")
        self.database = kwargs.get("database")
        self.sslmode = kwargs.get("sslmode", "require")  # Default to 'require' SSL mode
        self.app_identity_name = kwargs.get("app_identity_name")
        self.password = kwargs.get("password")
        self.auth_type = kwargs.get("auth_type", "password")  # Default to password auth
        self.table = kwargs.get("table", "vectors")  # Default to vectors table

        # Ensure environment variables are set
        if not all([self.host, self.username, self.password, self.database]):
            raise ValueError("Missing required environment variables for database connection.")

        # Set SSL mode parameters
        self.sslmode_params = {}
        if self.sslmode.lower() in ["require", "verify-ca", "verify-full"]:
            self.sslmode_params["sslmode"] = self.sslmode

        self.properties = kwargs.get("properties", {})
        self.vector_size = self.properties.get("dimensions", DEFAULT_VECTOR_SIZE)

    def configure_age(self, engine, app_identity_name):
        with engine.connect() as conn:
            logger.info("AGE configuration...")

            # Execute the first query
            #logger.info("Initializing AGE extension...")
            #conn.execute(text("""SELECT * FROM initialize_age_extension();"""))
            #conn.commit()  # Commit after the first query

            # Execute the second query
            logger.info("Creating AGE extension if not exists...")
            conn.execute(text("""CREATE EXTENSION IF NOT EXISTS age CASCADE;"""))
            conn.commit()  # Commit after the second query

            # Execute the third query
            logger.info("Setting search_path...")
            conn.execute(text("""SET search_path = ag_catalog, "$user", public;"""))
            conn.commit()  # Commit after the third query

        logger.info("AGE configuration completed.")

    def connect(self, **kwargs: Any) -> Any:
        """Connect to PostgreSQL vector storage."""

        if self.auth_type == "azure_managed_identity":
            azure_credential = DefaultAzureCredential()
            self.password = self.get_password_from_azure_credential(azure_credential)

        self.conn = None
        try:
            # Connect to PostgreSQL using psycopg2
            self.conn = psycopg2.connect(
            host=self.host,
            user=self.username,
            password=self.password,
            dbname=self.database,
            **self.sslmode_params,
        )

        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
            
        self.vector_size = kwargs.get("vector_size", self.properties.get("dimensions", DEFAULT_VECTOR_SIZE))

        credential = None

        if self.auth_type == "azure_managed_identity":
            credential = DefaultAzureCredential()

        self.engine = self.create_postgres_engine(self.host, self.username, self.database, self.password, self.sslmode, credential)

    def initialize(self, **kwargs: Any) -> None:

        self.create_database(self.engine, **kwargs)
        self.create_tables(self.engine, **kwargs)

        # Configure AGE
        self.configure_age(self.engine, self.app_identity_name)

    def get_password_from_azure_credential(self,azure_credential):
        token = azure_credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
        return token.token
    
    def get_azure_credential(self):
        if self.auth_type == "azure_managed_identity":
            return DefaultAzureCredential()
        return None
    
    def create_postgres_engine(self, host, username, database, password, sslmode, azure_credential) -> Engine:

        token_based_password = False
        if azure_credential:
            token_based_password = True
            logger.info("Authenticating to Azure Database for PostgreSQL using Azure Identity...")
            password = self.get_password_from_azure_credential(azure_credential)
        else:
            logger.info("Authenticating to PostgreSQL using password...")

        DATABASE_URI = f"postgresql+psycopg2://{username}:{password}@{host}/{database}"
        # Specify SSL mode if needed
        if sslmode:
            DATABASE_URI += f"?sslmode={sslmode}"

        engine = create_engine(
            DATABASE_URI,
            echo=False,
        )

        @event.listens_for(engine.engine, "do_connect")
        def update_password_token(dialect, conn_rec, cargs, cparams):
            if token_based_password:
                logger.info("Updating password token for Azure Database for PostgreSQL")
                cparams["password"] = self.get_password_from_azure_credential(azure_credential)

        return engine

    def create_postgres_engine_from_args(self, args, azure_credential=None) -> Engine:
        if azure_credential is None and args.host.endswith(".database.azure.com"):
            azure_credential = DefaultAzureCredential()

        return self.create_postgres_engine(
            host=args.host,
            username=args.username,
            database=args.database,
            password=args.password,
            sslmode=args.sslmode,
            azure_credential=azure_credential,
        )

    def create_database(self, engine, **kwargs) -> None:
        with engine.begin() as conn:
            logger.info("Enabling azure_ai extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS azure_ai"))

            logger.info("Enabling the pgvector extension for Postgres...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            # Load environment variables for Azure OpenAI endpoint settings
            properties = kwargs.get("properties", {})

            if len( properties ) == 0:
                properties = {
                    "azure_ml_scoring_endpoint": config.get("AZURE_ML_SCORING_ENDPOINT",None, allow_none=True),
                    "azure_ml_endpoint_key": config.get("AZURE_ML_ENDPOINT_KEY",None, allow_none=True),
                    "azure_ml_deployment": config.get("AZURE_ML_DEPLOYMENT", "chat", allow_none=True),
                    "azure_openai_endpoint": config.get("AZURE_OPENAI_ENDPOINT",None, allow_none=True),
                    "azure_openai_endpoint_key": config.get("AZURE_OPENAI_ENDPOINT_KEY",None, allow_none=True),
                    "azure_openai_deployment": config.get("AZURE_OPENAI_DEPLOYMENT", "chat", allow_none=True),
                    "index_type": config.get("INDEX_TYPE", "diskann", allow_none=True),
                }

            scoring_endpoint = properties.get("azure_ml_scoring_endpoint")
            endpoint_key = properties.get("azure_ml_endpoint_key")
            deployment_name = properties.get("azure_ml_deployment", "chat")

            openai_endpoint = properties.get("azure_openai_endpoint")
            openai_endpoint_key = properties.get("azure_openai_endpoint_key")
            openai_deployment_name = properties.get("azure_openai_deployment", "chat")

            if not scoring_endpoint or not endpoint_key:
                logger.error(
                    "Azure OpenAI endpoint settings are missing. Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_ENDPOINT_KEY in the environment."
                )
                return

            logger.info("Setting Azure endpoint and API key...")
            if scoring_endpoint:
                conn.execute(text(f"SELECT azure_ai.set_setting('azure_ml.scoring_endpoint', '{scoring_endpoint}');"))

            if endpoint_key:
                conn.execute(text(f"SELECT azure_ai.set_setting('azure_ml.endpoint_key', '{endpoint_key}');"))

            if openai_endpoint:
                conn.execute(text(f"SELECT azure_ai.set_setting('azure_openai.endpoint', '{openai_endpoint}');"))
            
            if openai_endpoint_key:
                conn.execute(text(f"SELECT azure_ai.set_setting('azure_openai.subscription_key', '{openai_endpoint_key}');"))

            # Create the semantic_relevance function
            logger.info("Creating semantic_relevance function...")
            conn.execute(
                text("""
                CREATE OR REPLACE FUNCTION semantic_relevance(query TEXT, n INT)
                RETURNS jsonb AS $$
                DECLARE
                    json_pairs jsonb;
                    result_json jsonb;
                BEGIN
                    json_pairs := generate_json_pairs(query, n);
                    result_json := azure_ml.invoke(
                        json_pairs,
                        deployment_name => '{deployment_name}',
                        timeout_ms => 180000
                    );
                    RETURN (
                        SELECT result_json as result
                    );
                END $$ LANGUAGE plpgsql;
            """.format(deployment_name=deployment_name))
            )

            conn.execute(
                text("""
                    DROP TABLE IF EXISTS public.cases_updated;
            """)
            )
            logger.info("Creating database tables and indexes...")
            Base.metadata.create_all(bind=engine)

            # Enable the Apache AGE extension and load the library
            logger.info("Enabling the Apache AGE extension for Postgres...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS age;"))
            conn.execute(text('SET search_path = ag_catalog, "$user", public;'))

        conn.close()

    def delete_database(self, session: Session) -> None:
        """Delete the database if it exists."""
        if self.database_exists():
            self._postgres_client.delete_database(self.database)

    def database_exists(self) -> bool:
        """Check if the database exists."""
        existing_database_names = [
            database["id"] for database in self._postgres_client.list_databases()
        ]
        return self.database in existing_database_names
    
    def initialize_final_documents_table(self, engine: Engine):
        """
        Initialize and populate the `final_documents` table.
        """
        csv_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", "data/final_documents.csv"))
        query = text("""
            INSERT INTO final_documents (id, human_readable_id, title, text, text_unit_ids, attributes)
            VALUES (:id, :human_readable_id, :title, :text, :text_unit_ids, :attributes)
            ON CONFLICT (id) DO NOTHING
        """)

        def process_row(row):
            try:
                attributes = json.loads(row["attributes"].replace("'", '"'))
                text_unit_ids = row["text_unit_ids"].strip("[]").split(",")
                return {
                    "id": row["id"],
                    "human_readable_id": row["human_readable_id"],
                    "title": row["title"],
                    "text": row["text"],
                    "text_unit_ids": text_unit_ids,
                    "attributes": json.dumps(attributes),
                }
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in row {row}: {e}")
                return None

        with Session(engine) as session:
            self.create_table(
                session,
                "final_documents",
                """
                CREATE TABLE final_documents (
                    id TEXT PRIMARY KEY,
                    human_readable_id TEXT,
                    title TEXT,
                    text TEXT,
                    text_unit_ids TEXT[],
                    attributes JSONB
                );
            """,
            )
            self.initialize_table_from_csv(session, csv_file_path, "final_documents", query, process_row)


    def initialize_final_text_units_table(self, engine: Engine, import_data: bool = False):
        """
        Initialize and populate the `final_text_units` table.
        """
        query = text("""
            INSERT INTO final_text_units (id, human_readable_id, text, n_tokens, document_ids, entity_ids, relationship_ids, text_vector)
            VALUES (:id, :human_readable_id, :text, :n_tokens, :document_ids, :entity_ids, :relationship_ids, :text_vector)
            ON CONFLICT (id) DO NOTHING
        """)

        def process_row(row):
            try:
                document_ids = row["document_ids"].strip("[]").split(",")
                entity_ids = row["entity_ids"].strip("[]").split(",")
                relationship_ids = row["relationship_ids"].strip("[]").split(",")
                return {
                    "id": row["id"],
                    "human_readable_id": row["human_readable_id"],
                    "text": row["text"],
                    "n_tokens": int(row["n_tokens"]),
                    "document_ids": document_ids,
                    "entity_ids": entity_ids,
                    "relationship_ids": relationship_ids,
                    "text_vector": row["text_vector"],
                }
            except Exception as e:
                logger.error(f"Error processing row {row}: {e}")
                return None

        with Session(engine) as session:
            self.create_table(
                session,
                "final_text_units",
                """
                CREATE TABLE final_text_units (
                    id TEXT PRIMARY KEY,
                    human_readable_id TEXT,
                    text TEXT,
                    n_tokens INT,
                    document_ids TEXT[],
                    entity_ids TEXT[],
                    relationship_ids TEXT[],
                    text_vector vector({vector_size})
                );
            """.format(vector_size=self.vector_size),
            )

            if import_data:
                csv_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", "data/final_text_units.csv"))        
                self.initialize_table_from_csv(session, csv_file_path, "final_text_units", query, process_row)

    def initialize_final_communities_table(self, engine: Engine):
        """
        Initialize and populate the `final_communities` table.
        """
        csv_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..", "data/final_communities.csv"))
        table_name = "final_communities"
        schema = """
            CREATE TABLE final_communities (
                id TEXT PRIMARY KEY,
                human_readable_id TEXT,
                community INT,
                level INT,
                title TEXT,
                entity_ids TEXT[],
                relationship_ids TEXT[],
                text_unit_ids TEXT[],
                period TEXT,
                size INT
            );
        """
        query = text("""
            INSERT INTO final_communities (
                id, human_readable_id, community, level, title,
                entity_ids, relationship_ids, text_unit_ids, period, size
            )
            VALUES (
                :id, :human_readable_id, :community, :level, :title,
                :entity_ids, :relationship_ids, :text_unit_ids, :period, :size
            )
            ON CONFLICT (id) DO NOTHING
        """)

        def process_row(row):
            try:
                return {
                    "id": row["id"],
                    "human_readable_id": row["human_readable_id"],
                    "community": int(row["community"]),
                    "level": int(row["level"]),
                    "title": row["title"],
                    "entity_ids": row["entity_ids"].strip("[]").split(","),
                    "relationship_ids": row["relationship_ids"].strip("[]").split(","),
                    "text_unit_ids": row["text_unit_ids"].strip("[]").split(","),
                    "period": row["period"],
                    "size": int(row["size"]),
                }
            except Exception as e:
                logger.error(f"Error processing row {row}: {e}")
                return None

        with Session(engine) as session:
            self.create_table(session, table_name, schema)
            self.initialize_table_from_csv(session, csv_file_path, table_name, query, process_row)

    def initialize_final_community_reports_table(self, engine: Engine):
        """
        Initialize and populate the `final_community_reports` table.
        """
        csv_file_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../..", "data/final_community_reports.csv")
        )
        table_name = "final_community_reports"
        schema = """
            CREATE TABLE final_community_reports (
                id TEXT PRIMARY KEY,
                human_readable_id TEXT,
                community INT,
                level INT,
                title TEXT,
                summary TEXT,
                full_content TEXT,
                rank TEXT,
                rank_explanation TEXT,
                findings TEXT,
                full_content_json TEXT,
                period TEXT,
                size TEXT,
                full_content_vector vector({vector_size})
            );
        """.format(vector_size=self.vector_size)
        query = text("""
            INSERT INTO final_community_reports (
                id, human_readable_id, community, level, title, summary, full_content,
                rank, rank_explanation, findings, full_content_json, period, size, full_content_vector
            )
            VALUES (
                :id, :human_readable_id, :community, :level, :title, :summary, :full_content,
                :rank, :rank_explanation, :findings, :full_content_json, :period, :size, :full_content_vector
            )
            ON CONFLICT (id) DO NOTHING
        """)

        def process_row(row):
            try:
                return {
                    "id": row["id"],
                    "human_readable_id": row["human_readable_id"],
                    "community": int(row["community"]),
                    "level": int(row["level"]),
                    "title": row["title"],
                    "summary": row["summary"],
                    "full_content": row["full_content"],
                    "rank": row["rank"],
                    "rank_explanation": row["rank_explanation"],
                    "findings": row["findings"],
                    "full_content_json": row["full_content_json"],
                    "period": row["period"],
                    "size": row["size"],
                    "full_content_vector": row["full_content_vector"],
                }
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                logger.error(f"Error processing row {row['id'] if 'id' in row else 'unknown'}: {e}")
                return None

        with Session(engine) as session:
            self.create_table(session, table_name, schema)
            self.initialize_table_from_csv(session, csv_file_path, table_name, query, process_row)


    def generate_and_update_embeddings(self,engine: Engine):
        """
        Generate embeddings for `full_content` and update the `full_content_vector` column.
        """
        update_query = text("""
            UPDATE final_community_reports
            SET full_content_vector = :vector
            WHERE id = :id
        """)

        select_query = text("""
            SELECT id, full_content
            FROM final_community_reports
            WHERE full_content_vector IS NULL
        """)

        def addapt_vector(nparray):
            """Adapt a numpy array to the PostgreSQL VECTOR type."""
            vector_str = ",".join(map(str, nparray.tolist()))
            return AsIs(f"'[{vector_str}]'::VECTOR")

        def adapt_vector(nparray):
            """Adapt a numpy array to the PostgreSQL VECTOR type."""
            return f"[{','.join(map(str, nparray.tolist()))}]"

        register_adapter(np.ndarray, addapt_vector)

        with Session(engine) as session:
            with session.begin():
                print("Generating embeddings and updating the database...")
                result = session.execute(select_query)
                rows = result.fetchall()

                print(f"Found {len(rows)} rows to process.")

                for row in rows:
                    try:
                        # Generate embeddings for `full_content`
                        azure_credential = self.get_azure_credential()
                        openai_embed_client = self.create_openai_embed_client(azure_credential)

                        embedding = self.compute_text_embedding(
                            row[1],
                            openai_client=openai_embed_client,
                            embed_model="text-embedding-3-small",
                            embed_deployment="text-embedding-3-small",
                            embedding_dimensions=self.vector_size,
                        )

                        fcv = np.array(embedding)
                        if fcv is not None:
                            # Update the `full_content_vector` column
                            vector_str = adapt_vector(fcv)
                            session.execute(
                                update_query,
                                {"vector": vector_str, "id": row[0]},
                            )
                    except Exception as e:
                        logger.error(f"Error generating embeddings for row ID {row[0]}: {e}")
                session.commit()

    def generate_and_update_embeddings_ftu(self, engine: Engine):
        """
        Generate embeddings for `text` and update the `text_vector` column.
        """
        update_query = text("""
            UPDATE final_text_units
            SET text_vector = :vector
            WHERE id = :id
        """)

        select_query = text("""
            SELECT id, text
            FROM final_text_units
            WHERE text_vector IS NULL
        """)

        def addapt_vector(nparray):
            """Adapt a numpy array to the PostgreSQL VECTOR type."""
            vector_str = ",".join(map(str, nparray.tolist()))
            return AsIs(f"'[{vector_str}]'::VECTOR")

        def adapt_vector(nparray):
            """Adapt a numpy array to the PostgreSQL VECTOR type."""
            return f"[{','.join(map(str, nparray.tolist()))}]"

        register_adapter(np.ndarray, addapt_vector)

        with Session(engine) as session:
            with session.begin():
                print("Generating embeddings and updating the database...")
                result = session.execute(select_query)
                rows = result.fetchall()

                print(f"Found {len(rows)} rows to process.")

                for row in rows:
                    try:
                        # Generate embeddings for `full_content`
                        azure_credential = self.get_azure_credential()
                        openai_embed_client = self.create_openai_embed_client(azure_credential)

                        embedding = self.compute_text_embedding(
                            row[1],
                            openai_client=openai_embed_client,
                            embed_model="text-embedding-3-small",
                            embed_deployment="text-embedding-3-small",
                            embedding_dimensions=self.vector_size,
                        )

                        fcv = np.array(embedding)
                        if fcv is not None:
                            # Update the `text_vector` column
                            vector_str = adapt_vector(fcv)
                            session.execute(
                                update_query,
                                {"vector": vector_str, "id": row[0]},
                            )
                    except Exception as e:
                        logger.error(f"Error generating embeddings for row ID {row[0]}: {e}")
                session.commit()

    def create_diskann_index(self,engine: Engine):
        """
        Create the DISKANN index on the `full_content_vector` column.
        """
        with Session(engine) as session:
            with session.begin():

                logger.info("Enabling pg_diskann extension...")
                session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_diskann"))

                create_index_query = text("""
                    CREATE INDEX IF NOT EXISTS idx_diskann_content_vector ON final_community_reports
                    USING diskann (full_content_vector vector_cosine_ops);
                """)
                session.execute(create_index_query)
                session.commit()
                logger.info("DISKANN index on `full_content_vector` created successfully.")

    def create_hnsw_index(self,engine: Engine):
        """
        Create the HNSW index on the `full_content_vector` column.
        """
        with Session(engine) as session:
            with session.begin():
                create_index_query = text("""
                    CREATE INDEX IF NOT EXISTS idx_full_content_vector ON final_community_reports
                    USING hnsw (full_content_vector vector_cosine_ops);
                """)
                session.execute(create_index_query)
                session.commit()
                logger.info("HNSW index on `full_content_vector` created successfully.")


    def create_hnsw_index_ftu(self, engine: Engine):
        """
        Create the HNSW index on the `text_vector` column.
        """
        with Session(engine) as session:
            with session.begin():
                create_index_query = text("""
                    CREATE INDEX IF NOT EXISTS idx_text_vector ON final_text_units
                    USING hnsw (text_vector vector_cosine_ops);
                """)
                session.execute(create_index_query)
                session.commit()
                logger.info("HNSW index on `text_vector` created successfully.")

    def create_vector_table(self, engine: Engine ):
        """
        Create a table with a vector column.
        """
        with Session(engine) as session:
            self.create_table(
                        session,
                        self.table,
                        """
                        CREATE TABLE public.{table} (
                            id TEXT PRIMARY KEY,
                            human_readable_id TEXT,
                            text TEXT,
                            n_tokens INT,
                            document_ids TEXT[],
                            entity_ids TEXT[],
                            relationship_ids TEXT[],
                            text_vector vector({dimensions})
                        );
                    """.format(table=self.table,dimensions=self.vector_size),
                    )
    
    def create_tables(self, engine, **kwargs) -> None:

        self.initialize_final_documents_table(engine)
        self.initialize_final_text_units_table(engine)
        self.initialize_final_communities_table(engine)
        self.initialize_final_community_reports_table(engine)

        if kwargs.get("run_post_embedding") == "true":
            self.generate_and_update_embeddings(engine)
            self.generate_and_update_embeddings_ftu(engine)

        properties = kwargs.get("properties", {})
        index_type = properties.get("index_type", "diskann").lower()

        if index_type not in ["diskann", "hnsw"]:
            logger.warning(f"Unknown index_type '{index_type}'. Defaulting to 'diskann'.")
            index_type = "diskann"

        if index_type == "diskann":
            self.create_diskann_index(engine)
        elif index_type == "hnsw":
            self.create_hnsw_index(engine)
            self.create_hnsw_index_ftu(engine)

        engine.dispose()

    def insert_batch(self, session: Session, batch, table_name, query):
        """
        Insert a batch of rows into the specified table.
        """
        try:
            session.execute(query, batch)
            session.commit()
        except Exception as e:
            logger.error(f"Batch insert failed for table {table_name}: {e}")
            session.rollback()

    def initialize_table_from_csv(self, session: Session, csv_file_path, table_name, insert_query, process_row):
        """
        Generic function to initialize a table and populate it from a CSV file.
        """

        batch = []
        try:
            with open(csv_file_path, encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    processed_row = process_row(row)
                    if processed_row:
                        batch.append(processed_row)

                    # Insert batch into the database when the batch size is reached
                    if len(batch) >= BATCH_SIZE:
                        self.insert_batch(session, batch, table_name, insert_query)
                        batch = []  # Clear the batch after inserting

                # Insert any remaining rows in the last batch
                if batch:
                    self.insert_batch(session, batch, table_name, insert_query)

            logger.info(f"Data seeding completed successfully for table {table_name}.")
        except Exception as e:
            logger.error(f"Data seeding failed for table {table_name}: {e}")
            session.rollback()
    
    def create_table(self, session: Session, table_name, schema, drop_if_exists=True):
        """
        Create a table with the specified schema.
        """
        if drop_if_exists:
            self.delete_table(session, table_name)

        session.execute(text(schema))
        session.commit()
        logger.info(f"Table `{table_name}` created successfully.")

    def delete_table(self, session: Session, table_name):
        """
        Delete a table if it exists.
        """
        session.execute(text(f"DROP TABLE IF EXISTS \"{table_name}\";"))
        session.commit()
        logger.info(f"Table `{table_name}` deleted successfully.")

    def table_exists(self, session: Session, table_name: str) -> bool:
        """Check if the table exists."""
        result = session.execute(
            text(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table_name)"),
            {"table_name": table_name}
        )
        return result.scalar() != None

    def load_documents(
        self, documents: list[VectorStoreDocument], overwrite: bool = True
    ) -> None:
        """Load documents into PostgreSQL."""
        # Create a PostgreSQL table on overwrite
        with Session(self.engine) as session:
            if overwrite:
                self.delete_table(session, 'final_text_units')
                self.create_table(
                    session,
                    "final_text_units",
                    """
                    CREATE TABLE public.final_text_units (
                        id TEXT PRIMARY KEY,
                        human_readable_id TEXT,
                        text TEXT,
                        n_tokens INT,
                        document_ids TEXT[],
                        entity_ids TEXT[],
                        relationship_ids TEXT[],
                        text_vector vector({dimensions})
                    );
                """.format(dimensions=self.vector_size),
                )

            # Upload documents to PostgreSQL
            for doc in documents:
                if doc.vector is not None:
                    doc_json = {
                        "id": doc.id,
                        "human_readable_id": '', #doc.human_readable_id,
                        "text": doc.text,
                        "n_tokens": 0, #doc.n_tokens,
                        "document_ids": '{}', #doc.document_ids,
                        "entity_ids": '{}', #doc.entity_ids,
                        "relationship_ids": '{}', #doc.relationship_ids,
                        "text_vector": doc.vector,
                        #"attributes": json.dumps(doc.attributes),
                    }

                    query = text("""
                        INSERT INTO final_text_units (id, human_readable_id, text, n_tokens, document_ids, entity_ids, relationship_ids, text_vector)
                        VALUES (:id, :human_readable_id, :text, :n_tokens, :document_ids, :entity_ids, :relationship_ids, :text_vector)
                        ON CONFLICT (id) DO NOTHING
                    """)

                    session.execute(query, doc_json)
                    session.commit()

    async def create_openai_chat_client(self, azure_credential: azure.identity.AzureDeveloperCliCredential | azure.identity.ManagedIdentityCredential,
        **kwargs: Any,
    ) -> openai.AsyncAzureOpenAI | openai.AsyncOpenAI:
        openai_chat_client: openai.AsyncAzureOpenAI | openai.AsyncOpenAI
        OPENAI_CHAT_HOST = kwargs.get("OPENAI_CHAT_HOST")
        if OPENAI_CHAT_HOST == "azure":
            api_version = "2023-05-15"
            azure_endpoint = kwargs.get("AZURE_OPENAI_ENDPOINT", "")
            azure_deployment = kwargs.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "")
            if api_key := kwargs.get("AZURE_OPENAI_KEY"):
                logger.info(
                    "Setting up Azure OpenAI client for chat completions using API key, endpoint %s, deployment %s",
                    azure_endpoint,
                    azure_deployment,
                )
                openai_chat_client = openai.AsyncAzureOpenAI(
                    api_version=api_version,
                    azure_endpoint=azure_endpoint,
                    azure_deployment=azure_deployment,
                    api_key=api_key,
                )
            else:
                logger.info(
                    "Setting up Azure OpenAI client for chat completions using Azure Identity, endpoint %s, deployment %s",
                    azure_endpoint,
                    azure_deployment,
                )
                token_provider = azure.identity.get_bearer_token_provider(
                    azure_credential, "https://cognitiveservices.azure.com/.default"
                )
                openai_chat_client = openai.AsyncAzureOpenAI(
                    api_version=api_version,
                    azure_endpoint=azure_endpoint,
                    azure_deployment=azure_deployment,
                    azure_ad_token_provider=token_provider,
                )
        elif OPENAI_CHAT_HOST == "ollama":
            logger.info("Setting up OpenAI client for chat completions using Ollama")
            openai_chat_client = openai.AsyncOpenAI(
                base_url=os.getenv("OLLAMA_ENDPOINT"),
                api_key="nokeyneeded",
            )
        else:
            logger.info("Setting up OpenAI client for chat completions using OpenAI.com API key")
            openai_chat_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAICOM_KEY"))

        return openai_chat_client

    def compute_text_embedding(self,
        q: str,
        openai_client: OpenAI | AzureOpenAI,
        embed_model: str,
        embed_deployment: str | None = None,
        embedding_dimensions: int | None = None,
    ) -> list[float]:
        SUPPORTED_DIMENSIONS_MODEL = {
            "text-embedding-ada-002": False,
            "text-embedding-3-small": True,
            "text-embedding-3-large": True,
        }

        dimensions_args: Dict = {}
        if SUPPORTED_DIMENSIONS_MODEL.get(embed_model):
            if embedding_dimensions is None:
                raise ValueError(f"Model {embed_model} requires embedding dimensions")
            else:
                dimensions_args = {"dimensions": embedding_dimensions}

        embedding = openai_client.embeddings.create(
            # Azure OpenAI takes the deployment name as the model name
            model=embed_deployment if embed_deployment else embed_model,
            input=q,
            **dimensions_args,
        )
        return embedding.data[0].embedding

    def create_openai_embed_client(self,
        azure_credential,
        **kwargs: Any,
    ) -> openai.AzureOpenAI | openai.OpenAI:
        openai_embed_client: openai.AzureOpenAI | openai.OpenAI
        OPENAI_EMBED_HOST = os.getenv("OPENAI_EMBED_HOST")
        if OPENAI_EMBED_HOST == "azure":
            api_version = "2023-05-15"
            azure_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
            azure_deployment = os.environ["AZURE_OPENAI_EMBED_DEPLOYMENT"]
            if api_key := os.getenv("AZURE_OPENAI_KEY"):
                logger.info(
                    "Setting up Azure OpenAI client for embeddings using API key, endpoint %s, deployment %s",
                    azure_endpoint,
                    azure_deployment,
                )
                openai_embed_client = openai.AzureOpenAI(
                    api_version=api_version,
                    azure_endpoint=azure_endpoint,
                    azure_deployment=azure_deployment,
                    api_key=api_key,
                )
            else:
                token_provider = azure.identity.get_bearer_token_provider(
                    azure_credential, "https://cognitiveservices.azure.com/.default"
                )

                openai_embed_client = openai.AzureOpenAI(
                    api_version=api_version,
                    azure_endpoint=azure_endpoint,
                    azure_deployment=azure_deployment,
                    azure_ad_token_provider=token_provider,
                )
        elif OPENAI_EMBED_HOST == "ollama":
            logger.info("Setting up OpenAI client for embeddings using Ollama")
            openai_embed_client = openai.OpenAI(
                base_url=os.getenv("OLLAMA_ENDPOINT"),
                api_key="nokeyneeded",
            )
        else:
            logger.info("Setting up OpenAI client for embeddings using OpenAI.com API key")
            openai_embed_client = openai.OpenAI(api_key=os.getenv("OPENAICOM_KEY"))
        return openai_embed_client

    def similarity_search_by_vector(
        self, query_embedding: list[float], k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a vector-based similarity search."""
        if self._table_client is None:
            msg = "Table client is not initialized."
            raise ValueError(msg)

        try:
            query = f"SELECT TOP {k} c.id, c.text, c.vector, c.attributes, VectorDistance(c.vector, @embedding) AS SimilarityScore FROM c ORDER BY VectorDistance(c.vector, @embedding)"  # noqa: S608
            query_params = [{"name": "@embedding", "value": query_embedding}]
            items = list(
                self._table_client.query_items(
                    query=query,
                    parameters=query_params,
                    enable_cross_partition_query=True,
                )
            )
        except Exception:
            query = "SELECT c.id, c.text, c.vector, c.attributes FROM c"
            items = list(
                self._table_client.query_items(
                    query=query,
                    enable_cross_partition_query=True,
                )
            )

            # Calculate cosine similarity locally (1 - cosine distance)
            from numpy import dot
            from numpy.linalg import norm

            def cosine_similarity(a, b):
                if norm(a) * norm(b) == 0:
                    return 0.0
                return dot(a, b) / (norm(a) * norm(b))

            # Calculate scores for all items
            for item in items:
                item_vector = item.get("vector", [])
                similarity = cosine_similarity(query_embedding, item_vector)
                item["SimilarityScore"] = similarity

            # Sort by similarity score (higher is better) and take top k
            items = sorted(
                items, key=lambda x: x.get("SimilarityScore", 0.0), reverse=True
            )[:k]

        return [
            VectorStoreSearchResult(
                document=VectorStoreDocument(
                    id=item.get("id", ""),
                    text=item.get("text", ""),
                    vector=item.get("vector", []),
                    attributes=(json.loads(item.get("attributes", "{}"))),
                ),
                score=item.get("SimilarityScore", 0.0),
            )
            for item in items
        ]

    def similarity_search_by_text(
        self, text: str, text_embedder: TextEmbedder, k: int = 10, **kwargs: Any
    ) -> list[VectorStoreSearchResult]:
        """Perform a text-based similarity search."""
        query_embedding = text_embedder(text)
        if query_embedding:
            return self.similarity_search_by_vector(
                query_embedding=query_embedding, k=k
            )
        return []

    def filter_by_id(self, include_ids: list[str] | list[int]) -> Any:
        """Build a query filter to filter documents by a list of ids."""
        if include_ids is None or len(include_ids) == 0:
            self.query_filter = None
        else:
            if isinstance(include_ids[0], str):
                id_filter = ", ".join([f"'{id}'" for id in include_ids])
            else:
                id_filter = ", ".join([str(id) for id in include_ids])
            self.query_filter = f"SELECT * FROM c WHERE c.id IN ({id_filter})"  # noqa: S608
        return self.query_filter

    def search_by_id(self, id: str) -> VectorStoreDocument:
        """Search for a document by id."""
        if self._table_client is None:
            msg = "Table client is not initialized."
            raise ValueError(msg)

        item = self._table_client.read_item(item=id, partition_key=id)
        return VectorStoreDocument(
            id=item.get("id", ""),
            vector=item.get("vector", []),
            text=item.get("text", ""),
            attributes=(json.loads(item.get("attributes", "{}"))),
        )

    async def clear(self, session: Session) -> None:
        """Clear the vector store."""
        self.delete_table(session, self.collection_name)
        self.delete_database(session)

# Define the models
class Base(DeclarativeBase):
    pass

class Item(Base):
    __tablename__ = "vectors"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column()
    brand: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()
    # Embeddings for different models:
    embedding_large: Mapped[Vector] = mapped_column(Vector(3072), nullable=True)  # text-embedding-3-large
    embedding_ada002: Mapped[Vector] = mapped_column(Vector(1536), nullable=True)  # ada-002
    embedding_nomic: Mapped[Vector] = mapped_column(Vector(768), nullable=True)  # nomic-embed-text

    def to_dict(self, include_embedding: bool = False):
        model_dict = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        if include_embedding:
            model_dict["embedding_ada002"] = model_dict.get("embedding_ada002", [])
            model_dict["embedding_nomic"] = model_dict.get("embedding_nomic", [])
        else:
            del model_dict["embedding_ada002"]
            del model_dict["embedding_nomic"]
        return model_dict

    def to_str_for_rag(self):
        return f"Name:{self.name} Description:{self.description} Price:{self.price} Brand:{self.brand} Type:{self.type}"

    def to_str_for_embedding(self):
        return f"Name: {self.name} Description: {self.description} Type: {self.type}"


# class Case(Base):
#     __tablename__ = "cases"
#     id: Mapped[str] = mapped_column(Text, primary_key=True)
#     data: Mapped[MutableDict] = mapped_column(MutableDict.as_mutable(JSONB), nullable=False)
#     description_vector: Mapped[Vector] = mapped_column(
#         Vector(1536), nullable=True
#     )  # Assuming 1536-dimensional vector for description

#     def to_dict(self, include_vector: bool = False):
#         """
#         Converts the Case instance to a dictionary representation.
#         """
#         model_dict = {column.name: getattr(self, column.name) for column in self.__table__.columns}
#         if include_vector:
#             model_dict["description_vector"] = model_dict.get("description_vector", [])
#         else:
#             del model_dict["description_vector"]
#         return model_dict

#     def to_str_for_rag(self):
#         """
#         Converts Case to a string representation for Retrieval-Augmented Generation (RAG) usage.
#         """
#         data_fields = " ".join([f"{key}:{value}" for key, value in self.data.items()])
#         return f"ID: {self.id} Data: {data_fields}"

#     def to_str_for_embedding(self):
#         """
#         Converts Case to a string representation for embeddings.
#         """
#         return " ".join([f"{key}: {value}" for key, value in self.data.items() if key != "embedding"])


class Case(Base):
    __tablename__ = "cases_updated"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    data: Mapped[MutableDict] = mapped_column(MutableDict.as_mutable(JSONB), nullable=False)
    description_vector: Mapped[Vector] = mapped_column(Vector(1536), nullable=True)

    def to_dict(self, include_vectors: bool = False):
        """
        Converts the Case instance to a dictionary representation.
        """
        model_dict = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        if not include_vectors:
            model_dict.pop("description_vector", None)
        return model_dict

    def to_str_for_rag(self):
        """
        Converts Case to a string representation for Retrieval-Augmented Generation (RAG) usage.
        """
        # data_fields = " ".join([f"{key}:{value}" for key, value in self.data.items()])
        # return f"ID: {self.id} Data: {data_fields}"
        casebody_text = self.data.get("casebody", {}).get("opinions", [{}])[0].get("text", "")
        truncated_text = casebody_text[:800]  # Truncate to 800 characters

        # Include truncated data alongside other fields if necessary
        data_fields = [
            f"{key}:{value}"
            for key, value in self.data.items()
            if key != "casebody"  # Exclude the large 'casebody' field
        ]
        data_fields.append(f"casebody_opinion_text:{truncated_text}")

        page_rank = self.data.get("analysis", {}).get("pagerank", [{}]).get("percentile", "")
        data_str = " ".join(data_fields)
        return f"Pagerank: {page_rank} Data: {data_str}"

    def to_str_for_embedding(self):
        """
        Converts Case to a string representation for embeddings.
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

table_name = Case.__tablename__

index_description_vector = Index(
    f"{table_name}_description_vector_idx",
    Case.description_vector,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"description_vector": "vector_cosine_ops"},
)
