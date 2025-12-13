"""
Unit tests for core.py business logic
"""

import unittest
from package.core import (
    sanitize_string,
    sanitize_transaction,
    validate_transaction,
    generate_transaction_id,
    sanitize_filepath
)


class TestSanitization(unittest.TestCase):
    """Test input sanitization functions"""

    def test_sanitize_string_removes_null_bytes(self):
        result = sanitize_string("test\x00data")
        self.assertEqual(result, "testdata")

    def test_sanitize_string_truncates_long_strings(self):
        long_string = "a" * 2000
        result = sanitize_string(long_string, max_length=100)
        self.assertEqual(len(result), 100)

    def test_sanitize_transaction(self):
        transaction = {
            'date': '2024-01-01',
            'address': 'Test\x00Address',
            'amount': 100.50,
            'name': 'Test  Name  '
        }
        result = sanitize_transaction(transaction)
        self.assertEqual(result['address'], 'TestAddress')
        self.assertEqual(result['name'], 'Test  Name')
        self.assertEqual(result['amount'], 100.50)


class TestValidation(unittest.TestCase):
    """Test validation functions"""

    def test_validate_transaction_valid(self):
        transaction = {
            'date': '2024-01-01',
            'address': 'Valid Address',
            'amount': 100.50
        }
        is_valid, error = validate_transaction(transaction)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_validate_transaction_missing_field(self):
        transaction = {
            'date': '2024-01-01',
            'amount': 100.50
        }
        is_valid, error = validate_transaction(transaction)
        self.assertFalse(is_valid)
        self.assertIn("Missing required field", error)

    def test_validate_transaction_invalid_amount(self):
        transaction = {
            'date': '2024-01-01',
            'address': 'Test',
            'amount': 'invalid'
        }
        is_valid, error = validate_transaction(transaction)
        self.assertFalse(is_valid)
        self.assertIn("Invalid amount", error)

    def test_validate_transaction_sql_injection(self):
        transaction = {
            'date': '2024-01-01',
            'address': "'; DROP TABLE users; --",
            'amount': 100
        }
        is_valid, error = validate_transaction(transaction)
        self.assertFalse(is_valid)
        self.assertIn("Suspicious content", error)


class TestTransactionID(unittest.TestCase):
    """Test transaction ID generation"""

    def test_generate_transaction_id_with_hash(self):
        tx_id = generate_transaction_id('2024-01-01', 100.50, 'abcd1234')
        self.assertIn('2024-01-01', tx_id)
        self.assertIn('abcd1234', tx_id)
        self.assertIn('100.5', tx_id)

    def test_generate_transaction_id_without_hash(self):
        tx_id = generate_transaction_id('2024-01-01', 100.50)
        self.assertIn('2024-01-01', tx_id)
        self.assertIn('100.5', tx_id)


class TestFilePath(unittest.TestCase):
    """Test file path sanitization"""

    def test_sanitize_filepath_valid_csv(self):
        path, is_valid, error = sanitize_filepath('test.csv')
        self.assertTrue(is_valid)
        self.assertTrue(path.endswith('test.csv'))

    def test_sanitize_filepath_invalid_extension(self):
        path, is_valid, error = sanitize_filepath('test.txt')
        self.assertFalse(is_valid)
        self.assertIn("Invalid file extension", error)

    def test_sanitize_filepath_null_byte(self):
        path, is_valid, error = sanitize_filepath('test\x00.csv')
        self.assertFalse(is_valid)
        self.assertIn("null byte", error.lower())


if __name__ == '__main__':
    unittest.main()
