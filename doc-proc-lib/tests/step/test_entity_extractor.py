"""
Unit tests for the EntityExtractorStep class.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from doc.proc.step.entity_extractor import EntityExtractorStep
from doc.proc.step.step_base import StepInputOutput, StepExecutionError, StepInstanceConfig


class TestEntityExtractorStep:
    """Test cases for EntityExtractorStep."""
    
    @pytest.fixture
    def entity_extractor_config(self):
        """Fixture for EntityExtractorStep configuration."""
        return StepInstanceConfig(
            step_catalog_id="entity_extractor",
            name="entity_extractor_instance",
            enabled=True,
            debug_mode=True,
            services=["ai_inference_service"],
            settings={
                "chunk_field_to_extract_entities_from": "text",
                "output_field_name": "extracted_entities",
                "extract_people": True,
                "extract_places": True,
                "extract_locations": True,
                "extract_organizations": True,
                "extract_relationships": True,
                "custom_entity_types": ["PRODUCT", "TECHNOLOGY"],
                "output_format": "structured",
                "include_confidence": True,
                "include_context": True,
                "prompts": {
                    "system": "You are an expert entity extraction system.",
                    "user": "Extract entities from this text: {chunk_content}"
                },
                "max_completion_tokens": 4000,
                "temperature": 0.1
            }
        )
    
    @pytest.fixture
    def minimal_entity_extractor_config(self):
        """Fixture for minimal EntityExtractorStep configuration."""
        return StepInstanceConfig(
            step_catalog_id="entity_extractor",
            name="entity_extractor_minimal",
            enabled=True,
            services=["ai_inference_service"],
            settings={
                "prompts": {
                    "system": "Extract entities.",
                    "user": "Text: {chunk_content}"
                }
            }
        )
    
    @pytest.fixture
    def documents_with_chunks_input(self):
        """Fixture for documents with chunks for entity extraction."""
        return StepInputOutput(
            id="entity_extraction_test",
            summary_data={"total_documents": 2},
            data={
                "documents": [
                    {
                        "file_path": "/test/doc1.pdf",
                        "file_name": "doc1.pdf",
                        "chunks": [
                            {
                                "chunk_id": "chunk_1",
                                "chunk_num": 1,
                                "text": "John Smith is the CEO of TechCorp located in San Francisco. The company was founded in 2020.",
                                "raw_text": "John Smith is the CEO of TechCorp located in San Francisco. The company was founded in 2020.",
                                "page_num": 1
                            },
                            {
                                "chunk_id": "chunk_2",
                                "chunk_num": 2,
                                "text": "Dr. Sarah Johnson works at Stanford University in Palo Alto, California.",
                                "raw_text": "Dr. Sarah Johnson works at Stanford University in Palo Alto, California.",
                                "page_num": 1
                            }
                        ]
                    },
                    {
                        "file_path": "/test/doc2.txt",
                        "file_name": "doc2.txt",
                        "chunks": [
                            {
                                "chunk_id": "chunk_3",
                                "chunk_num": 1,
                                "text": "Microsoft Corporation announced a partnership with OpenAI in Redmond, Washington.",
                                "raw_text": "Microsoft Corporation announced a partnership with OpenAI in Redmond, Washington.",
                                "page_num": 1
                            }
                        ]
                    }
                ]
            }
        )
    
    @pytest.fixture
    def mock_ai_response(self):
        """Fixture for mock AI response with extracted entities."""
        return '''{
            "entities": [
                {
                    "text": "John Smith",
                    "type": "PERSON",
                    "confidence": 9,
                    "context": "John Smith is the CEO of TechCorp",
                    "start_position": 0,
                    "end_position": 10
                },
                {
                    "text": "TechCorp",
                    "type": "ORGANIZATION",
                    "confidence": 10,
                    "context": "CEO of TechCorp located in San Francisco",
                    "start_position": 23,
                    "end_position": 31
                },
                {
                    "text": "San Francisco",
                    "type": "PLACE",
                    "confidence": 10,
                    "context": "TechCorp located in San Francisco",
                    "start_position": 43,
                    "end_position": 56
                }
            ],
            "relationships": [
                {
                    "entity1": "John Smith",
                    "entity2": "TechCorp",
                    "relationship": "CEO of",
                    "confidence": 9,
                    "context": "John Smith is the CEO of TechCorp"
                },
                {
                    "entity1": "TechCorp",
                    "entity2": "San Francisco",
                    "relationship": "located in",
                    "confidence": 8,
                    "context": "TechCorp located in San Francisco"
                }
            ]
        }'''
    
    def test_entity_extractor_step_initialization_success(self, entity_extractor_config):
        """Test successful initialization of EntityExtractorStep."""
        step = EntityExtractorStep(entity_extractor_config)
        
        assert step.step_catalog_id == "entity_extractor"
        assert step.name == "entity_extractor_instance"
        assert step.debug_mode is True
        assert step.extract_people is True
        assert step.extract_places is True
        assert step.extract_organizations is True
        assert step.extract_relationships is True
        assert "PRODUCT" in step.custom_entity_types
        assert "TECHNOLOGY" in step.custom_entity_types
        assert step.output_format == "structured"
        assert "ai_inference_service" in step.services
    
    def test_entity_extractor_step_minimal_initialization(self, minimal_entity_extractor_config):
        """Test initialization with minimal configuration."""
        step = EntityExtractorStep(minimal_entity_extractor_config)
        
        assert step.chunk_field_to_extract_entities_from == "text"
        assert step.output_field_name == "extracted_entities"
        assert step.extract_people is True  # default
        assert step.extract_places is True  # default
        assert step.temperature == 0.1  # default
    
    def test_entity_extractor_step_missing_prompts(self):
        """Test EntityExtractorStep initialization with missing prompts."""
        config = StepInstanceConfig(
            step_catalog_id="entity_extractor",
            name="entity_extractor_instance",
            settings={}  # Missing prompts
        )
        
        with pytest.raises(StepExecutionError) as exc_info:
            EntityExtractorStep(config)
        
        assert "No prompts found in settings" in str(exc_info.value)
    
    def test_entity_extractor_step_missing_system_prompt(self):
        """Test EntityExtractorStep initialization with missing system prompt uses default."""
        config = StepInstanceConfig(
            step_catalog_id="entity_extractor",
            name="entity_extractor_instance",
            settings={
                "prompts": {
                    "user": "Extract entities"
                    # Missing system prompt - should use default
                }
            }
        )
        
        step = EntityExtractorStep(config)
        
        # Should use default system prompt
        assert step.system_prompt is not None
        assert len(step.system_prompt) > 0
        assert "entity extraction" in step.system_prompt.lower()
    
    def test_entity_extractor_step_missing_user_prompt(self):
        """Test EntityExtractorStep initialization with missing user prompt uses default."""
        config = StepInstanceConfig(
            step_catalog_id="entity_extractor",
            name="entity_extractor_instance",
            settings={
                "prompts": {
                    "system": "You are an entity extractor"
                    # Missing user prompt - should use default
                }
            }
        )
        
        step = EntityExtractorStep(config)
        
        # Should use default user prompt
        assert step.user_prompt is not None
        assert len(step.user_prompt) > 0
        assert "{chunk_content}" in step.user_prompt
    
    def test_entity_extractor_step_invalid_chunk_field(self):
        """Test EntityExtractorStep initialization with missing chunk field."""
        config = StepInstanceConfig(
            step_catalog_id="entity_extractor",
            name="entity_extractor_instance",
            settings={
                "chunk_field_to_extract_entities_from": "",  # Empty field
                "prompts": {
                    "system": "System",
                    "user": "User"
                }
            }
        )
        
        with pytest.raises(ValueError) as exc_info:
            EntityExtractorStep(config)
        
        assert "Chunk field to extract entities from not found" in str(exc_info.value)
    
    def test_entity_extractor_step_invalid_output_field(self):
        """Test EntityExtractorStep initialization with missing output field."""
        config = StepInstanceConfig(
            step_catalog_id="entity_extractor",
            name="entity_extractor_instance",
            settings={
                "output_field_name": "",  # Empty field
                "prompts": {
                    "system": "System",
                    "user": "User"
                }
            }
        )
        
        with pytest.raises(ValueError) as exc_info:
            EntityExtractorStep(config)
        
        assert "Output field name not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_entity_extractor_step_run_success(self, entity_extractor_config, documents_with_chunks_input, mock_ai_response):
        """Test successful execution of EntityExtractorStep."""
        step = EntityExtractorStep(entity_extractor_config)
        
        # Mock AI inference service
        mock_ai_service = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = mock_ai_response
        mock_ai_service.run_chat_completion.return_value = mock_response
        mock_ai_service.type = 'azure_ai_inference'
        
        # Mock context
        mock_context = MagicMock()
        mock_context.get_service.return_value = mock_ai_service
        
        # Run the step
        result = await step.run(documents_with_chunks_input, mock_context)
        
        # Verify result structure
        assert isinstance(result, StepInputOutput)
        assert result.data is not None
        assert "documents" in result.data
        
        # Verify that entities were extracted and added to chunks
        documents = result.data["documents"]
        for document in documents:
            for chunk in document["chunks"]:
                assert "extracted_entities" in chunk
                entities_data = chunk["extracted_entities"]
                assert isinstance(entities_data, dict)
                assert "entities" in entities_data
                assert "relationships" in entities_data
        
        # Verify statistics
        assert f"{step.name}_stats" in result.summary_data
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 2
        assert stats["successful_documents"] == 2
        assert stats["failed_documents"] == 0
        assert stats["total_entities_extracted"] > 0
    
    @pytest.mark.asyncio
    async def test_entity_extractor_step_no_documents(self, entity_extractor_config):
        """Test EntityExtractorStep with no documents."""
        step = EntityExtractorStep(entity_extractor_config)
        
        # Input with no documents
        input_data = StepInputOutput(
            id="test",
            summary_data={},
            data={"documents": []}
        )
        
        # Mock context
        mock_context = MagicMock()
        mock_ai_service = MagicMock()
        mock_ai_service.type = 'azure_ai_inference'
        mock_context.get_service.return_value = mock_ai_service
        
        result = await step.run(input_data, mock_context)
        
        # Should return early with zero stats
        stats = result.summary_data[f"{step.name}_stats"]
        assert stats["total_documents"] == 0
        assert stats["successful_documents"] == 0
    
    @pytest.mark.asyncio
    async def test_entity_extractor_step_invalid_input(self, entity_extractor_config):
        """Test EntityExtractorStep with invalid input."""
        step = EntityExtractorStep(entity_extractor_config)
        
        # Mock context
        mock_context = MagicMock()
        
        # Test with None input
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(None, mock_context)
        assert "Invalid input data" in str(exc_info.value)
        
        # Test with invalid input structure
        invalid_input = MagicMock()
        invalid_input.data = None
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(invalid_input, mock_context)
        assert "Invalid input data" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_entity_extractor_step_no_ai_service(self, entity_extractor_config, documents_with_chunks_input):
        """Test EntityExtractorStep with no AI service available."""
        step = EntityExtractorStep(entity_extractor_config)
        
        # Mock context with no AI service
        mock_context = MagicMock()
        mock_context.get_service.return_value = None
        
        with pytest.raises(StepExecutionError) as exc_info:
            await step.run(documents_with_chunks_input, mock_context)
        
        assert "Azure AI Model Inference Service not found" in str(exc_info.value)
    
    def test_parse_extraction_response_valid_json(self, entity_extractor_config, mock_ai_response):
        """Test parsing valid JSON response."""
        step = EntityExtractorStep(entity_extractor_config)
        
        result = step.parse_extraction_response(mock_ai_response)
        
        assert isinstance(result, dict)
        assert "entities" in result
        assert "relationships" in result
        assert len(result["entities"]) == 3
        assert len(result["relationships"]) == 2
    
    def test_parse_extraction_response_json_in_markdown(self, entity_extractor_config):
        """Test parsing JSON wrapped in markdown code blocks."""
        step = EntityExtractorStep(entity_extractor_config)
        
        markdown_response = '''```json
        {
            "entities": [{"text": "Test", "type": "PERSON", "confidence": 8}],
            "relationships": []
        }
        ```'''
        
        result = step.parse_extraction_response(markdown_response)
        
        assert isinstance(result, dict)
        assert "entities" in result
        assert len(result["entities"]) == 1
        assert result["entities"][0]["text"] == "Test"
    
    def test_parse_extraction_response_invalid_json(self, entity_extractor_config):
        """Test parsing invalid JSON response."""
        step = EntityExtractorStep(entity_extractor_config)
        
        invalid_response = "This is not valid JSON"
        
        result = step.parse_extraction_response(invalid_response)
        
        assert isinstance(result, dict)
        assert result == {"entities": [], "relationships": []}
    
    def test_filter_entities_by_type(self, entity_extractor_config):
        """Test filtering entities by configured types."""
        step = EntityExtractorStep(entity_extractor_config)
        
        entities = [
            {"text": "John", "type": "PERSON"},
            {"text": "TechCorp", "type": "ORGANIZATION"},
            {"text": "iPhone", "type": "PRODUCT"},  # Custom type
            {"text": "Unknown", "type": "UNKNOWN"}  # Not configured
        ]
        
        filtered = step.filter_entities_by_type(entities)
        
        # Should include PERSON, ORGANIZATION, and PRODUCT (custom type)
        assert len(filtered) == 3
        types = [entity["type"] for entity in filtered]
        assert "PERSON" in types
        assert "ORGANIZATION" in types
        assert "PRODUCT" in types
        assert "UNKNOWN" not in types
    
    def test_deduplicate_entities(self, entity_extractor_config):
        """Test entity deduplication."""
        step = EntityExtractorStep(entity_extractor_config)
        
        entities = [
            {"text": "John Smith", "type": "PERSON", "confidence": 9},
            {"text": "john smith", "type": "PERSON", "confidence": 8},  # Duplicate (case insensitive)
            {"text": "TechCorp", "type": "ORGANIZATION", "confidence": 10},
            {"text": "TechCorp", "type": "ORGANIZATION", "confidence": 9}  # Exact duplicate
        ]
        
        deduplicated = step.deduplicate_entities(entities)
        
        # Should remove duplicates
        assert len(deduplicated) == 2
        texts = [entity["text"] for entity in deduplicated]
        assert "John Smith" in texts
        assert "TechCorp" in texts
    
    def test_enhance_entities_with_metadata(self, entity_extractor_config):
        """Test enhancing entities with chunk metadata."""
        step = EntityExtractorStep(entity_extractor_config)
        
        entities = [
            {"text": "John Smith", "type": "PERSON", "confidence": 9}
        ]
        
        chunk = {
            "chunk_id": "test_chunk_123",
            "chunk_num": 5,
            "input_file_path": "/test/document.pdf",
            "page_num": 3
        }
        
        enhanced = step.enhance_entities_with_metadata(entities, chunk)
        
        assert len(enhanced) == 1
        entity = enhanced[0]
        assert entity["source_chunk_id"] == "test_chunk_123"
        assert entity["source_chunk_num"] == 5
        assert entity["source_file"] == "/test/document.pdf"
        assert entity["page_num"] == 3
    
    def test_get_default_system_prompt(self, entity_extractor_config):
        """Test generation of default system prompt."""
        step = EntityExtractorStep(entity_extractor_config)
        
        prompt = step._get_default_system_prompt()
        
        assert isinstance(prompt, str)
        assert "PERSON" in prompt
        assert "PLACE" in prompt
        assert "ORGANIZATION" in prompt
        assert "PRODUCT" in prompt  # Custom type
        assert "TECHNOLOGY" in prompt  # Custom type
        assert "relationships" in prompt.lower()
        assert "JSON" in prompt
    
    def test_get_default_user_prompt(self, entity_extractor_config):
        """Test generation of default user prompt."""
        step = EntityExtractorStep(entity_extractor_config)
        
        prompt = step._get_default_user_prompt()
        
        assert isinstance(prompt, str)
        assert "{chunk_content}" in prompt
        assert "JSON" in prompt
