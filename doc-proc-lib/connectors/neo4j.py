# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing the CosmosDB vector store implementation."""
import os
import asyncio
import sys
import csv
import json
import logging
import numpy as np
import openai
import azure.identity
import networkx as nx

from neo4j import GraphDatabase

from typing import Any, TypedDict, Dict, List, Optional
from enum import Enum

from azure.identity import ManagedIdentityCredential, ChainedTokenCredential, AzureCliCredential

from openai import AsyncAzureOpenAI, AsyncOpenAI, AzureOpenAI, OpenAI
from dependencies import get_config
config = get_config()

logger = logging.getLogger("neo4j")

class Neo4jClient(BaseVectorStore):
    """Neo4j vector storage implementation."""

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
        self.driver = None

        # Ensure environment variables are set
        if not all([self.host, self.username, self.password, self.database]):
            raise ValueError("Missing required environment variables for database connection.")

    def filter_by_id(self, id: str) -> List[VectorStoreDocument]:
        pass

    def filter_by_ids(self, ids: List[str]) -> List[VectorStoreDocument]:
        pass

    def search_by_id(self, id):
        pass

    def similarity_search_by_text(self, text, text_embedder, k = 10, **kwargs):
        pass

    def similarity_search_by_vector(self, query_embedding, k = 10, **kwargs):
        pass

    def connect(self, **kwargs: Any) -> Any:
        """Connect to Neo4j."""

        if self.auth_type == "azure_managed_identity":
            azure_credential = ChainedTokenCredential(ManagedIdentityCredential(), AzureCliCredential())
            self.password = self.get_password_from_azure_credential(azure_credential)

        try:
            AUTH = (self.username, self.password)
            self.driver = GraphDatabase.driver(self.host, auth=AUTH)
            self.driver.verify_connectivity()

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j: {e}")

        credential = None

        if self.auth_type == "azure_managed_identity":
            credential = ChainedTokenCredential(ManagedIdentityCredential(), AzureCliCredential())

    def initialize(self, **kwargs: Any) -> None:

        self.create_database(self.conn, **kwargs)
        self.create_tables(self.conn, **kwargs)

    def create_database(self, conn, **kwargs) -> None:
        
        try:
            self.driver.execute_query(f"CREATE DATABASE {self.database}")
            print(f"Database '{self.database}' created successfully.")
        except Exception as e:
            print(f"Error creating database: {e}")
        finally:
            self.driver.close()

    def delete_database(self) -> None:
        try:
            self.driver.execute_query(f"DELETE DATABASE {self.database}")
            print(f"Database '{self.database}' deleted successfully.")
        except Exception as e:
            print(f"Error deleting database: {e}")
        finally:
            self.driver.close()

    def database_exists(self) -> bool:
        # You can also verify its existence (optional)
        records, summary, keys = self.driver.execute_query("SHOW DATABASES YIELD name")
        print("\nAvailable databases:")
        for record in records:
            if record["name"] == self.database:
                print(f"- {record['name']} (exists)")
                return True
            print(f"- {record['name']}")

        return False

    async def search(
        self,
        cypher_query: str | None
    ):
        
        summary = self.driver.execute_query(
            cypher_query,
            database_=self.database
        ).summary

        return summary