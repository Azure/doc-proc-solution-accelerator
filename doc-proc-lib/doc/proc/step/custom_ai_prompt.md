# Custom AI Prompt Step Documentation

## Overview

The Custom AI Prompt step is a versatile and powerful component of the document processing pipeline that applies custom AI prompts to document content. This step enables users to perform specialized AI-powered analysis, transformation, and enhancement of document chunks using configurable prompts and Azure AI Inference services.

## Step Information

- **Step ID**: `custom_ai_prompt`
- **Step Name**: Custom AI Prompt Step
- **Category**: AI Processing
- **Version**: 1.0
- **Module**: `doc.proc.step.custom_ai_prompt`
- **Class**: `CustomAIPromptStep`

## Description

The Custom AI Prompt step processes document chunks by applying user-defined AI prompts to specific fields within each chunk. It provides complete flexibility in prompt design and can be configured to perform various AI-powered tasks such as summarization, analysis, translation, classification, or content enhancement. The step supports template-based prompts with dynamic content substitution.

### Key Features

- **Flexible Prompt Configuration**: Define custom system and user prompts for specific use cases
- **Dynamic Content Substitution**: Use template variables to inject chunk content into prompts
- **Configurable Input/Output Fields**: Specify which fields to process and where to store results
- **AI Model Parameter Control**: Full control over AI model parameters (temperature, top_p, etc.)
- **Batch Processing**: Process multiple documents and chunks efficiently
- **Error Handling**: Robust error handling with skip-on-failure options
- **Debug Mode**: Comprehensive logging for prompt engineering and troubleshooting
- **Service Integration**: Seamless integration with Azure AI Inference services

## Use Cases

### 1. Content Summarization
Generate concise summaries of document sections or entire documents.

**Example Scenario**: A research organization processes academic papers to generate executive summaries for each section, enabling quick literature reviews and research synthesis.

### 2. Document Classification and Tagging
Classify document content and assign relevant tags or categories.

**Example Scenario**: A legal firm automatically categorizes contract clauses by type (liability, payment terms, termination) and assigns risk ratings to each clause.

### 3. Sentiment and Tone Analysis
Analyze the sentiment, tone, and emotional content of documents.

**Example Scenario**: A customer service team analyzes customer feedback documents to identify sentiment patterns, satisfaction levels, and areas for improvement.

### 4. Language Translation
Translate document content between different languages.

**Example Scenario**: A multinational corporation processes internal documents in multiple languages, automatically translating content to ensure global accessibility.

### 5. Content Enhancement and Enrichment
Enhance document content with additional information, explanations, or context.

**Example Scenario**: A training organization processes technical manuals to add simplified explanations, glossary terms, and practical examples for different skill levels.

### 6. Data Extraction and Structuring
Extract specific information from unstructured text and format it consistently.

**Example Scenario**: An insurance company processes claim documents to extract key information like dates, amounts, parties involved, and incident details into structured data fields.

### 7. Quality Assessment and Validation
Assess the quality, accuracy, or completeness of document content.

**Example Scenario**: A publishing company uses AI to review manuscript chapters for consistency, fact-checking, and adherence to style guidelines.

### 8. Comparative Analysis
Compare document content against standards, templates, or other documents.

**Example Scenario**: A compliance team compares policy documents against regulatory requirements to identify gaps and ensure adherence to legal standards.

## Prerequisites

### Required Services

1. **Azure AI Inference Service**: A configured Azure AI service for prompt processing and content generation

### Input Data Requirements

The step expects input data in the following structure:

```json
{
  "documents": [
    {
      "chunks": [
        {
          "page_id": "unique_identifier",
          "page_num": 1,
          "markdown_text": "content_to_process",
          "markdown": "full_markdown_content"
        }
      ]
    }
  ]
}
```

## Configuration

### Required Settings

#### AI Inference Service
- **Parameter**: `ai_model_inference_service`
- **Type**: String
- **Description**: Reference to the Azure AI Inference service instance
- **Required**: Yes
- **UI Component**: Service Selector (azure_ai_inference)

### Processing Configuration

#### Field to Apply Prompt On
- **Parameter**: `chunk_field_to_apply_prompt_on`
- **Type**: String
- **Description**: The field key in document.chunks.chunk which the AI prompt will be applied to
- **Required**: No
- **Default**: `markdown_text`
- **UI Component**: Input

#### Output Field Name
- **Parameter**: `output_field_name`
- **Type**: String
- **Description**: Field name in document.chunks.chunk to store the AI response
- **Required**: No
- **Default**: `custom_ai_prompt_output`
- **UI Component**: Input

### Prompt Configuration

#### System Prompt
- **Parameter**: `system_prompt`
- **Type**: String
- **Description**: Instructions for the AI system that define its role and behavior
- **Required**: No
- **Default**: `You are an AI assistant.`
- **UI Component**: Textarea

#### User Prompt Template
- **Parameter**: `user_prompt`
- **Type**: String
- **Description**: Template for the custom user prompts sent to AI
- **Required**: No
- **Default**: `This is a custom AI prompt step. Please process the input accordingly.\nInput: {chunk_content}`
- **UI Component**: Textarea

### AI Model Parameters

#### Max Completion Tokens
- **Parameter**: `max_completion_tokens`
- **Type**: Integer
- **Description**: Maximum number of tokens to generate
- **Required**: No
- **Default**: `4000`
- **Range**: `100` to `8000`

#### Temperature
- **Parameter**: `temperature`
- **Type**: Number
- **Description**: Controls randomness in AI responses (0.0 = deterministic, 2.0 = very random)
- **Required**: No
- **Default**: `1.0`
- **Range**: `0.0` to `2.0`
- **Step**: `0.1`

#### Top P
- **Parameter**: `top_p`
- **Type**: Number
- **Description**: Controls diversity of AI responses
- **Required**: No
- **Default**: `0.4`
- **Range**: `0.0` to `1.0`
- **Step**: `0.1`

#### Frequency Penalty
- **Parameter**: `frequency_penalty`
- **Type**: Number
- **Description**: Reduces repetition in AI responses
- **Required**: No
- **Default**: `0.0`
- **Range**: `-2.0` to `2.0`
- **Step**: `0.1`

#### Presence Penalty
- **Parameter**: `presence_penalty`
- **Type**: Number
- **Description**: Encourages AI to talk about new topics
- **Required**: No
- **Default**: `0.0`
- **Range**: `-2.0` to `2.0`
- **Step**: `0.1`

### Step Configuration Example

```yaml
steps:
  - name: summarize_content
    step_catalog_id: custom_ai_prompt
    services: [primary_ai_inference_service]
    settings:
      ai_model_inference_service: "primary_ai_inference_service"
      chunk_field_to_apply_prompt_on: "markdown_text"
      output_field_name: "summary"
      system_prompt: "You are an expert summarization assistant. Create concise, accurate summaries that capture the key points and main ideas."
      user_prompt: |
        Please provide a comprehensive summary of the following text. Focus on the main ideas, key findings, and important details.
        
        Text to summarize:
        {chunk_content}
        
        Summary:
      max_completion_tokens: 2000
      temperature: 0.3
      top_p: 0.8
      frequency_penalty: 0.1
      presence_penalty: 0.0
```

## Service Configuration

### Azure AI Inference Service

The step requires a configured Azure AI Inference service:

```yaml
services:
  - name: primary_ai_inference_service
    service_catalog_id: azure_ai_inference_service_01
    settings:
      endpoint: "https://your-ai-service.cognitiveservices.azure.com/"
      api_key: "your-api-key"
      model_name: "gpt-4"
      api_version: "2024-02-01"
```

## Prompt Engineering

### Template Variables

The step supports template variables in the user prompt:

- **{chunk_content}**: Replaced with the content of the specified input field
- **Custom Variables**: Additional variables can be added based on chunk structure

### Prompt Design Patterns

#### 1. Template-Based Prompts
Use the `{chunk_content}` placeholder for dynamic content injection:

```yaml
user_prompt: |
  Analyze the following document section and provide insights:
  
  Document Section:
  {chunk_content}
  
  Analysis:
```

#### 2. Instruction-Based Prompts
Provide clear instructions without placeholders:

```yaml
user_prompt: |
  Please summarize the key points from the provided text.
  Focus on actionable insights and important findings.
  
  Text Content:
```

#### 3. Structured Output Prompts
Request specific output formats:

```yaml
user_prompt: |
  Extract key information from the following text and format as JSON:
  
  {
    "main_topic": "primary subject",
    "key_points": ["point 1", "point 2", "point 3"],
    "sentiment": "positive/negative/neutral",
    "confidence": "high/medium/low"
  }
  
  Text:
  {chunk_content}
```

### Advanced Prompt Examples

#### Content Summarization
```yaml
system_prompt: "You are a professional summarization expert. Create clear, concise summaries that preserve the most important information."
user_prompt: |
  Create a bullet-point summary of the following content. Include:
  - Main topic or theme
  - Key findings or conclusions
  - Important details or data points
  - Any recommendations or next steps mentioned
  
  Content to summarize:
  {chunk_content}
```

#### Document Classification
```yaml
system_prompt: "You are a document classification expert. Categorize documents based on their content and structure."
user_prompt: |
  Analyze the following document excerpt and classify it into one of these categories:
  - Legal Contract
  - Financial Report
  - Technical Documentation
  - Marketing Material
  - Academic Paper
  - Other (specify)
  
  Also provide:
  - Confidence level (High/Medium/Low)
  - Key indicators that support your classification
  - Document subtype if applicable
  
  Document excerpt:
  {chunk_content}
```

#### Sentiment Analysis
```yaml
system_prompt: "You are a sentiment analysis expert. Analyze text for emotional tone, sentiment, and attitude."
user_prompt: |
  Analyze the sentiment and tone of the following text. Provide:
  
  1. Overall Sentiment: Positive/Negative/Neutral (with confidence %)
  2. Emotional Tone: (e.g., formal, casual, urgent, optimistic, concerned)
  3. Key Phrases: Words or phrases that indicate sentiment
  4. Context: Brief explanation of why you reached this conclusion
  
  Text to analyze:
  {chunk_content}
```

#### Data Extraction
```yaml
system_prompt: "You are a data extraction specialist. Extract specific information from unstructured text and format it consistently."
user_prompt: |
  Extract the following information from the text and format as JSON:
  
  {
    "dates": ["list of dates mentioned"],
    "names": ["list of person names"],
    "organizations": ["list of organizations"],
    "locations": ["list of locations"],
    "amounts": ["list of monetary amounts"],
    "key_terms": ["list of important terms or concepts"]
  }
  
  If any category has no relevant information, use an empty array.
  
  Text:
  {chunk_content}
```

#### Quality Assessment
```yaml
system_prompt: "You are a content quality assessor. Evaluate document quality based on clarity, completeness, and accuracy."
user_prompt: |
  Assess the quality of the following text content and provide:
  
  1. Quality Score: 1-10 scale
  2. Strengths: What makes this content effective
  3. Weaknesses: Areas that need improvement
  4. Recommendations: Specific suggestions for enhancement
  5. Readability: Assessment of how easy it is to understand
  
  Content to assess:
  {chunk_content}
```

## Processing Workflow

### Step 1: Input Validation
1. **Data Structure Check**: Verify input data format and structure
2. **Field Validation**: Ensure required fields are present in chunks
3. **Service Availability**: Confirm AI inference service is available

### Step 2: Prompt Preparation
1. **Template Processing**: Replace template variables with actual content
2. **Message Construction**: Build system and user messages
3. **Parameter Validation**: Verify AI model parameters are within valid ranges

### Step 3: AI Processing
1. **API Call**: Send prompt to Azure AI Inference service
2. **Response Processing**: Extract and validate AI response
3. **Output Storage**: Store response in specified output field

### Step 4: Result Compilation
1. **Chunk Update**: Add AI response to chunk data
2. **Statistics Tracking**: Update processing statistics
3. **Error Handling**: Handle and log any processing errors

## Output Data Structure

The step produces enhanced document chunks with AI-generated content:

```json
{
  "summary_data": {
    "custom_ai_prompt_stats": {
      "total_documents": 1,
      "successful_documents": 1,
      "failed_documents": 0
    }
  },
  "data": {
    "documents": [
      {
        "chunks": [
          {
            "page_id": "unique_identifier",
            "page_num": 1,
            "markdown_text": "original_content",
            "markdown": "full_markdown_content",
            "custom_ai_prompt_output": "ai_generated_response"
          }
        ]
      }
    ]
  }
}
```

### Output Fields Description

| Field | Type | Description |
|-------|------|-------------|
| Original Fields | Various | All original chunk fields are preserved |
| `{output_field_name}` | String | AI-generated response based on the custom prompt |

## Error Handling

### Error Types

1. **Configuration Errors**: Missing or invalid service configurations
2. **Data Validation Errors**: Invalid input data structure or missing fields
3. **AI Service Errors**: API limits, authentication failures, model errors
4. **Prompt Processing Errors**: Template variable substitution failures

### Error Handling Configuration

#### Fail on Document Error
- **Setting**: `fail_step_on_document_error`
- **Default**: `false`
- **Description**: Whether to fail the entire step if a single document fails

#### Retry Configuration
- **Retry on Failure**: `true`
- **Retry Count**: `3`
- **Timeout**: `600` seconds

### Common Error Scenarios

#### 1. Missing Input Field
```
Warning: Chunk field 'markdown_text' not found in chunk
```
**Solution**: Verify the field name matches your document structure

#### 2. Empty Content
```
Warning: The value is not a string or is empty. Skipping this chunk.
```
**Solution**: Ensure the input field contains valid text content

#### 3. AI Service Error
```
Error: Azure AI Model Inference Service not found in context
```
**Solution**: Verify service configuration and availability

#### 4. Template Variable Error
```
Error: Template variable substitution failed
```
**Solution**: Check that all template variables are properly defined

### Error Recovery

The step implements graceful error handling:

1. **Chunk-Level Recovery**: If one chunk fails, processing continues with remaining chunks
2. **Empty Response Handling**: Sets empty string for failed chunks
3. **Warning Logs**: Logs warnings for non-critical issues
4. **Statistics Tracking**: Tracks success/failure rates for monitoring

## Performance Optimization

### Processing Efficiency

#### Factors Affecting Performance

1. **Prompt Complexity**: More complex prompts require more processing time
2. **Content Length**: Longer input content increases processing time
3. **AI Model Parameters**: Higher token limits and complex parameters affect speed
4. **Batch Size**: Number of chunks processed simultaneously

#### Optimization Strategies

1. **Prompt Optimization**: Use clear, concise prompts for better performance
2. **Content Filtering**: Pre-filter content to avoid processing empty or irrelevant chunks
3. **Parameter Tuning**: Optimize AI model parameters for your specific use case
4. **Batch Processing**: Process multiple documents in parallel when possible

### Resource Management

#### Memory Considerations

- **Prompt Size**: Large prompts consume more memory
- **Response Size**: Longer AI responses use more memory
- **Batch Size**: Processing many chunks simultaneously increases memory usage

#### Token Management

- **Input Tokens**: Monitor input token usage to stay within limits
- **Output Tokens**: Set appropriate max_completion_tokens for your use case
- **Cost Optimization**: Balance quality with token usage costs

## Integration Examples

### Complete Pipeline Example

```yaml
pipeline:
  name: "Document Analysis and Enhancement Pipeline"
  description: "Extract text, summarize, and analyze document content"
  
  services:
    - name: primary_ai_inference_service
      service_catalog_id: azure_ai_inference_service_01
      settings:
        endpoint: "https://myaiservice.cognitiveservices.azure.com/"
        api_key: "your-api-key"
        model_name: "gpt-4"
        
    - name: primary_ai_search_service
      service_catalog_id: azure_ai_search_service_01
      settings:
        account_name: "mysearchservice"
        api_key: "your-search-api-key"
        index_name: "documents-index"
  
  steps:
    - name: extract_pdf_text
      step_catalog_id: pdf_text_extractor
      services: [primary_ai_inference_service]
      settings:
        ai_model_inference_service: "primary_ai_inference_service"
        png_output_folder: "./output/png"
        
    - name: summarize_content
      step_catalog_id: custom_ai_prompt
      services: [primary_ai_inference_service]
      settings:
        ai_model_inference_service: "primary_ai_inference_service"
        chunk_field_to_apply_prompt_on: "markdown_text"
        output_field_name: "summary"
        system_prompt: "You are a professional summarization expert."
        user_prompt: |
          Create a concise summary of the following text:
          {chunk_content}
          
    - name: analyze_sentiment
      step_catalog_id: custom_ai_prompt
      services: [primary_ai_inference_service]
      settings:
        ai_model_inference_service: "primary_ai_inference_service"
        chunk_field_to_apply_prompt_on: "markdown_text"
        output_field_name: "sentiment_analysis"
        system_prompt: "You are a sentiment analysis expert."
        user_prompt: |
          Analyze the sentiment of this text and respond with:
          - Sentiment: Positive/Negative/Neutral
          - Confidence: High/Medium/Low
          - Key indicators: Brief explanation
          
          Text: {chunk_content}
        
    - name: index_documents
      step_catalog_id: ai_search_index_writer
      services: [primary_ai_search_service]
      settings:
        ai_search_service: "primary_ai_search_service"
        index_name: "documents-index"
        index_field_mappings: |
          {
            "page_id": "id",
            "markdown_text": "content",
            "summary": "summary",
            "sentiment_analysis": "sentiment"
          }
```

### Multi-Step Analysis Pipeline

```yaml
pipeline:
  name: "Comprehensive Document Analysis"
  description: "Multi-step analysis with classification, summarization, and extraction"
  
  steps:
    - name: classify_document
      step_catalog_id: custom_ai_prompt
      services: [primary_ai_inference_service]
      settings:
        chunk_field_to_apply_prompt_on: "markdown_text"
        output_field_name: "classification"
        system_prompt: "You are a document classification expert."
        user_prompt: |
          Classify this document excerpt into one of these categories:
          - Legal, Financial, Technical, Marketing, Academic, Other
          
          Content: {chunk_content}
          
          Response format: Category | Confidence | Key Indicators
          
    - name: extract_key_info
      step_catalog_id: custom_ai_prompt
      services: [primary_ai_inference_service]
      settings:
        chunk_field_to_apply_prompt_on: "markdown_text"
        output_field_name: "key_info"
        system_prompt: "You are a data extraction specialist."
        user_prompt: |
          Extract key information as JSON:
          {
            "main_topics": ["topic1", "topic2"],
            "key_dates": ["date1", "date2"],
            "important_figures": ["name1", "name2"],
            "action_items": ["item1", "item2"]
          }
          
          Text: {chunk_content}
          
    - name: quality_assessment
      step_catalog_id: custom_ai_prompt
      services: [primary_ai_inference_service]
      settings:
        chunk_field_to_apply_prompt_on: "markdown_text"
        output_field_name: "quality_score"
        system_prompt: "You are a content quality assessor."
        user_prompt: |
          Rate the quality of this content (1-10) and provide:
          - Score: X/10
          - Strengths: What works well
          - Improvements: What could be better
          
          Content: {chunk_content}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Template Variable Not Replaced

**Symptoms**: `{chunk_content}` appears in AI response
**Causes**: 
- Missing template variable in user prompt
- Field name mismatch

**Solutions**:
- Verify template variable syntax: `{chunk_content}`
- Check that input field contains valid content
- Ensure field name matches document structure

#### 2. Empty or Poor Quality Responses

**Symptoms**: AI generates empty or irrelevant responses
**Causes**:
- Unclear or ambiguous prompts
- Inappropriate AI model parameters
- Insufficient context in system prompt

**Solutions**:
- Refine system and user prompts for clarity
- Adjust temperature and top_p parameters
- Provide more specific instructions and examples

#### 3. Inconsistent Response Format

**Symptoms**: AI responses vary in format despite structured prompts
**Causes**:
- High temperature settings
- Ambiguous formatting instructions
- Model variability

**Solutions**:
- Lower temperature for more consistent responses
- Provide clear formatting examples
- Use more explicit formatting instructions

#### 4. Processing Timeouts

**Symptoms**: Step times out during processing
**Causes**:
- Large content chunks
- High token limits
- Complex prompts

**Solutions**:
- Reduce max_completion_tokens
- Simplify prompts
- Increase timeout settings

### Debug Mode

Enable debug mode for detailed logging:

```yaml
steps:
  - name: custom_analysis
    step_catalog_id: custom_ai_prompt
    debug_mode: true
    # ... other settings
```

Debug mode provides:
- Detailed prompt and response logging
- Processing statistics for each chunk
- Error details and stack traces
- Performance metrics

## Best Practices

### 1. Prompt Engineering

- **Be Specific**: Use clear, specific instructions rather than vague requests
- **Provide Context**: Include relevant context in system prompts
- **Use Examples**: Provide examples of desired output format
- **Test Iteratively**: Refine prompts based on actual results
- **Consider Edge Cases**: Handle empty content, unusual formats, etc.

### 2. Parameter Optimization

- **Temperature**: Use lower values (0.1-0.3) for consistent, factual responses
- **Top P**: Use 0.8-1.0 for creative tasks, 0.4-0.6 for analytical tasks
- **Token Limits**: Set appropriate limits based on expected response length
- **Penalties**: Use frequency penalty to reduce repetition

### 3. Error Handling Strategy

- **Graceful Degradation**: Continue processing when individual chunks fail
- **Meaningful Defaults**: Set appropriate default values for failed processing
- **Comprehensive Logging**: Log all processing steps for troubleshooting
- **Monitoring**: Track success rates and response quality

### 4. Performance Optimization

- **Batch Processing**: Process multiple documents efficiently
- **Content Filtering**: Skip empty or irrelevant content
- **Resource Monitoring**: Monitor token usage and costs
- **Caching**: Consider caching common responses

### 5. Security and Privacy

- **Data Sensitivity**: Be aware of sensitive information in prompts
- **API Key Management**: Securely manage AI service credentials
- **Content Filtering**: Implement appropriate content filters
- **Audit Trails**: Maintain logs for compliance and debugging

## Security Considerations

### Data Privacy

- **Sensitive Content**: Ensure appropriate handling of confidential information
- **Data Residency**: Verify AI service data residency requirements
- **Content Logging**: Be cautious about logging sensitive prompt content
- **Access Controls**: Implement proper access controls for AI services

### Prompt Security

- **Prompt Injection**: Validate and sanitize user inputs
- **Template Security**: Ensure template variables are properly escaped
- **Content Validation**: Validate AI responses before storing
- **Error Information**: Avoid exposing sensitive information in error messages

## Monitoring and Maintenance

### Key Metrics

- **Processing Success Rate**: Percentage of successfully processed chunks
- **Response Quality**: Subjective assessment of AI response quality
- **Token Usage**: Monitor input and output token consumption
- **Processing Time**: Average time per chunk/document
- **Error Rate**: Frequency of different error types

### Maintenance Tasks

- **Prompt Optimization**: Regularly review and refine prompts
- **Parameter Tuning**: Adjust AI model parameters based on results
- **Performance Monitoring**: Track processing metrics and costs
- **Quality Assessment**: Periodically evaluate AI response quality

### Cost Management

- **Token Monitoring**: Track and optimize token usage
- **Prompt Efficiency**: Design prompts for optimal token usage
- **Batch Optimization**: Process documents efficiently to reduce costs
- **Service Tier Selection**: Choose appropriate AI service tiers

## Version History

- **Version 1.0**: Initial release with basic custom prompt functionality
- **Future Versions**: Planned enhancements for:
  - Advanced template variables
  - Multi-turn conversations
  - Response validation
  - Custom output formatting

## Support and Resources

- **Step Implementation**: `doc/proc/step/custom_ai_prompt.py`
- **Step Catalog**: `step_catalog.yaml`
- **Service Catalog**: `service_catalog.yaml`
- **Azure AI Documentation**: [Azure AI Services Documentation](https://docs.microsoft.com/azure/cognitive-services/)
- **Prompt Engineering Guide**: [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- **Pipeline Configuration**: Refer to pipeline configuration documentation
