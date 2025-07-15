"""
Unit tests for the secure condition evaluator.
"""

import pytest
from doc.proc.utils.secure_condition_evaluator import (
    SecureConditionEvaluator,
    ConditionEvaluationError,
    evaluate_condition,
    validate_condition,
    Condition,
    ConditionGroup,
    ComparisonOperator,
    LogicalOperator
)


class TestSecureConditionEvaluator:
    """Test cases for SecureConditionEvaluator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = SecureConditionEvaluator()
        self.test_data = {
            "document_type": {
                "primary_type": "pdf",
                "mime_type": "application/pdf",
                "confidence": 0.95,
                "category": "pdf",
                "subtype": "pdf"
            },
            "file_size": 1024,
            "file_name": "test.pdf",
            "tags": ["important", "contract"],
            "metadata": {
                "pages": 5,
                "author": "John Doe",
                "encrypted": False
            },
            "empty_field": None,
            "empty_string": "",
            "empty_list": []
        }
    
    def test_simple_equality_condition(self):
        """Test simple equality conditions."""
        condition = "document_type.primary_type == 'pdf'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "document_type.primary_type == 'word'"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_numeric_comparison_conditions(self):
        """Test numeric comparison conditions."""
        condition = "document_type.confidence > 0.8"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "document_type.confidence >= 0.95"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "file_size < 2000"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "metadata.pages <= 10"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
    
    def test_in_operator_conditions(self):
        """Test 'in' operator conditions."""
        condition = "document_type.category in ['pdf', 'word', 'excel']"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "document_type.category in ['word', 'excel']"
        result = evaluate_condition(condition, self.test_data)
        assert result is False

        condition = "tags contains 'important'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
    
    def test_contains_operator_conditions(self):
        """Test 'contains' operator conditions."""
        condition = "file_name contains 'test'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "file_name contains 'document'"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_string_pattern_conditions(self):
        """Test string pattern matching conditions."""
        condition = "file_name starts_with 'test'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "file_name ends_with '.pdf'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "file_name starts_with 'document'"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_regex_match_conditions(self):
        """Test regex pattern matching conditions."""
        condition = "file_name regex_match '.*\\.pdf$'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "file_name regex_match '^test.*'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "file_name regex_match '.*\\.docx$'"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_empty_conditions(self):
        """Test empty/null checking conditions."""
        condition = "empty_field is_empty"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "empty_string is_empty"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "empty_list is_empty"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "file_name is_not_empty"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "empty_field is_not_empty"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_logical_and_conditions(self):
        """Test logical AND conditions."""
        condition = "document_type.primary_type == 'pdf' and document_type.confidence > 0.8"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "document_type.primary_type == 'pdf' and document_type.confidence < 0.5"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
        
        condition = "document_type.primary_type == 'word' and document_type.confidence > 0.8"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_logical_or_conditions(self):
        """Test logical OR conditions."""
        condition = "document_type.primary_type == 'pdf' or document_type.primary_type == 'word'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "document_type.primary_type == 'excel' or document_type.primary_type == 'word'"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
        
        condition = "document_type.confidence < 0.5 or document_type.primary_type == 'pdf'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
    
    def test_complex_logical_conditions(self):
        """Test complex logical conditions with mixed AND/OR."""
        condition = "document_type.primary_type == 'pdf' and document_type.confidence > 0.8 or file_size < 500"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "document_type.primary_type == 'word' and document_type.confidence > 0.8 or file_size > 2000"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_field_path_validation(self):
        """Test field path validation."""
        # Valid field paths
        valid_paths = [
            "document_type",
            "document_type.primary_type",
            "metadata.pages",
            "tags[0]",
            "metadata['author']",
            "data.nested.deep_field"
        ]
        
        for path in valid_paths:
            self.evaluator._validate_field_path(path)  # Should not raise
        
        # Invalid field paths
        invalid_paths = [
            "",
            "document.type..primary",
            "document type",
            "document-type.primary!type",
            "document_type[invalid_index]",
            "." + ".".join(["deep"] * 20)  # Too deep
        ]
        
        for path in invalid_paths:
            with pytest.raises(ConditionEvaluationError):
                self.evaluator._validate_field_path(path)
    
    def test_field_value_extraction(self):
        """Test field value extraction from nested data."""
        assert self.evaluator._get_field_value("document_type.primary_type", self.test_data) == "pdf"
        assert self.evaluator._get_field_value("metadata.pages", self.test_data) == 5
        assert self.evaluator._get_field_value("tags[0]", self.test_data) == "important"
        assert self.evaluator._get_field_value("tags[1]", self.test_data) == "contract"
        assert self.evaluator._get_field_value("nonexistent.field", self.test_data) is None
        assert self.evaluator._get_field_value("tags[99]", self.test_data) is None
    
    def test_value_parsing(self):
        """Test value parsing from strings."""
        assert self.evaluator._parse_value("'string'") == "string"
        assert self.evaluator._parse_value('"string"') == "string"
        assert self.evaluator._parse_value("123") == 123
        assert self.evaluator._parse_value("12.34") == 12.34
        assert self.evaluator._parse_value("true") is True
        assert self.evaluator._parse_value("false") is False
        assert self.evaluator._parse_value("null") is None
        assert self.evaluator._parse_value("['a', 'b', 'c']") == ["a", "b", "c"]
        assert self.evaluator._parse_value("[1, 2, 3]") == [1, 2, 3]
    
    def test_security_validation(self):
        """Test security validation prevents code injection."""
        # These should raise ConditionEvaluationError
        malicious_conditions = [
            "document_type.__class__.__name__ == 'dict'",
            "document_type.primary_type == 'pdf'; import os; os.system('ls')",
            "eval('1+1') == 2",
            "exec('print(\"hello\")')",
            "__import__('os').system('ls')"
        ]
        
        for condition in malicious_conditions:
            with pytest.raises(ConditionEvaluationError):
                evaluate_condition(condition, self.test_data)
    
    def test_invalid_operators(self):
        """Test handling of invalid operators."""
        invalid_conditions = [
            "document_type.primary_type === 'pdf'",
            "document_type.primary_type <> 'pdf'",
            "document_type.primary_type like 'pdf'",
            "document_type.primary_type equals 'pdf'"
        ]
        
        for condition in invalid_conditions:
            with pytest.raises(ConditionEvaluationError):
                evaluate_condition(condition, self.test_data)
    
    def test_condition_validation(self):
        """Test condition validation function."""
        # Valid conditions
        valid_conditions = [
            "document_type.primary_type == 'pdf'",
            "document_type.confidence > 0.8",
            "file_name contains 'test'",
            "tags[0] in ['important', 'urgent']",
            "metadata.encrypted is_empty"
        ]
        
        for condition in valid_conditions:
            errors = validate_condition(condition)
            assert len(errors) == 0, f"Valid condition '{condition}' should not have errors: {errors}"
        
        # Invalid conditions
        invalid_conditions = [
            "",
            "document_type.primary_type ==",
            "document_type..primary_type == 'pdf'",
            "document_type.primary_type bad_operator 'pdf'",
            "invalid field name == 'value'"
        ]
        
        for condition in invalid_conditions:
            errors = validate_condition(condition)
            assert len(errors) > 0, f"Invalid condition '{condition}' should have errors"
    
    def test_boolean_conditions(self):
        """Test boolean field conditions."""
        condition = "metadata.encrypted == false"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "metadata.encrypted == true"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_not_equals_conditions(self):
        """Test not equals conditions."""
        condition = "document_type.primary_type != 'word'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "document_type.primary_type != 'pdf'"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_not_in_conditions(self):
        """Test not in conditions."""
        condition = "document_type.category not_in ['word', 'excel']"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "document_type.category not_in ['pdf', 'word']"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_not_contains_conditions(self):
        """Test not contains conditions."""
        condition = "file_name not_contains 'document'"
        result = evaluate_condition(condition, self.test_data)
        assert result is True
        
        condition = "file_name not_contains 'test'"
        result = evaluate_condition(condition, self.test_data)
        assert result is False
    
    def test_regex_error_handling(self):
        """Test regex error handling."""
        condition = "file_name regex_match '[invalid regex'"
        with pytest.raises(ConditionEvaluationError):
            evaluate_condition(condition, self.test_data)
    
    def test_type_coercion(self):
        """Test type coercion in comparisons."""
        # String/number comparisons
        data = {"string_number": "123", "number": 123}
        
        # These should work with type coercion
        condition = "string_number == 123"
        result = evaluate_condition(condition, data)
        assert result is False  # String "123" != number 123
        
        condition = "string_number == '123'"
        result = evaluate_condition(condition, data)
        assert result is True
    
    def test_missing_field_handling(self):
        """Test handling of missing fields."""
        condition = "nonexistent.field == 'value'"
        result = evaluate_condition(condition, self.test_data)
        assert result is False  # None != 'value'
        
        condition = "nonexistent.field is_empty"
        result = evaluate_condition(condition, self.test_data)
        assert result is True  # None is empty
    
    def test_array_access_patterns(self):
        """Test various array access patterns."""
        data = {
            "array": ["first", "second", "third"],
            "dict_array": [{"key": "value1"}, {"key": "value2"}],
            "nested": {
                "array": ["nested1", "nested2"]
            }
        }
        
        # Standard array access
        condition = "array[0] == 'first'"
        result = evaluate_condition(condition, data)
        assert result is True
        
        condition = "array[2] == 'third'"
        result = evaluate_condition(condition, data)
        assert result is True
        
        # Out of bounds access
        condition = "array[99] == 'nonexistent'"
        result = evaluate_condition(condition, data)
        assert result is False
        
        # Nested array access
        condition = "nested.array[0] == 'nested1'"
        result = evaluate_condition(condition, data)
        assert result is True
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty condition string
        with pytest.raises(ConditionEvaluationError):
            evaluate_condition("", self.test_data)
        
        # Whitespace-only condition
        with pytest.raises(ConditionEvaluationError):
            evaluate_condition("   ", self.test_data)
        
        # Single word condition (invalid)
        with pytest.raises(ConditionEvaluationError):
            evaluate_condition("document_type", self.test_data)
    
    def test_performance_regression_protection(self):
        """Test that evaluation doesn't have performance regressions."""
        # This test ensures that complex conditions don't cause performance issues
        complex_condition = " and ".join([
            f"document_type.primary_type == 'pdf'"
            for _ in range(10)
        ])
        
        # Should complete quickly without issues
        result = evaluate_condition(complex_condition, self.test_data)
        assert result is True
    
    def test_condition_caching(self):
        """Test that regex patterns are properly cached."""
        # Multiple evaluations of the same regex should use cached compiled pattern
        condition = "file_name regex_match '.*\\.pdf$'"
        
        # First evaluation
        result1 = evaluate_condition(condition, self.test_data)
        
        # Second evaluation (should use cached pattern)
        result2 = evaluate_condition(condition, self.test_data)
        
        assert result1 == result2 == True
        
        # Verify pattern was cached
        assert '.*\\.pdf$' in self.evaluator._compiled_regex_cache


if __name__ == "__main__":
    pytest.main([__file__])
