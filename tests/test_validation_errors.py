"""
Unit tests for validation error reporting (Session 5)
"""

import unittest
from package.core import ValidationError


class TestValidationError(unittest.TestCase):
    """Test ValidationError exception class"""

    def test_basic_validation_error(self):
        """Test creating basic validation error"""
        error = ValidationError("Test error message")

        self.assertEqual(error.message, "Test error message")
        self.assertIsNone(error.line_number)
        self.assertEqual(error.error_type, 'unknown')
        self.assertIsNone(error.field)
        self.assertIsNone(error.value)

    def test_validation_error_with_line_number(self):
        """Test validation error with line number"""
        error = ValidationError("Test error", line_number=42)

        self.assertEqual(error.line_number, 42)
        self.assertIn("Line 42", str(error))

    def test_validation_error_with_type(self):
        """Test validation error with specific type"""
        error = ValidationError(
            "Invalid amount",
            error_type='invalid_amount'
        )

        self.assertEqual(error.error_type, 'invalid_amount')

    def test_validation_error_with_field_and_value(self):
        """Test validation error with field and value"""
        error = ValidationError(
            "Invalid amount",
            line_number=10,
            error_type='invalid_amount',
            field='amount',
            value='abc'
        )

        self.assertEqual(error.field, 'amount')
        self.assertEqual(error.value, 'abc')
        self.assertEqual(error.line_number, 10)

    def test_validation_error_string_with_line(self):
        """Test string representation with line number"""
        error = ValidationError(
            "Missing required field",
            line_number=5
        )

        result = str(error)
        self.assertEqual(result, "Line 5: Missing required field")

    def test_validation_error_string_without_line(self):
        """Test string representation without line number"""
        error = ValidationError("General error")

        result = str(error)
        self.assertEqual(result, "General error")

    def test_validation_error_is_exception(self):
        """Test that ValidationError is an Exception"""
        error = ValidationError("Test")

        self.assertIsInstance(error, Exception)

    def test_validation_error_can_be_raised(self):
        """Test that ValidationError can be raised and caught"""
        with self.assertRaises(ValidationError) as ctx:
            raise ValidationError("Test error", line_number=100)

        self.assertIn("Line 100", str(ctx.exception))


class TestValidationErrorGrouping(unittest.TestCase):
    """Test grouping validation errors by type"""

    def test_group_errors_by_type(self):
        """Test grouping multiple errors by type"""
        errors = [
            ValidationError("Amount 1", error_type='invalid_amount'),
            ValidationError("Amount 2", error_type='invalid_amount'),
            ValidationError("Date 1", error_type='invalid_date'),
            ValidationError("Missing", error_type='missing_field')
        ]

        # Group by type
        grouped = {}
        for error in errors:
            if error.error_type not in grouped:
                grouped[error.error_type] = []
            grouped[error.error_type].append(error)

        self.assertEqual(len(grouped), 3)
        self.assertEqual(len(grouped['invalid_amount']), 2)
        self.assertEqual(len(grouped['invalid_date']), 1)
        self.assertEqual(len(grouped['missing_field']), 1)

    def test_multiple_line_numbers(self):
        """Test that line numbers are preserved for multiple errors"""
        errors = [
            ValidationError("Error 1", line_number=5),
            ValidationError("Error 2", line_number=10),
            ValidationError("Error 3", line_number=15)
        ]

        line_numbers = [e.line_number for e in errors]
        self.assertEqual(line_numbers, [5, 10, 15])


if __name__ == '__main__':
    unittest.main()
