# Entity Extractor Step Documentation

## Overview

The Entity Extractor step is a specialized AI-powered component of the document processing pipeline that identifies and extracts named entities and their relationships from document content. This step leverages Azure AI Inference services to perform advanced natural language processing (NLP) tasks, enabling automated extraction of people, places, locations, organizations, and custom entity types along with their inter-relationships.

## Step Information

- **Step ID**: `entity_extractor`
- **Step Name**: Entity Extractor Step
- **Category**: AI Processing / NLP
- **Version**: 1.0
- **Module**: `doc.proc.step.entity_extractor`
- **Class**: `EntityExtractorStep`

## Description

The Entity Extractor step processes document chunks by applying sophisticated named entity recognition (NER) and relationship extraction algorithms to identify and extract structured information from unstructured text. It provides configurable entity types, relationship extraction, and flexible output formats for downstream processing and analysis.

### Key Features

- **Configurable Entity Types**: Extract people, places, locations, organizations, and custom entity types
- **Relationship Extraction**: Identify and extract relationships between entities
- **Confidence Scoring**: Provide confidence scores for each extracted entity and relationship
- **Context Preservation**: Include surrounding text context for each extraction
- **Flexible Output Formats**: Support both structured data and JSON output formats
- **Custom Entity Types**: Define and extract domain-specific entity types
- **Batch Processing**: Process multiple documents and chunks efficiently
- **Deduplication**: Automatic removal of duplicate entities
- **Metadata Enhancement**: Enrich entities with source document metadata
- **Error Handling**: Robust error handling with skip-on-failure options
- **Debug Mode**: Comprehensive logging for analysis and troubleshooting

## Use Cases

### 1. Legal Document Analysis
Extract key entities and relationships from legal documents for case analysis and due diligence.

**Example Scenario**: A law firm processes contracts to identify all parties (people and organizations), locations, and their relationships to build a comprehensive understanding of contractual obligations and dependencies.

### 2. Intelligence and Security Analysis
Extract entities and relationships from intelligence reports for threat assessment and network analysis.

**Example Scenario**: A security agency analyzes intelligence reports to identify individuals, organizations, locations, and their relationships to map potential security threats and networks.

### 3. Academic Research and Literature Analysis
Extract research entities and relationships from academic papers for systematic reviews and meta-analyses.

**Example Scenario**: Researchers process hundreds of scientific papers to extract authors, institutions, research locations, and collaboration networks for comprehensive literature mapping.

### 4. Business Intelligence and Market Analysis
Extract business entities and relationships from market reports and business documents.

**Example Scenario**: A consulting firm analyzes market research reports to identify companies, key personnel, market locations, and business relationships for competitive intelligence.

### 5. Healthcare and Medical Records
Extract medical entities and relationships from healthcare documents for clinical analysis.

**Example Scenario**: A healthcare organization processes patient records to extract medical professionals, facilities, treatments, and patient relationships for quality assurance and care coordination.

### 6. Financial Document Processing
Extract financial entities and relationships from financial reports and documents.

**Example Scenario**: A financial institution analyzes regulatory filings to extract companies, executives, financial relationships, and compliance-related entities for risk assessment.

## Configuration

### Required Settings

#### Basic Configuration
- **`chunk_field_to_extract_entities_from`** (string): The field name in the chunk data to extract entities from
  - Default: `"text"`
  - Example: `"markdown_text"`, `"raw_text"`, `"processed_text"`

- **`output_field_name`** (string): The field name where extracted entities will be stored
  - Default: `"extracted_entities"`
  - Example: `"entities"`, `"ner_results"`, `"extracted_data"`

#### Entity Type Configuration
- **`extract_people`** (boolean): Extract person entities (names of individuals)
  - Default: `true`
  - Example: `true`, `false`

- **`extract_places`** (boolean): Extract place entities (geographical locations, cities, countries)
  - Default: `true`
  - Example: `true`, `false`

- **`extract_locations`** (boolean): Extract location entities (addresses, buildings, facilities)
  - Default: `true`
  - Example: `true`, `false`

- **`extract_organizations`** (boolean): Extract organization entities (companies, institutions)
  - Default: `true`
  - Example: `true`, `false`

- **`extract_relationships`** (boolean): Extract relationships between entities
  - Default: `true`
  - Example: `true`, `false`

#### Advanced Configuration
- **`custom_entity_types`** (array): List of custom entity types to extract
  - Default: `[]`
  - Example: `["PRODUCT", "TECHNOLOGY", "EVENT", "REGULATION"]`

- **`output_format`** (string): Format for the output data
  - Default: `"structured"`
  - Options: `"structured"`, `"json"`

- **`include_confidence`** (boolean): Include confidence scores in the output
  - Default: `true`
  - Example: `true`, `false`

- **`include_context`** (boolean): Include surrounding text context for entities
  - Default: `true`
  - Example: `true`, `false`

### AI Model Configuration
- **`max_completion_tokens`** (integer): Maximum tokens for AI response
  - Default: `4000`
  - Range: `100-8000`

- **`temperature`** (float): Controls randomness in AI responses
  - Default: `0.1` (lower for more consistent extraction)
  - Range: `0.0-2.0`

- **`top_p`** (float): Controls diversity of AI responses
  - Default: `1.0`
  - Range: `0.0-1.0`

- **`frequency_penalty`** (float): Reduces repetition in responses
  - Default: `0.0`
  - Range: `-2.0-2.0`

- **`presence_penalty`** (float): Encourages topic diversity
  - Default: `0.0`
  - Range: `-2.0-2.0`

### Prompt Configuration
- **`prompts`** (object): System and user prompts for entity extraction
  - **`system`** (string): System prompt defining extraction instructions
  - **`user`** (string): User prompt template for content processing

## Example Configurations

### Basic Entity Extraction
```yaml
steps:
  - step_catalog_id: "entity_extractor"
    name: "basic_entity_extraction"
    enabled: true
    settings:
      chunk_field_to_extract_entities_from: "text"
      output_field_name: "extracted_entities"
      extract_people: true
      extract_places: true
      extract_locations: true
      extract_organizations: true
      extract_relationships: true
```

### Custom Entity Types for Legal Documents
```yaml
steps:
  - step_catalog_id: "entity_extractor"
    name: "legal_entity_extraction"
    enabled: true
    settings:
      chunk_field_to_extract_entities_from: "markdown_text"
      output_field_name: "legal_entities"
      extract_people: true
      extract_organizations: true
      extract_locations: true
      custom_entity_types: ["CONTRACT", "CLAUSE_TYPE", "LEGAL_REFERENCE", "DATE", "MONETARY_AMOUNT"]
      include_confidence: true
      include_context: true
      prompts:
        system: |
          You are an expert legal entity extraction system. Extract entities and relationships from legal documents.
          Focus on: parties to contracts, legal references, important dates, monetary amounts, and contract types.
        user: |
          Extract entities from this legal text:
          {chunk_content}
```

### Academic Research Entity Extraction
```yaml
steps:
  - step_catalog_id: "entity_extractor"
    name: "research_entity_extraction"
    enabled: true
    settings:
      chunk_field_to_extract_entities_from: "text"
      output_field_name: "research_entities"
      extract_people: true
      extract_organizations: true
      extract_places: true
      custom_entity_types: ["RESEARCH_METHOD", "DATASET", "TECHNOLOGY", "PUBLICATION"]
      extract_relationships: true
      output_format: "structured"
      temperature: 0.1
      prompts:
        system: |
          Extract research-related entities from academic papers.
          Focus on: researchers, institutions, methodologies, datasets, and research relationships.
        user: |
          Analyze this academic text and extract entities:
          {chunk_content}
```

### Financial Document Analysis
```yaml
steps:
  - step_catalog_id: "entity_extractor"
    name: "financial_entity_extraction"
    enabled: true
    settings:
      chunk_field_to_extract_entities_from: "processed_text"
      output_field_name: "financial_entities"
      extract_people: true
      extract_organizations: true
      custom_entity_types: ["FINANCIAL_INSTRUMENT", "CURRENCY", "PERCENTAGE", "REGULATION", "MARKET"]
      include_confidence: true
      max_completion_tokens: 6000
      temperature: 0.05
```

## Output Format

### Structured Output Format
```json
{
  "entities": [
    {
      "text": "John Smith",
      "type": "PERSON",
      "confidence": 9,
      "context": "John Smith, CEO of TechCorp, announced...",
      "start_position": 15,
      "end_position": 25,
      "source_chunk_id": "chunk_hash_123",
      "source_chunk_num": 1,
      "source_file": "/path/to/document.pdf",
      "page_num": 1
    },
    {
      "text": "TechCorp",
      "type": "ORGANIZATION",
      "confidence": 10,
      "context": "John Smith, CEO of TechCorp, announced...",
      "start_position": 35,
      "end_position": 43,
      "source_chunk_id": "chunk_hash_123",
      "source_chunk_num": 1,
      "source_file": "/path/to/document.pdf",
      "page_num": 1
    }
  ],
  "relationships": [
    {
      "entity1": "John Smith",
      "entity2": "TechCorp",
      "relationship": "CEO of",
      "confidence": 9,
      "context": "John Smith, CEO of TechCorp, announced..."
    }
  ]
}
```

### JSON Output Format
Raw JSON string containing the extracted entities and relationships as returned by the AI model.

## Dependencies

### Required Services
- **Azure AI Inference Service**: Required for AI-powered entity extraction
  - Service type: `azure_ai_inference`
  - Used for: Natural language processing and entity recognition

### Python Dependencies
- `azure-ai-inference`: Azure AI inference SDK
- `json`: JSON parsing and formatting
- `re`: Regular expression processing
- `logging`: Logging functionality
- `typing`: Type hints

## Performance Considerations

### Processing Speed
- Entity extraction is computationally intensive
- Processing time depends on:
  - Text length and complexity
  - Number of entity types to extract
  - AI model response time
  - Relationship extraction complexity

### Memory Usage
- Memory consumption scales with:
  - Number of entities extracted
  - Context length preservation
  - Metadata enhancement level

### Optimization Tips
1. **Selective Entity Types**: Only enable entity types needed for your use case
2. **Appropriate Chunk Sizes**: Balance between context and processing efficiency
3. **Temperature Settings**: Use lower temperature (0.1-0.3) for consistent extraction
4. **Batch Processing**: Process documents in batches for optimal throughput
5. **Context Management**: Limit context length for very large documents

## Error Handling

### Common Errors
- **Invalid Input Data**: Missing or malformed chunk data
- **AI Service Unavailable**: Azure AI service connection issues
- **JSON Parsing Errors**: Malformed AI response format
- **Configuration Errors**: Invalid settings or missing required parameters

### Error Recovery
- Automatic fallback to empty entity structure
- Configurable error handling modes
- Detailed error logging for debugging
- Skip-on-failure option for batch processing

## Best Practices

### Prompt Engineering
1. **Clear Instructions**: Provide specific, clear extraction instructions
2. **Example Format**: Include expected output format in system prompt
3. **Domain Context**: Adapt prompts to your specific domain and use case
4. **Confidence Guidelines**: Define clear confidence scoring criteria

### Configuration Optimization
1. **Entity Type Selection**: Only extract relevant entity types
2. **Custom Types**: Define domain-specific entity types for better accuracy
3. **Temperature Tuning**: Use low temperature for consistent extraction
4. **Context Balance**: Balance context inclusion with processing efficiency

### Quality Assurance
1. **Manual Validation**: Regularly validate extraction accuracy
2. **Confidence Thresholds**: Filter results by confidence scores
3. **Deduplication**: Use built-in deduplication for cleaner results
4. **Relationship Validation**: Verify relationship extraction accuracy

## Troubleshooting

### Debug Mode
Enable debug mode to get detailed logging:
```yaml
debug_mode: true
```

### Common Issues
1. **Low Extraction Accuracy**: Adjust prompts and temperature settings
2. **Missing Entities**: Verify entity type configuration and prompts
3. **Duplicate Entities**: Enable deduplication features
4. **Performance Issues**: Optimize chunk sizes and entity type selection

### Monitoring
- Monitor extraction statistics in step output
- Track confidence score distributions
- Analyze entity type coverage
- Review relationship extraction patterns

## Integration Examples

### With PDF Text Extractor
```yaml
pipeline:
  steps:
    - step_catalog_id: "pdf_text_extractor"
      name: "pdf_extraction"
      # ... PDF extraction settings
    
    - step_catalog_id: "entity_extractor"
      name: "entity_extraction"
      settings:
        chunk_field_to_extract_entities_from: "markdown_text"
        output_field_name: "pdf_entities"
        # ... entity extraction settings
```

### With Custom AI Prompt
```yaml
pipeline:
  steps:
    - step_catalog_id: "entity_extractor"
      name: "entity_extraction"
      # ... entity extraction settings
    
    - step_catalog_id: "custom_ai_prompt"
      name: "entity_analysis"
      settings:
        chunk_field_to_apply_prompt_on: "extracted_entities"
        prompts:
          system: "Analyze extracted entities for insights and patterns"
          user: "Provide analysis of these entities: {chunk_content}"
```

## Version History

### Version 1.0
- Initial release
- Support for basic entity types (PERSON, PLACE, LOCATION, ORGANIZATION)
- Relationship extraction capability
- Configurable output formats
- Azure AI Inference integration
- Custom entity type support
- Confidence scoring and context preservation
