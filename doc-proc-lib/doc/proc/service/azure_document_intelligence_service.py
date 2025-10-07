import logging
import os
from typing import List, Dict, Any


from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient, DocumentIntelligenceAdministrationClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, DocumentContentFormat, AnalyzeResult

from doc.proc.service.service_base import ServiceBase
from doc.proc.models import ServiceExecutionError

logger = logging.getLogger("doc.proc.service.azure_document_intelligence_service") # need to specify the logger name as this module is loaded dynamically


class AzureDocumentIntelligenceService(ServiceBase):
    """Azure Document Intelligence service for document analysis and content extraction."""

    def __init__(self, name: str, type: str, settings: dict, **kwargs):
        super().__init__(name=name, type=type, settings=settings, **kwargs)

        self.endpoint = settings.get('endpoint', '').strip()
        self.credential_type = settings.get('credential_type', '').strip()
        self.api_version = settings.get('api_version', '2023-07-31').strip()
        self.model_id = settings.get('model_id', 'prebuilt-layout').strip()
        self.api_key = ''

        # Validate endpoint
        if not self.endpoint:
            raise ValueError("Settings key 'endpoint' is required")

        if self.endpoint.startswith('${') and self.endpoint.endswith('}'):
            env_var_name = self.endpoint[2:-1]
            self.endpoint = os.getenv(env_var_name)
            if not self.endpoint:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
        

        # Validate credential type
        if not self.credential_type:
            raise ValueError("Settings key 'credential_type' is required")
        
        if self.credential_type.startswith('${') and self.credential_type.endswith('}'):
            env_var_name = self.credential_type[2:-1]
            self.credential_type = os.getenv(env_var_name)
            if not self.credential_type:
                raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
            
            self.credential_type = self.credential_type.lower()

        
        # Validate API key based on credential type
        if self.credential_type == 'azure_key_credential':
            self.api_key = settings.get('api_key', '').strip()
            if not self.api_key:
                raise ValueError("Settings key 'api_key' is required for azure_key_credential")

            # Read the API key from environment variable
            if self.api_key.startswith('${') and self.api_key.endswith('}'):
                env_var_name = self.api_key[2:-1]
                self.api_key = os.getenv(env_var_name)
                if not self.api_key:
                    raise ValueError(f"Environment variable '{env_var_name}' is not set or empty. Ensure it is defined in your environment or .env file.")
            else:
                self.api_key = self.api_key

        elif self.credential_type == 'default_azure_credential':
            self.api_key = ''        
        else:
            raise ValueError(f"Unsupported credential type: {self.credential_type}. Supported types are 'azure_key_credential' and 'default_azure_credential'.")


        # Validate API version
        if self.api_version not in ['2023-07-31', '2022-08-31', '2021-09-30-preview']:
            logger.warning(f"Unsupported API version: {self.api_version}. Supported versions are '2023-07-31', '2022-08-31', and '2021-09-30-preview'.")

        # Validate model ID
        supported_models = [
            'prebuilt-layout', 'prebuilt-read', 
            'prebuilt-businessCard', 'prebuilt-idDocument', 'prebuilt-invoice',
            'prebuilt-receipt', 'prebuilt-tax.us.w2', 'prebuilt-healthInsuranceCard.us'
        ]
        if self.model_id not in supported_models:
            logger.warning(f"Model ID '{self.model_id}' may not be supported. Supported models: {supported_models}")

        self.document_client: DocumentIntelligenceClient = None
        self.__init_client()

    def __init_client(self):
        """Initialize the DocumentIntelligenceClient."""

        logger.debug(f"Creating DocumentIntelligenceClient with endpoint: {self.endpoint} and credential type: {self.credential_type}")

        cred = DefaultAzureCredential() if self.credential_type == 'default_azure_credential' else AzureKeyCredential(self.api_key)
        
        # Initialize the DocumentIntelligenceClient with the appropriate credential
        self.document_client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=cred
        )

        logger.debug(f"Initialized DocumentIntelligenceClient for Azure Document Intelligence Service: {self.name}")

    async def test_connection(self) -> bool:
        """Test the connection to the Azure Document Intelligence service."""
        try:
            # Test with a simple operation - get account information
            cred = DefaultAzureCredential() if self.credential_type == 'default_azure_credential' else AzureKeyCredential(self.api_key)

            result = False
            
            # Use the administration client to list models as a connectivity test
            async with DocumentIntelligenceAdministrationClient(endpoint=self.endpoint, credential=cred) as document_intelligence_admin_client:
                # Try to get info about the service models
                async for model in document_intelligence_admin_client.list_models():
                    # If we can list at least one model, the connection is working
                    logger.debug(f"Connected to Azure Document Intelligence Service: {self.name}. Found model: {model.model_id}")
                    result = True
                    break  # No need to list all models, just confirm connectivity

                if isinstance(cred, DefaultAzureCredential):
                    await cred.close()
            
            return result
        except Exception as e:
            logger.error(f"Failed to connect to Azure Document Intelligence Service: {str(e)}")
            raise ServiceExecutionError(f"Failed to connect to Azure Document Intelligence Service: {str(e)}")

    async def analyze_document_from_url(self, document_url: str, model_id: str = None) -> Dict[str, Any]:
        """
        Analyze a document from URL using Azure Document Intelligence.
        
        :param document_url: URL of the document to analyze
        :param model_id: Model ID to use for analysis (defaults to instance model_id)
        :return: Analysis result dictionary
        """
        if not model_id:
            model_id = self.model_id

        try:
            async with self.document_client as client:
                poller = await client.begin_analyze_document(
                    model_id=model_id,
                    body=AnalyzeDocumentRequest(
                        url_source=document_url
                    )
                )
                
                result: AnalyzeResult = await poller.result()
                
                return self._process_analysis_result(result)

        except Exception as e:
            logger.error(f"Error analyzing document from URL '{document_url}': {str(e)}")
            raise ServiceExecutionError(f"Failed to analyze document from URL: {str(e)}")

    async def analyze_document_from_bytes(self, document_bytes: bytes, model_id: str = None, output_content_format: str = "markdown") -> Dict[str, Any]:
        """
        Analyze a document from bytes using Azure Document Intelligence.
        
        :param document_bytes: Document content as bytes
        :param model_id: Model ID to use for analysis (defaults to instance model_id)
        :param output_content_format: Format for the extracted content, either "text" or "markdown"
        :return: Analysis result dictionary
        """
        if not model_id:
            model_id = self.model_id

        try:
            poller = await self.document_client.begin_analyze_document(
                    model_id=model_id,
                    body=AnalyzeDocumentRequest(
                        bytes_source=document_bytes,
                    ),
                    output_content_format= DocumentContentFormat.TEXT if output_content_format == "text" else DocumentContentFormat.MARKDOWN,
                )
                
            result: AnalyzeResult = await poller.result()
                
            return self._process_analysis_result(result)

        except Exception as e:
            logger.error(f"Error analyzing document from bytes: {str(e)}")
            raise ServiceExecutionError(f"Failed to analyze document from bytes: {str(e)}")

    def _process_analysis_result(self, result) -> Dict[str, Any]:
        """
        Process the raw analysis result into a structured format.
        
        :param result: Raw analysis result from Azure Document Intelligence
        :return: Processed result dictionary
        """
        processed_result = {
            "content": result.content if hasattr(result, 'content') else "",
            "pages": [],
            "tables": [],
            "paragraphs": [],
            "styles": [],
            "key_value_pairs": [],
            "entities": []
        }

        # Process pages
        if hasattr(result, 'pages') and result.pages:
            for page in result.pages:
                page_data = {
                    "page_number": page.page_number if hasattr(page, 'page_number') else 1,
                    "spans": [{"offset": span.offset, "length": span.length} for span in page.spans] if hasattr(page, 'spans') and page.spans else [],
                    "words": [],
                    "lines": [],
                    "selection_marks": []
                }
                
                # Process words
                if hasattr(page, 'words') and page.words:
                    for word in page.words:
                        page_data["words"].append({
                            "content": word.content if hasattr(word, 'content') else "",
                            "polygon": word.polygon if hasattr(word, 'polygon') else [],
                            "confidence": word.confidence if hasattr(word, 'confidence') else 1.0,
                            "span": {"offset": word.span.offset, "length": word.span.length} if hasattr(word, 'span') and word.span else {}
                        })

                # Process lines
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        page_data["lines"].append({
                            "content": line.content if hasattr(line, 'content') else "",
                            "polygon": line.polygon if hasattr(line, 'polygon') else [],
                            "spans": [{"offset": span.offset, "length": span.length} for span in line.spans] if hasattr(line, 'spans') and line.spans else []
                        })

                processed_result["pages"].append(page_data)

        # Process tables
        if hasattr(result, 'tables') and result.tables:
            for table in result.tables:
                table_data = {
                    "row_count": table.row_count if hasattr(table, 'row_count') else 0,
                    "column_count": table.column_count if hasattr(table, 'column_count') else 0,
                    "cells": [],
                    "spans": [{"offset": span.offset, "length": span.length} for span in table.spans] if hasattr(table, 'spans') and table.spans else []
                }
                
                # Process table cells
                if hasattr(table, 'cells') and table.cells:
                    for cell in table.cells:
                        table_data["cells"].append({
                            "content": cell.content if hasattr(cell, 'content') else "",
                            "row_index": cell.row_index if hasattr(cell, 'row_index') else 0,
                            "column_index": cell.column_index if hasattr(cell, 'column_index') else 0,
                            "row_span": cell.row_span if hasattr(cell, 'row_span') else 1,
                            "column_span": cell.column_span if hasattr(cell, 'column_span') else 1,
                            "kind": cell.kind if hasattr(cell, 'kind') else "content",
                            "spans": [{"offset": span.offset, "length": span.length} for span in cell.spans] if hasattr(cell, 'spans') and cell.spans else []
                        })

                processed_result["tables"].append(table_data)

        # Process paragraphs
        if hasattr(result, 'paragraphs') and result.paragraphs:
            for paragraph in result.paragraphs:
                processed_result["paragraphs"].append({
                    "content": paragraph.content if hasattr(paragraph, 'content') else "",
                    "role": paragraph.role if hasattr(paragraph, 'role') else None,
                    "spans": [{"offset": span.offset, "length": span.length} for span in paragraph.spans] if hasattr(paragraph, 'spans') and paragraph.spans else []
                })

        # Process key-value pairs
        if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
            for kv_pair in result.key_value_pairs:
                kv_data = {
                    "key": {},
                    "value": {},
                    "confidence": kv_pair.confidence if hasattr(kv_pair, 'confidence') else 1.0
                }
                
                if hasattr(kv_pair, 'key') and kv_pair.key:
                    kv_data["key"] = {
                        "content": kv_pair.key.content if hasattr(kv_pair.key, 'content') else "",
                        "spans": [{"offset": span.offset, "length": span.length} for span in kv_pair.key.spans] if hasattr(kv_pair.key, 'spans') and kv_pair.key.spans else []
                    }
                
                if hasattr(kv_pair, 'value') and kv_pair.value:
                    kv_data["value"] = {
                        "content": kv_pair.value.content if hasattr(kv_pair.value, 'content') else "",
                        "spans": [{"offset": span.offset, "length": span.length} for span in kv_pair.value.spans] if hasattr(kv_pair.value, 'spans') and kv_pair.value.spans else []
                    }

                processed_result["key_value_pairs"].append(kv_data)

        return processed_result

