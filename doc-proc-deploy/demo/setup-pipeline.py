#!/usr/bin/env python3
"""
Document Processing Pipeline Setup Script

Creates a complete document processing pipeline using the deployed API.
This script creates:
- Service instances (Azure Blob Storage)
- Step instances (content-retriever, document-type-identifier, blob-store-output)
- A sample blob source
- A pipeline with the steps
- A vault that uses both the pipeline and source
"""

import os
import sys
import json
import uuid
import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import argparse


# Configuration class
@dataclass
class Config:
    api_base_url: str
    azure_storage_account_name: str
    azure_storage_container_name: str
    azure_output_container_name: str
    resource_prefix: str
    

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class PipelineSetup:
    """Main class for setting up the document processing pipeline"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = None  # Will be initialized in async context
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Resource names
        self.storage_service_name = f"{config.resource_prefix}-storage-svc"
        self.content_retriever_step_name = f"{config.resource_prefix}-content-retriever"
        self.doc_type_step_name = f"{config.resource_prefix}-doc-type-id"
        self.blob_output_step_name = f"{config.resource_prefix}-blob-output"
        self.source_id = f"{config.resource_prefix}-blob-source"
        self.pipeline_name = f"{config.resource_prefix}-pipeline"
        self.vault_name = f"{config.resource_prefix}-vault"
        
    
    def print_colored(self, message: str, color: str) -> None:
        """Print colored message to console"""
        print(f"{color}{message}{Colors.NC}")
    
    def print_success(self, message: str) -> None:
        self.print_colored(f"✅ {message}", Colors.GREEN)
    
    def print_error(self, message: str) -> None:
        self.print_colored(f"❌ {message}", Colors.RED)
    
    def print_warning(self, message: str) -> None:
        self.print_colored(f"⚠️ {message}", Colors.YELLOW)
    
    def print_info(self, message: str) -> None:
        self.print_colored(f"ℹ️ {message}", Colors.BLUE)
    
    def print_header(self) -> None:
        """Print script header"""
        self.print_colored("=" * 47, Colors.BLUE)
        self.print_colored("  Document Processing Pipeline Setup", Colors.BLUE)
        self.print_colored("=" * 47, Colors.BLUE)
        print()
    
    async def api_call(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, description: str = "") -> Dict[str, Any]:
        """Make API call with error handling"""
        url = f"{self.config.api_base_url}{endpoint}"
        
        self.logger.info(f"API Call: {method} {url}")
        if data:
            self.logger.info(f"Data: {json.dumps(data, indent=2)}")
        
        try:
            headers = {'Content-Type': 'application/json'}
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                if method == "POST":
                    async with session.post(url, json=data) as response:
                        return await self._process_response(response, description)
                elif method == "GET":
                    async with session.get(url) as response:
                        return await self._process_response(response, description)
                elif method == "PUT":
                    async with session.put(url, json=data) as response:
                        return await self._process_response(response, description)
                elif method == "DELETE":
                    async with session.delete(url) as response:
                        return await self._process_response(response, description)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
            
        except aiohttp.ClientError as e:
            self.logger.error(f"API call failed: {e}")
            self.print_error(f"Failed to {description}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in API call: {e}")
            self.print_error(f"Failed to {description}")
            raise
    
    async def _process_response(self, response: aiohttp.ClientResponse, description: str) -> Dict[str, Any]:
        """Process aiohttp response"""
        try:
            # Check if request was successful
            response.raise_for_status()
            
            # Get response text
            response_text = await response.text()
            
            # Parse JSON if there's content
            if response_text.strip():
                result = json.loads(response_text)
            else:
                result = {}
            
            self.logger.info(f"Response: {json.dumps(result, indent=2)}")
            return result
            
        except aiohttp.ClientResponseError as e:
            self.logger.error(f"HTTP error {e.status}: {e.message}")
            try:
                error_text = await response.text()
                if error_text:
                    try:
                        error_detail = json.loads(error_text)
                        self.logger.error(f"Error details: {json.dumps(error_detail, indent=2)}")
                    except json.JSONDecodeError:
                        self.logger.error(f"Error response: {error_text}")
            except:
                pass
            self.print_error(f"Failed to {description}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.print_error(f"Failed to {description}")
            raise
    
    def extract_id(self, response: Dict[str, Any]) -> str:
        """Extract ID from API response"""
        return response.get('id', '')
    
    async def test_api_connection(self) -> None:
        """Test API connectivity"""
        self.print_info(f"Testing API connection to {self.config.api_base_url}...")
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.config.api_base_url}/api/health") as response:
                    response.raise_for_status()
                    self.print_success(f"API is accessible at {self.config.api_base_url}")
        except (aiohttp.ClientError, asyncio.TimeoutError):
            self.print_error(f"Cannot connect to API at {self.config.api_base_url}")
            self.print_info("Make sure the API is running and the URL is correct")
            sys.exit(1)
    
    async def create_storage_service(self) -> str:
        """Create Azure Blob Storage service instance"""
        self.print_info(f"Creating Azure Blob Storage service instance: {self.storage_service_name}")
        
        service_data = {
            "name": self.storage_service_name,
            "service_catalog_id": "azure_storage_service_01",
            "settings": {
                "account_name": self.config.azure_storage_account_name,
                "credential_type": "default_azure_credential",
            }
        }
        
        response = await self.api_call("POST", "/api/services/instances", service_data, "create storage service")
        service_id = self.extract_id(response)
        
        if service_id:
            self.print_success(f"Storage service created with ID: {service_id}")
            return service_id
        else:
            self.print_error("Failed to create storage service")
            sys.exit(1)
    
    async def test_service_connection(self, service_id: str, service_name: str) -> None:
        """Test service connection"""
        self.print_info(f"Testing connection for service: {service_name} (ID: {service_id})")
        
        try:
            response = await self.api_call("POST", f"/api/services/instances/{service_id}/test", {}, "test service connection")
            
            if (response.get('success') is True or 
                response.get('status') == 'success'):
                self.print_success(f"Service connection test passed for {service_name}")
            else:
                self.print_warning(f"Service connection test failed for {service_name}, but continuing...")
                self.logger.warning(f"Test response: {json.dumps(response, indent=2)}")
        except Exception as e:
            self.print_warning(f"Service connection test failed for {service_name}, but continuing...")
            self.logger.warning(f"Test error: {str(e)}")
    
    async def create_content_retriever_step(self) -> str:
        """Create content retriever step instance"""
        self.print_info(f"Creating content retriever step: {self.content_retriever_step_name}")
        
        step_data = {
            "name": self.content_retriever_step_name,
            "step_catalog_id": "content_retriever",
            "settings": {
                "include_content_bytes_as_field": False,
                "use_temp_file_for_content": True
            },
            "enabled": True,
            "fail_pipeline_on_error": True,
            "timeout": 60,
            "services": [],
            "condition": "",
            "debug_mode": False
        }
        
        response = await self.api_call("POST", "/api/steps/instances", step_data, "create content retriever step")
        step_id = self.extract_id(response)
        
        if step_id:
            self.print_success(f"Content retriever step created with ID: {step_id}")
            return step_id
        else:
            self.print_error("Failed to create content retriever step")
            sys.exit(1)
    
    async def create_document_type_step(self) -> str:
        """Create document type identifier step instance"""
        self.print_info(f"Creating document type identifier step: {self.doc_type_step_name}")
        
        step_data = {
            "name": self.doc_type_step_name,
            "step_catalog_id": "document_type_identifier",
            "settings": {
                "identification_methods": "file_extension"
            },
            "enabled": True,
            "fail_pipeline_on_error": False,
            "timeout": 30,
            "services": [],
            "condition": "",
            "debug_mode": False
        }
        
        response = await self.api_call("POST", "/api/steps/instances", step_data, "create document type identifier step")
        step_id = self.extract_id(response)
        
        if step_id:
            self.print_success(f"Document type identifier step created with ID: {step_id}")
            return step_id
        else:
            self.print_error("Failed to create document type identifier step")
            sys.exit(1)
    
    async def create_blob_output_step(self, storage_service_id: str) -> str:
        """Create blob store output step instance"""
        self.print_info(f"Creating blob store output step: {self.blob_output_step_name}")
        
        step_data = {
            "name": self.blob_output_step_name,
            "step_catalog_id": "blob_store_output",
            "settings": {
                "storage_service": storage_service_id,
                "blob_container": self.config.azure_output_container_name,
                "blob_path": "{pipeline_name}/{file_name}",
                "overwrite_existing": True,
                "delete_temp_file": True
            },
            "enabled": True,
            "fail_pipeline_on_error": False,
            "timeout": 120,
            "services": [storage_service_id],
            "condition": "",
            "debug_mode": False
        }
        
        response = await self.api_call("POST", "/api/steps/instances", step_data, "create blob output step")
        step_id = self.extract_id(response)
        
        if step_id:
            self.print_success(f"Blob output step created with ID: {step_id}")
            return step_id
        else:
            self.print_error("Failed to create blob output step")
            sys.exit(1)
    
    async def create_sample_source(self) -> str:
        """Create a sample blob source instance"""
        self.print_info(f"Creating sample blob source instance: {self.source_id}")
        
        source_data = {
            "name": self.source_id,
            "source_catalog_id": "azure_blob_storage",
            "description": "Sample Azure Blob Storage source for demo pipeline",
            "settings": {
                "account_name": self.config.azure_storage_account_name,
                "container_name": self.config.azure_storage_container_name,
                "credential_type": "default_azure_credential",
            },
            "crawler_settings": {
                "crawl_interval_minutes": 5,
                "max_files_per_crawl": 100
            },
            "enabled": True,
            "test_connection": True
        }
        
        response = await self.api_call("POST", "/api/sources/instances", source_data, "create sample source")
        source_id = self.extract_id(response)
        
        if source_id:
            self.print_success(f"Sample source created with ID: {source_id}")
            return source_id
        else:
            self.print_error("Failed to create sample source")
            sys.exit(1)
    
    async def create_pipeline(self, content_retriever_step_id: str, doc_type_step_id: str, blob_output_step_id: str) -> str:
        """Create pipeline with step instances"""
        self.print_info(f"Creating pipeline: {self.pipeline_name}")
        
        pipeline_data = {
            "name": self.pipeline_name,
            "description": "Demo document processing pipeline with content retrieval, type identification, and blob output",
            "steps": [
                content_retriever_step_id,
                doc_type_step_id,
                blob_output_step_id
            ],
            "execution_sequence": [
                content_retriever_step_id,
                doc_type_step_id,
                blob_output_step_id
            ],
            "settings": {
                "enabled": True,
                "retry_delay": 5,
                "timeout": 600,
                "retries": 3,
                "max_concurrent_runs": 5
            },
        }
        
        response = await self.api_call("POST", "/api/pipelines", pipeline_data, "create pipeline")
        pipeline_id = self.extract_id(response)
        
        if pipeline_id:
            self.print_success(f"Pipeline created with ID: {pipeline_id}")
            return pipeline_id
        else:
            self.print_error("Failed to create pipeline")
            sys.exit(1)
    
    async def create_vault(self, pipeline_id: str, source_instance_name: str) -> str:
        """Create vault with pipeline and source"""
        self.print_info(f"Creating vault: {self.vault_name}")
        
        vault_data = {
            "name": self.vault_name,
            "description": "Demo vault for document processing pipeline",
            "pipeline_name": self.pipeline_name,
            "source_instance_name": source_instance_name,
            "processing_config": {
                "auto_process_documents": True,
                "max_concurrent_documents": 5,
                "retry_failed_documents": True,
                "max_retries": 3
            },
        }
        
        response = await self.api_call("POST", "/api/vaults", vault_data, "create vault")
        vault_id = self.extract_id(response)
        
        if vault_id:
            self.print_success(f"Vault created with ID: {vault_id}")
            return vault_id
        else:
            self.print_error("Failed to create vault")
            sys.exit(1)
    
    def display_summary(self, storage_service_id: str, content_retriever_step_id: str, 
                       doc_type_step_id: str, blob_output_step_id: str, 
                       source_instance_id: str, pipeline_id: str, vault_id: str) -> None:
        """Display setup summary"""
        print()
        self.print_colored("=" * 47, Colors.BLUE)
        self.print_colored("          Pipeline Setup Complete!", Colors.BLUE)
        self.print_colored("=" * 47, Colors.BLUE)
        print()
        
        self.print_success("All components created successfully!")
        print()
        
        self.print_colored("📋 Summary:", Colors.BLUE)
        print(f"  {Colors.GREEN}• Storage Service:{Colors.NC} {self.storage_service_name} (ID: {storage_service_id})")
        print(f"  {Colors.GREEN}• Content Retriever Step:{Colors.NC} {self.content_retriever_step_name} (ID: {content_retriever_step_id})")
        print(f"  {Colors.GREEN}• Document Type Step:{Colors.NC} {self.doc_type_step_name} (ID: {doc_type_step_id})")
        print(f"  {Colors.GREEN}• Blob Output Step:{Colors.NC} {self.blob_output_step_name} (ID: {blob_output_step_id})")
        print(f"  {Colors.GREEN}• Source Instance:{Colors.NC} {self.source_id} (ID: {source_instance_id})")
        print(f"  {Colors.GREEN}• Pipeline:{Colors.NC} {self.pipeline_name} (ID: {pipeline_id})")
        print(f"  {Colors.GREEN}• Vault:{Colors.NC} {self.vault_name} (ID: {vault_id})")
        print()
        
        self.print_colored("🔗 API Links:", Colors.BLUE)
        print(f"  {Colors.GREEN}• API Health:{Colors.NC} {self.config.api_base_url}/api/health")
        print(f"  {Colors.GREEN}• API Docs:{Colors.NC} {self.config.api_base_url}/docs")
        print(f"  {Colors.GREEN}• Vault Details:{Colors.NC} {self.config.api_base_url}/api/vaults/{vault_id}")
        print(f"  {Colors.GREEN}• Pipeline Details:{Colors.NC} {self.config.api_base_url}/api/pipelines/{pipeline_id}")
        print()
        
        self.print_colored("📁 Configuration Used:", Colors.BLUE)
        print(f"  {Colors.GREEN}• Storage Account:{Colors.NC} {self.config.azure_storage_account_name}")
        print(f"  {Colors.GREEN}• Input Container:{Colors.NC} {self.config.azure_storage_container_name}")
        print(f"  {Colors.GREEN}• Output Container:{Colors.NC} {self.config.azure_output_container_name}")
        print()
        
        self.print_info("You can now upload documents to the vault to test the pipeline!")
    
    async def run(self) -> None:
        """Main execution flow"""
        self.print_header()
        
        # Prerequisites check
        await self.test_api_connection()
        
        self.print_info(f"Starting pipeline setup with resource prefix: {self.config.resource_prefix}")
        print()
        
        self.print_info("=== Starting Document Processing Pipeline Setup ===")
        print()
        
        # Step 1: Create storage service
        self.print_info("Step 1/7: Creating storage service...")
        storage_service_id = await self.create_storage_service()
        await self.test_service_connection(storage_service_id, self.storage_service_name)
        print()
        
        # Step 2: Create content retriever step
        self.print_info("Step 2/7: Creating content retriever step...")
        content_retriever_step_id = await self.create_content_retriever_step()
        print()
        
        # Step 3: Create document type identifier step
        self.print_info("Step 3/7: Creating document type identifier step...")
        doc_type_step_id = await self.create_document_type_step()
        print()
        
        # Step 4: Create blob output step
        self.print_info("Step 4/7: Creating blob output step...")
        blob_output_step_id = await self.create_blob_output_step(storage_service_id)
        print()
        
        # Step 5: Create sample source
        self.print_info("Step 5/7: Creating sample blob source...")
        source_instance_id = await self.create_sample_source()
        print()
        
        # Step 6: Create pipeline
        self.print_info("Step 6/7: Creating pipeline...")
        pipeline_id = await self.create_pipeline(content_retriever_step_id, doc_type_step_id, blob_output_step_id)
        print()
        
        # Step 7: Create vault
        self.print_info("Step 7/7: Creating vault...")
        vault_id = await self.create_vault(pipeline_id, self.source_id)
        print()
        
        # Display final summary
        self.display_summary(storage_service_id, content_retriever_step_id, doc_type_step_id, 
                           blob_output_step_id, source_instance_id, pipeline_id, vault_id)
        
        self.print_success("Pipeline setup completed successfully!")


async def async_main():
    """Async main execution function"""
    
    parser = argparse.ArgumentParser(description='Document Processing Pipeline Setup Script')
    parser.add_argument('--api-url', help='API base URL (overrides API_BASE_URL env var)')
    parser.add_argument('--storage-account', help='Azure Storage Account name (overrides AZURE_STORAGE_ACCOUNT_NAME env var)')
    
    args = parser.parse_args()
    
    try:
        # Override environment variables with command line arguments if provided
        if not args.api_url:
            print(f"{Colors.RED}❌ API Base URL is required.{Colors.NC}")
            sys.exit(1)
        if not args.storage_account:
            print(f"{Colors.RED}❌ Storage Account is required.{Colors.NC}")
            sys.exit(1)
        
        # Load configuration
        config = Config(api_base_url=args.api_url,
                        azure_storage_account_name=args.storage_account,
                        azure_storage_container_name='documents',
                        azure_output_container_name='output',
                        resource_prefix=f"demo-{uuid.uuid4().hex[:3]}")
        
        # Run the setup
        setup = PipelineSetup(config)
        await setup.run()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Setup failed: {str(e)}{Colors.NC}")
        sys.exit(1)


def main():
    """Main entry point - runs async main"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()