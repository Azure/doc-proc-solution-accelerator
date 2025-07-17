# Test Suite for doc-proc-lib

This directory contains comprehensive tests for the document processing library. The tests are organized in a structured manner to ensure maintainability and easy navigation.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and configuration
├── step/                          # Tests for pipeline steps
│   ├── __init__.py
│   ├── test_step_base.py         # Base step class tests
│   ├── test_sample_step.py       # Sample step implementation tests
│   ├── test_pdf_text_extractor.py    # PDF text extraction step tests
│   ├── test_word_text_extractor.py   # Word document extraction step tests
│   ├── test_pptx_text_extractor.py   # PowerPoint extraction step tests
│   └── test_document_type_identifier.py  # Document type identification tests
├── service/                       # Tests for services
│   ├── __init__.py
│   ├── test_service_base.py      # Base service class tests
│   ├── test_sample_service.py    # Sample service implementation tests
│   └── test_azure_ai_inference_service.py  # Azure AI service tests
├── pipeline/                      # Tests for pipeline components
│   ├── __init__.py
│   └── test_pipeline_base.py     # Pipeline base classes tests
|   └── test_pipeline_config.py   # Pipeline config classes tests
└── utils/                         # Tests for utility functions
    ├── __init__.py
    ├── test_import_module.py      # Module import utility tests
    └── test_secure_condition_evaluator.py  # Condition evaluator tests
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

Or use the test runner:
```bash
python run_tests.py --install-deps
```

### Basic Test Execution

Run all tests:
```bash
pytest tests/
```

Or use the test runner:
```bash
python run_tests.py
```

### Component-Specific Tests

Run tests for specific components:

```bash
# Step tests
pytest tests/step/
python run_tests.py --component step

# Service tests
pytest tests/service/
python run_tests.py --component service

# Pipeline tests
pytest tests/pipeline/
python run_tests.py --component pipeline

# Utility tests
pytest tests/utils/
python run_tests.py --component utils
```

### Specific Test Files

Run tests for a specific file:
```bash
pytest tests/step/test_pdf_text_extractor.py
python run_tests.py --file tests/step/test_pdf_text_extractor.py
```

### Test Categories

Tests are marked with categories:

```bash
# Unit tests only
pytest -m unit
python run_tests.py --unit

# Integration tests only
pytest -m integration
python run_tests.py --integration

# Slow tests
pytest -m slow

# Tests requiring external services
pytest -m external
```

### Pattern Matching

Run tests matching a specific pattern:
```bash
pytest -k "test_initialization"
python run_tests.py --pattern "test_initialization"
```

### Coverage Reports

Generate test coverage reports:
```bash
pytest --cov=doc --cov-report=html --cov-report=term
python run_tests.py --coverage
```

## Test Organization

### Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `sample_step_config`: Standard step configuration for testing
- `sample_step_input`: Sample step input data
- `mock_service`: Mock service for testing
- `mock_pipeline_context`: Mock pipeline execution context
- `sample_document_data`: Sample document data for testing
- Service-specific settings fixtures for Azure services

### Test Categories by Component

#### Step Tests (`tests/step/`)

- **Base functionality**: Tests for `StepBase` class, `StepInstanceConfig`, and `StepInputOutput`
- **Text extractors**: Tests for PDF, Word, and PowerPoint text extraction steps
- **Document processing**: Tests for document type identification and processing
- **Error handling**: Tests for various error conditions and edge cases
- **Mocking**: External dependencies are mocked for isolated testing

#### Service Tests (`tests/service/`)

- **Base functionality**: Tests for `ServiceBase` class and common service patterns
- **Azure services**: Tests for Azure AI Inference, Blob Storage, and AI Search services
- **Connection testing**: Tests for service connectivity and configuration validation
- **Error scenarios**: Tests for connection failures and invalid configurations

#### Pipeline Tests (`tests/pipeline/`)

- **Execution context**: Tests for pipeline execution context and service management
- **Result models**: Tests for step and pipeline execution result models
- **Data flow**: Tests for data flow between pipeline components

#### Utility Tests (`tests/utils/`)

- **Module imports**: Tests for dynamic module loading and class instantiation
- **Condition evaluation**: Tests for secure condition evaluation logic
- **Helper functions**: Tests for various utility functions

## Test Patterns and Best Practices

### Naming Conventions

- Test files: `test_<component_name>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<specific_functionality>`

### Async Testing

For async methods, use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_method(self):
    result = await some_async_method()
    assert result is not None
```

### Mocking External Dependencies

Use `unittest.mock` for mocking external dependencies:

```python
@patch('module.external_dependency')
async def test_with_mocked_dependency(self, mock_dependency):
    mock_dependency.return_value = "mocked_result"
    # Test code here
```

### Test Data Management

- Use fixtures for reusable test data
- Create minimal test data that covers the test scenario
- Use factories for generating multiple similar test objects

### Error Testing

Test both success and failure scenarios:

```python
def test_success_case(self):
    # Test successful execution
    pass

def test_failure_case(self):
    with pytest.raises(SpecificException):
        # Test that specific exception is raised
        pass
```

## Adding New Tests

### For New Steps

1. Create `test_<step_name>.py` in `tests/step/`
2. Include tests for:
   - Initialization with various configurations
   - Successful execution with sample data
   - Error handling (invalid input, missing services, etc.)
   - Edge cases (empty documents, malformed data, etc.)

### For New Services

1. Create `test_<service_name>.py` in `tests/service/`
2. Include tests for:
   - Initialization with valid/invalid settings
   - Connection testing
   - Service-specific operations
   - Error scenarios

### For New Pipeline Components

1. Create tests in `tests/pipeline/`
2. Focus on:
   - Data flow and transformations
   - Error propagation
   - Context management

### For New Utilities

1. Create tests in `tests/utils/`
2. Cover:
   - All public functions
   - Edge cases and error conditions
   - Input validation

## Continuous Integration

The test suite is designed to work with CI/CD pipelines. Key considerations:

- All external dependencies are mocked
- Tests run in isolation
- No external services required
- Fast execution for frequent runs
- Comprehensive coverage reporting

## Test Maintenance

- Update tests when adding new features
- Maintain backward compatibility in test interfaces
- Regular review of test coverage
- Refactor tests along with production code
- Keep test data updated with schema changes
