"""
Secure condition evaluation system for pipeline steps.

This module provides a secure way to evaluate conditions on pipeline steps,
allowing for dynamic step execution based on document data while preventing
code injection attacks.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ComparisonOperator(Enum):
    """Supported comparison operators for condition evaluation."""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCH = "regex_match"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class LogicalOperator(Enum):
    """Supported logical operators for combining conditions."""
    AND = "and"
    OR = "or"


@dataclass
class Condition:
    """Represents a single condition to evaluate."""
    field_path: str  # Dot notation path to the field (e.g., "document_type.primary_type")
    operator: ComparisonOperator
    value: Any = None  # The value to compare against (not needed for is_empty/is_not_empty)
    
    def __post_init__(self):
        """Validate condition parameters."""
        if self.operator in [ComparisonOperator.IS_EMPTY, ComparisonOperator.IS_NOT_EMPTY]:
            if self.value is not None:
                raise ValueError(f"Operator {self.operator.value} should not have a value")
        else:
            if self.value is None:
                raise ValueError(f"Operator {self.operator.value} requires a value")


@dataclass
class ConditionGroup:
    """Represents a group of conditions combined with logical operators."""
    conditions: List[Union[Condition, 'ConditionGroup']]
    logical_operator: LogicalOperator = LogicalOperator.AND


class ConditionEvaluationError(Exception):
    """Exception raised when condition evaluation fails."""
    pass


class SecureConditionEvaluator:
    """
    A secure condition evaluator that prevents code injection while allowing
    flexible condition evaluation on document data.
    """
    
    # Maximum depth for nested field access to prevent stack overflow
    MAX_FIELD_DEPTH = 10
    
    # Pattern for valid field names (alphanumeric, underscore, hyphen)
    VALID_FIELD_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_-]*$')
    
    def __init__(self):
        """Initialize the secure condition evaluator."""
        self._compiled_regex_cache = {}
    
    def parse_condition_string(self, condition_string: str) -> ConditionGroup:
        """
        Parse a condition string into a structured ConditionGroup.
        
        Supports expressions like:
        - "document_type.primary_type == 'pdf'"
        - "document_type.confidence > 0.8"
        - "document_type.category in ['office_document', 'pdf']"
        - "document_type.primary_type == 'pdf' and document_type.confidence > 0.8"
        
        Args:
            condition_string: The condition string to parse
            
        Returns:
            ConditionGroup: Parsed condition structure
            
        Raises:
            ConditionEvaluationError: If the condition string is invalid
        """
        if not condition_string or not condition_string.strip():
            raise ConditionEvaluationError("Condition string cannot be empty")
        
        # Remove extra whitespace
        condition_string = condition_string.strip()
        
        # For now, implement a simple parser that handles basic conditions
        # This could be extended to support more complex expressions
        return self._parse_simple_condition(condition_string)
    
    def _parse_simple_condition(self, condition_string: str) -> ConditionGroup:
        """
        Parse a simple condition string (supports AND/OR operations).
        
        Args:
            condition_string: The condition string to parse
            
        Returns:
            ConditionGroup: Parsed condition structure
        """
        # Split by logical operators (case-insensitive)
        and_parts = re.split(r'\s+and\s+', condition_string, flags=re.IGNORECASE)
        
        if len(and_parts) > 1:
            # Handle AND operations
            conditions = []
            for part in and_parts:
                or_parts = re.split(r'\s+or\s+', part.strip(), flags=re.IGNORECASE)
                if len(or_parts) > 1:
                    # Nested OR within AND
                    or_conditions = [self._parse_single_condition(p.strip()) for p in or_parts]
                    conditions.append(ConditionGroup(or_conditions, LogicalOperator.OR))
                else:
                    conditions.append(self._parse_single_condition(part.strip()))
            return ConditionGroup(conditions, LogicalOperator.AND)
        else:
            # Check for OR operations
            or_parts = re.split(r'\s+or\s+', condition_string, flags=re.IGNORECASE)
            if len(or_parts) > 1:
                conditions = [self._parse_single_condition(p.strip()) for p in or_parts]
                return ConditionGroup(conditions, LogicalOperator.OR)
            else:
                # Single condition
                return ConditionGroup([self._parse_single_condition(condition_string)])
    
    def _parse_single_condition(self, condition_string: str) -> Condition:
        """
        Parse a single condition (no logical operators).
        
        Args:
            condition_string: Single condition string
            
        Returns:
            Condition: Parsed condition
        """
        # Remove surrounding parentheses if present
        condition_string = condition_string.strip()
        if condition_string.startswith('(') and condition_string.endswith(')'):
            condition_string = condition_string[1:-1].strip()
        
        # Try to match different operators
        # Sort operators by length (descending) to match longer operators first (e.g., >= before >)
        operators_by_length = sorted(ComparisonOperator, key=lambda op: len(op.value), reverse=True)
        
        for op in operators_by_length:
            if op in [ComparisonOperator.IS_EMPTY, ComparisonOperator.IS_NOT_EMPTY]:
                # Special case for unary operators
                if op.value in condition_string:
                    field_path = condition_string.replace(op.value, '').strip()
                    self._validate_field_path(field_path)
                    return Condition(field_path, op)
            else:
                # Binary operators
                if op.value in condition_string:
                    parts = condition_string.split(op.value, 1)
                    if len(parts) == 2:
                        field_path = parts[0].strip()
                        value_str = parts[1].strip()
                        
                        self._validate_field_path(field_path)
                        value = self._parse_value(value_str)
                        
                        return Condition(field_path, op, value)
        
        raise ConditionEvaluationError(f"Invalid condition format: {condition_string}")
    
    def _validate_field_path(self, field_path: str):
        """
        Validate that a field path is safe and well-formed.
        
        Args:
            field_path: The field path to validate
            
        Raises:
            ConditionEvaluationError: If the field path is invalid
        """
        if not field_path:
            raise ConditionEvaluationError("Field path cannot be empty")
        
        # Split by dots and validate each part
        parts = field_path.split('.')
        if len(parts) > self.MAX_FIELD_DEPTH:
            raise ConditionEvaluationError(f"Field path depth exceeds maximum ({self.MAX_FIELD_DEPTH})")
        
        for part in parts:
            if not part:
                raise ConditionEvaluationError("Field path cannot contain empty parts")
            
            # Check for array access patterns like [0] or ['key']
            if '[' in part and ']' in part:
                # Extract the field name and index/key
                field_name = part.split('[')[0]
                index_part = part[part.index('[')+1:part.rindex(']')]
                
                if field_name and not self.VALID_FIELD_PATTERN.match(field_name):
                    raise ConditionEvaluationError(f"Invalid field name: {field_name}")
                
                # Validate index (must be integer or quoted string)
                if not (index_part.isdigit() or 
                        (index_part.startswith('"') and index_part.endswith('"')) or
                        (index_part.startswith("'") and index_part.endswith("'"))):
                    raise ConditionEvaluationError(f"Invalid array index: {index_part}")
            else:
                if not self.VALID_FIELD_PATTERN.match(part):
                    raise ConditionEvaluationError(f"Invalid field name: {part}")
    
    def _parse_value(self, value_str: str) -> Any:
        """
        Parse a value string into its appropriate type.
        
        Args:
            value_str: The value string to parse
            
        Returns:
            Any: Parsed value
        """
        value_str = value_str.strip()
        
        # Handle quoted strings
        if ((value_str.startswith('"') and value_str.endswith('"')) or
            (value_str.startswith("'") and value_str.endswith("'"))):
            return value_str[1:-1]  # Remove quotes
        
        # Handle lists/arrays
        if value_str.startswith('[') and value_str.endswith(']'):
            list_content = value_str[1:-1].strip()
            if not list_content:
                return []
            
            # Split by comma and parse each item
            items = []
            for item in list_content.split(','):
                items.append(self._parse_value(item.strip()))
            return items
        
        # Handle booleans
        if value_str.lower() in ['true', 'false']:
            return value_str.lower() == 'true'
        
        # Handle null/none
        if value_str.lower() in ['null', 'none']:
            return None
        
        # Handle numbers
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # Return as string if no other type matches
        return value_str
    
    def evaluate(self, condition_group: ConditionGroup, data: Dict[str, Any]) -> bool:
        """
        Evaluate a condition group against the provided data.
        
        Args:
            condition_group: The condition group to evaluate
            data: The data dictionary to evaluate against
            
        Returns:
            bool: True if the condition is satisfied, False otherwise
            
        Raises:
            ConditionEvaluationError: If evaluation fails
        """
        try:
            return self._evaluate_condition_group(condition_group, data)
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            raise ConditionEvaluationError(f"Condition evaluation failed: {str(e)}")
    
    def _evaluate_condition_group(self, condition_group: ConditionGroup, data: Dict[str, Any]) -> bool:
        """
        Evaluate a condition group.
        
        Args:
            condition_group: The condition group to evaluate
            data: The data dictionary to evaluate against
            
        Returns:
            bool: Evaluation result
        """
        results = []
        
        for condition in condition_group.conditions:
            if isinstance(condition, Condition):
                results.append(self._evaluate_single_condition(condition, data))
            elif isinstance(condition, ConditionGroup):
                results.append(self._evaluate_condition_group(condition, data))
            else:
                raise ConditionEvaluationError(f"Invalid condition type: {type(condition)}")
        
        # Apply logical operator
        if condition_group.logical_operator == LogicalOperator.AND:
            return all(results)
        elif condition_group.logical_operator == LogicalOperator.OR:
            return any(results)
        else:
            raise ConditionEvaluationError(f"Unknown logical operator: {condition_group.logical_operator}")
    
    def _evaluate_single_condition(self, condition: Condition, data: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition.
        
        Args:
            condition: The condition to evaluate
            data: The data dictionary to evaluate against
            
        Returns:
            bool: Evaluation result
        """
        # Get the field value from the data
        field_value = self._get_field_value(condition.field_path, data)
        
        # Evaluate based on operator
        if condition.operator == ComparisonOperator.EQUALS:
            return field_value == condition.value
        elif condition.operator == ComparisonOperator.NOT_EQUALS:
            return field_value != condition.value
        elif condition.operator == ComparisonOperator.GREATER_THAN:
            return field_value > condition.value
        elif condition.operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
            return field_value >= condition.value
        elif condition.operator == ComparisonOperator.LESS_THAN:
            return field_value < condition.value
        elif condition.operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
            return field_value <= condition.value
        elif condition.operator == ComparisonOperator.CONTAINS:
            return condition.value in field_value
        elif condition.operator == ComparisonOperator.NOT_CONTAINS:
            return condition.value not in field_value
        elif condition.operator == ComparisonOperator.IN:
            return field_value in condition.value
        elif condition.operator == ComparisonOperator.NOT_IN:
            return field_value not in condition.value
        elif condition.operator == ComparisonOperator.STARTS_WITH:
            return str(field_value).startswith(str(condition.value))
        elif condition.operator == ComparisonOperator.ENDS_WITH:
            return str(field_value).endswith(str(condition.value))
        elif condition.operator == ComparisonOperator.REGEX_MATCH:
            return self._regex_match(field_value, condition.value)
        elif condition.operator == ComparisonOperator.IS_EMPTY:
            return field_value is None or field_value == "" or field_value == []
        elif condition.operator == ComparisonOperator.IS_NOT_EMPTY:
            return field_value is not None and field_value != "" and field_value != []
        else:
            raise ConditionEvaluationError(f"Unknown operator: {condition.operator}")
    
    def _get_field_value(self, field_path: str, data: Dict[str, Any]) -> Any:
        """
        Safely get a field value from nested data using dot notation.
        
        Args:
            field_path: Dot notation path to the field
            data: The data dictionary
            
        Returns:
            Any: The field value or None if not found
        """
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if current is None:
                return None
            
            # Handle array access
            if '[' in part and ']' in part:
                field_name = part.split('[')[0]
                index_part = part[part.index('[')+1:part.rindex(']')]
                
                # Get the field first
                if field_name:
                    if isinstance(current, dict):
                        current = current.get(field_name)
                    else:
                        return None
                
                # Apply index
                if isinstance(current, (list, tuple)):
                    try:
                        index = int(index_part)
                        if 0 <= index < len(current):
                            current = current[index]
                        else:
                            return None
                    except (ValueError, IndexError):
                        return None
                elif isinstance(current, dict):
                    # Remove quotes from string keys
                    key = index_part
                    if ((key.startswith('"') and key.endswith('"')) or
                        (key.startswith("'") and key.endswith("'"))):
                        key = key[1:-1]
                    current = current.get(key)
                else:
                    return None
            else:
                # Simple field access
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
        
        return current
    
    def _regex_match(self, field_value: Any, pattern: str) -> bool:
        """
        Perform regex matching with caching for performance.
        
        Args:
            field_value: The value to match against
            pattern: The regex pattern
            
        Returns:
            bool: True if the pattern matches, False otherwise
        """
        try:
            # Cache compiled regex patterns
            if pattern not in self._compiled_regex_cache:
                self._compiled_regex_cache[pattern] = re.compile(pattern)
            
            regex = self._compiled_regex_cache[pattern]
            return bool(regex.search(str(field_value)))
        except re.error as e:
            raise ConditionEvaluationError(f"Invalid regex pattern '{pattern}': {e}")
    
    def validate_condition_string(self, condition_string: str) -> List[str]:
        """
        Validate a condition string and return any errors.
        
        Args:
            condition_string: The condition string to validate
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            self.parse_condition_string(condition_string)
        except ConditionEvaluationError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
        
        return errors


# Convenience functions for common use cases
def evaluate_condition(condition_string: str, data: Dict[str, Any]) -> bool:
    """
    Evaluate a condition string against data.
    
    Args:
        condition_string: The condition string to evaluate
        data: The data dictionary to evaluate against
        
    Returns:
        bool: True if the condition is satisfied, False otherwise
    """
    evaluator = SecureConditionEvaluator()
    condition_group = evaluator.parse_condition_string(condition_string)
    return evaluator.evaluate(condition_group, data)


def validate_condition(condition_string: str) -> List[str]:
    """
    Validate a condition string.
    
    Args:
        condition_string: The condition string to validate
        
    Returns:
        List[str]: List of validation errors (empty if valid)
    """
    evaluator = SecureConditionEvaluator()
    return evaluator.validate_condition_string(condition_string)
