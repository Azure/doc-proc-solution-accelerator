from abc import ABC, abstractmethod
from dataclasses import Field
import hashlib
from typing import List, Dict, Any, AsyncGenerator, Optional
from datetime import datetime

from doc.proc.models import ContentIdentifier, ServiceExecutionError


class SourceItemMetadata:
    """Metadata for a source item (file, document, etc.)."""
    
    def __init__(self, 
                 content_identifier: ContentIdentifier,
                 name: str,
                 size: Optional[int] = None,
                 modified_date: Optional[datetime] = None,
                 created_date: Optional[datetime] = None,
                 content_type: Optional[str] = None,
                 etag: Optional[str] = None,
                 **kwargs):
        self.content_identifier = content_identifier
        self.name = name
        self.size = size
        self.modified_date = modified_date
        self.created_date = created_date
        self.content_type = content_type
        self.etag = etag
        self.additional_metadata = kwargs
    

class SourceItem:
    """Represents an item from a data source."""
    
    def __init__(self, 
                 content_identifier: ContentIdentifier,
                 metadata: SourceItemMetadata,
                 content: Optional[bytes] = None):
        self.content_identifier = content_identifier
        self.metadata = metadata
        self.content = content


class SourceBase(ABC):
    """
    Base class for data source crawlers.
    
    This class provides a standardized interface for crawling different data sources
    like Azure Blob Storage, Azure Files, SharePoint, etc. It follows the same
    patterns as Services and Steps in the document processing library.
    
    Each source implementation should provide methods to:
    - Test connection to the data source
    - Crawl the source to discover available items
    - Retrieve specific items by identifier
    - Fetch metadata for items without downloading content
    """

    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        """
        Initialize the source instance.
        
        Args:
            name: Name of the source instance
            type: Type of the source (e.g., 'azure_blob', 'azure_files', 'sharepoint')
            settings: Configuration settings for the source
            **kwargs: Additional parameters
        """
        self.name = name
        self.type = type
        self.settings = settings or {}
        self.params = kwargs

        if not self.name:
            raise ValueError("Source name cannot be empty")
        
        if not self.type:
            raise ValueError("Source type cannot be empty")

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the connection to the data source.
        
        Returns:
            bool: True if connection is successful, False otherwise
            
        Raises:
            ServiceExecutionError: If connection test fails with an error
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def crawl(self, 
                   path: Optional[str] = None,
                   recursive: bool = True,
                   crawl_depth: Optional[int] = None,
                   max_documents: Optional[int] = None,
                   file_filters: Optional[List[str]] = None,
                   incremental: Optional[bool] = True,
                   checkpoint_time: Optional[datetime] = None) -> AsyncGenerator[SourceItemMetadata, None]:
        """
        Crawl the data source to discover available items.
        
        Args:
            path: Starting path to crawl from (optional, defaults to root)
            recursive: Whether to crawl subdirectories recursively
            file_filters: List of file patterns to filter by (e.g., ['*.pdf', '*.docx'])
            
        Yields:
            SourceItemMetadata: Metadata for each discovered item
            
        Raises:
            ServiceExecutionError: If crawling fails
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def retrieve_item(self, content_identifier: ContentIdentifier) -> SourceItem:
        """
        Retrieve a specific item from the data source including its content.
        
        Args:
            content_identifier: Identifier for the item to retrieve
            
        Returns:
            SourceItem: The item with metadata and content
            
        Raises:
            ServiceExecutionError: If retrieval fails
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def get_item_metadata(self, content_identifier: ContentIdentifier) -> SourceItemMetadata:
        """
        Get metadata for a specific item without downloading its content.
        
        Args:
            content_identifier: Identifier for the item
            
        Returns:
            SourceItemMetadata: Metadata for the item
            
        Raises:
            ServiceExecutionError: If metadata retrieval fails
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def item_exists(self, content_identifier: ContentIdentifier) -> bool:
        """
        Check if an item exists in the data source.
        
        Args:
            content_identifier: Identifier for the item to check
            
        Returns:
            bool: True if the item exists, False otherwise
            
        Raises:
            ServiceExecutionError: If existence check fails
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def get_supported_file_types(self) -> List[str]:
        """
        Get list of supported file types for this source.
        
        Returns:
            List[str]: List of supported file extensions (e.g., ['.pdf', '.docx', '.txt'])
        """
        # Default implementation returns common document types
        return ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.md', '.csv']

    
    def _generate_sha1_hash(self, input_string: str) -> str:
        """
        Generates a sha1 hash from a given string.
        """
        # Encode the string to bytes, as hash functions operate on bytes
        encoded_string = input_string.encode('utf-8')
        # Create a SHA1 hash object
        sha1_hash = hashlib.sha1()
        # Update the hash object with the encoded string
        sha1_hash.update(encoded_string)
        # Get the hexadecimal representation of the hash
        return sha1_hash.hexdigest()
    
    
    def _validate_content_identifier(self, content_identifier: ContentIdentifier) -> None:
        """
        Validate that all required fields in ContentIdentifier are populated.
        
        Args:
            content_identifier: The ContentIdentifier to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        if not content_identifier.canonical_id:
            raise ValueError("ContentIdentifier.canonical_id cannot be empty")
        
        if not content_identifier.unique_id:
            raise ValueError("ContentIdentifier.unique_id cannot be empty")

        if not content_identifier.source_id:
            raise ValueError("ContentIdentifier.source_id cannot be empty")
        
        if not content_identifier.source_type:
            raise ValueError("ContentIdentifier.source_type cannot be empty")
        
        if not content_identifier.path:
            raise ValueError("ContentIdentifier.path cannot be empty")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.type}')"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.type}', settings={self.settings})"