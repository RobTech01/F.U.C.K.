"""
Unit tests for storage.py hash table persistence functions
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
from package.storage import (
    initialize_hash_table,
    save_hash_table,
    load_hash_table,
    get_categories_and_totals,
    print_hash_table,
    save_transaction
)


class TestInitializeHashTable(unittest.TestCase):
    """Test hash table initialization"""

    def test_initialize_creates_correct_structure(self):
        """Test that initialization creates the correct data structure"""
        hash_table = initialize_hash_table()

        self.assertIsInstance(hash_table, dict)
        self.assertIn('transaction_ids', hash_table)
        self.assertIn('categories', hash_table)
        self.assertIn('addresses', hash_table)
        self.assertIn('transactions', hash_table)

    def test_initialize_creates_empty_structures(self):
        """Test that initialization creates empty collections"""
        hash_table = initialize_hash_table()

        self.assertEqual(hash_table['transaction_ids'], [])
        self.assertEqual(hash_table['categories'], {})
        self.assertEqual(hash_table['addresses'], {})
        self.assertEqual(hash_table['transactions'], [])

    def test_initialize_returns_new_instance(self):
        """Test that each call returns a new instance"""
        table1 = initialize_hash_table()
        table2 = initialize_hash_table()

        # Modify one
        table1['transaction_ids'].append('test')

        # Verify the other is unchanged
        self.assertEqual(table2['transaction_ids'], [])


class TestSaveAndLoadHashTable(unittest.TestCase):
    """Test hash table save and load operations"""

    def setUp(self):
        """Set up test cipher suite and temporary file"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)

        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.enc')
        self.temp_file.close()

    def tearDown(self):
        """Clean up temporary file"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_save_hash_table_creates_file(self):
        """Test that saving creates a file"""
        hash_table = initialize_hash_table()

        # Patch the file path to use our temp file
        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            save_hash_table(hash_table, self.cipher_suite)

        self.assertTrue(os.path.exists(self.temp_file.name))

    def test_save_and_load_roundtrip(self):
        """Test that saving and loading returns the same data"""
        original_table = {
            'transaction_ids': ['tx_001', 'tx_002'],
            'categories': {
                'Groceries/Food': 250.50,
                'Utilities/Bills': 150.00
            },
            'addresses': {
                'hash_walmart': 'Groceries/Food',
                'hash_electric': 'Utilities/Bills'
            }
        }

        # Save and load
        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            save_hash_table(original_table, self.cipher_suite)
            loaded_table = load_hash_table(self.cipher_suite)

        self.assertEqual(original_table, loaded_table)

    def test_load_nonexistent_file_returns_initialized_table(self):
        """Test that loading a non-existent file returns an initialized table"""
        nonexistent_file = '/tmp/does_not_exist_12345.enc'

        with patch('package.storage.HASH_TABLE_FILE', nonexistent_file):
            loaded_table = load_hash_table(self.cipher_suite)

        expected = initialize_hash_table()
        self.assertEqual(loaded_table, expected)

    def test_load_with_wrong_key_raises_exception(self):
        """Test that loading with wrong key fails"""
        hash_table = initialize_hash_table()

        # Save with one key
        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            save_hash_table(hash_table, self.cipher_suite)

            # Try to load with different key
            wrong_key = Fernet.generate_key()
            wrong_cipher = Fernet(wrong_key)

            with self.assertRaises(Exception):
                load_hash_table(wrong_cipher)

    def test_save_complex_hash_table(self):
        """Test saving and loading a complex hash table"""
        complex_table = {
            'transaction_ids': [f'tx_{i:03d}' for i in range(10)],
            'categories': {
                'Groceries/Food': 1250.75,
                'Utilities/Bills': 450.00,
                'Entertainment/Leisure': 200.50,
                'Salary': -5000.00
            },
            'addresses': {
                f'hash_address_{i}': 'Groceries/Food'
                for i in range(20)
            }
        }

        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            save_hash_table(complex_table, self.cipher_suite)
            loaded_table = load_hash_table(self.cipher_suite)

        self.assertEqual(complex_table, loaded_table)

    def test_save_empty_hash_table(self):
        """Test saving and loading an empty hash table"""
        empty_table = initialize_hash_table()

        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            save_hash_table(empty_table, self.cipher_suite)
            loaded_table = load_hash_table(self.cipher_suite)

        self.assertEqual(empty_table, loaded_table)

    def test_saved_file_is_encrypted(self):
        """Test that the saved file is actually encrypted (not plain JSON)"""
        hash_table = {
            'transaction_ids': ['secret_transaction'],
            'categories': {'Secret': 999.99},
            'addresses': {'secret_hash': 'Secret'}
        }

        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            save_hash_table(hash_table, self.cipher_suite)

        # Read the raw file content
        with open(self.temp_file.name, 'rb') as f:
            raw_content = f.read()

        # Verify it's not plain JSON
        try:
            json.loads(raw_content.decode())
            self.fail("File content is plain JSON, not encrypted!")
        except (json.JSONDecodeError, UnicodeDecodeError):
            # This is expected - encrypted data shouldn't be valid JSON
            pass


class TestGetCategoriesAndTotals(unittest.TestCase):
    """Test category extraction function"""

    def test_get_categories_returns_categories_dict(self):
        """Test that function returns the categories dictionary"""
        hash_table = {
            'transaction_ids': [],
            'categories': {
                'Groceries/Food': 500.00,
                'Utilities/Bills': 200.00
            },
            'addresses': {}
        }

        # Suppress print output for clean test output
        with patch('builtins.print'):
            result = get_categories_and_totals(hash_table)

        self.assertEqual(result, hash_table['categories'])

    def test_get_categories_empty_table(self):
        """Test with empty categories"""
        hash_table = initialize_hash_table()

        with patch('builtins.print'):
            result = get_categories_and_totals(hash_table)

        self.assertEqual(result, {})


class TestPrintHashTable(unittest.TestCase):
    """Test hash table printing function"""

    def test_print_hash_table_does_not_crash(self):
        """Test that printing doesn't raise exceptions"""
        hash_table = {
            'transaction_ids': ['tx_001', 'tx_002'],
            'categories': {
                'Groceries/Food': 250.50,
                'Utilities/Bills': 150.00
            },
            'addresses': {
                'hash_walmart': 'Groceries/Food',
                'hash_electric': 'Utilities/Bills'
            }
        }

        # Should not raise any exceptions
        try:
            with patch('builtins.print'):
                print_hash_table(hash_table)
        except Exception as e:
            self.fail(f"print_hash_table raised {e}")

    def test_print_empty_hash_table(self):
        """Test printing an empty hash table"""
        hash_table = initialize_hash_table()

        try:
            with patch('builtins.print'):
                print_hash_table(hash_table)
        except Exception as e:
            self.fail(f"print_hash_table raised {e} for empty table")

    def test_print_calls_print_function(self):
        """Test that the function actually calls print"""
        hash_table = initialize_hash_table()

        with patch('builtins.print') as mock_print:
            print_hash_table(hash_table)
            # Verify print was called (output formatting happens)
            self.assertTrue(mock_print.called)


class TestStorageIntegration(unittest.TestCase):
    """Test realistic storage workflows"""

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.enc')
        self.temp_file.close()

    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_incremental_updates_workflow(self):
        """Test realistic workflow of loading, updating, and saving"""
        # Initial save
        initial_table = initialize_hash_table()
        initial_table['transaction_ids'].append('tx_001')
        initial_table['categories']['Groceries/Food'] = 100.00
        initial_table['addresses']['hash_store1'] = 'Groceries/Food'

        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            save_hash_table(initial_table, self.cipher_suite)

            # Load and update
            loaded_table = load_hash_table(self.cipher_suite)
            loaded_table['transaction_ids'].append('tx_002')
            loaded_table['categories']['Groceries/Food'] += 50.00
            loaded_table['addresses']['hash_store2'] = 'Utilities/Bills'

            # Save again
            save_hash_table(loaded_table, self.cipher_suite)

            # Load final state
            final_table = load_hash_table(self.cipher_suite)

        # Verify incremental changes persisted
        self.assertEqual(len(final_table['transaction_ids']), 2)
        self.assertEqual(final_table['categories']['Groceries/Food'], 150.00)
        self.assertEqual(len(final_table['addresses']), 2)

    def test_multiple_save_load_cycles(self):
        """Test multiple save/load cycles maintain data integrity"""
        current_table = initialize_hash_table()

        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            # Perform 5 save/load cycles
            for i in range(5):
                current_table['transaction_ids'].append(f'tx_{i:03d}')
                current_table['categories'][f'Category_{i}'] = i * 100.0

                save_hash_table(current_table, self.cipher_suite)
                current_table = load_hash_table(self.cipher_suite)

            # Verify all data persisted
            self.assertEqual(len(current_table['transaction_ids']), 5)
            self.assertEqual(len(current_table['categories']), 5)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility for transaction history"""

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.enc')
        self.temp_file.close()

    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_load_old_format_adds_transactions_key(self):
        """Test that loading old format hash table adds transactions key"""
        # Create old format hash table (without transactions)
        old_format_table = {
            'transaction_ids': ['tx_001'],
            'categories': {'Groceries/Food': 100.00},
            'addresses': {'hash_store': 'Groceries/Food'}
        }

        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            # Save old format
            save_hash_table(old_format_table, self.cipher_suite)

            # Load - should add transactions key
            with patch('builtins.print'):
                loaded_table = load_hash_table(self.cipher_suite)

        self.assertIn('transactions', loaded_table)
        self.assertEqual(loaded_table['transactions'], [])
        self.assertEqual(loaded_table['transaction_ids'], old_format_table['transaction_ids'])
        self.assertEqual(loaded_table['categories'], old_format_table['categories'])

    def test_load_new_format_preserves_transactions(self):
        """Test that loading new format preserves transactions"""
        new_format_table = initialize_hash_table()
        new_format_table['transactions'].append({
            'date': '2024-01-15',
            'address_hash': 'encrypted_hash',
            'amount': 99.99,
            'category': 'Entertainment'
        })

        with patch('package.storage.HASH_TABLE_FILE', self.temp_file.name):
            save_hash_table(new_format_table, self.cipher_suite)
            loaded_table = load_hash_table(self.cipher_suite)

        self.assertEqual(loaded_table, new_format_table)
        self.assertEqual(len(loaded_table['transactions']), 1)


class TestSaveTransaction(unittest.TestCase):
    """Test save_transaction function"""

    def test_save_transaction_adds_to_list(self):
        """Test that save_transaction adds transaction to list"""
        hash_table = initialize_hash_table()

        save_transaction(hash_table, '2024-01-15', 'enc_hash_123', 99.99, 'Entertainment')

        self.assertEqual(len(hash_table['transactions']), 1)
        self.assertEqual(hash_table['transactions'][0]['date'], '2024-01-15')
        self.assertEqual(hash_table['transactions'][0]['address_hash'], 'enc_hash_123')
        self.assertEqual(hash_table['transactions'][0]['amount'], 99.99)
        self.assertEqual(hash_table['transactions'][0]['category'], 'Entertainment')

    def test_save_transaction_creates_list_if_missing(self):
        """Test that save_transaction creates transactions list if missing"""
        # Hash table without transactions key (old format)
        hash_table = {
            'transaction_ids': [],
            'categories': {},
            'addresses': {}
        }

        save_transaction(hash_table, '2024-01-15', 'enc_hash', 50.00, 'Food')

        self.assertIn('transactions', hash_table)
        self.assertEqual(len(hash_table['transactions']), 1)

    def test_save_multiple_transactions(self):
        """Test saving multiple transactions"""
        hash_table = initialize_hash_table()

        transactions_data = [
            ('2024-01-15', 'hash1', 100.00, 'Food'),
            ('2024-01-16', 'hash2', 200.00, 'Utilities'),
            ('2024-01-17', 'hash1', 150.00, 'Food')
        ]

        for date, addr_hash, amount, category in transactions_data:
            save_transaction(hash_table, date, addr_hash, amount, category)

        self.assertEqual(len(hash_table['transactions']), 3)
        self.assertEqual(hash_table['transactions'][0]['amount'], 100.00)
        self.assertEqual(hash_table['transactions'][1]['category'], 'Utilities')
        self.assertEqual(hash_table['transactions'][2]['date'], '2024-01-17')

    def test_save_transaction_preserves_existing(self):
        """Test that save_transaction preserves existing transactions"""
        hash_table = initialize_hash_table()
        hash_table['transactions'].append({
            'date': '2024-01-01',
            'address_hash': 'existing',
            'amount': 50.00,
            'category': 'Test'
        })

        save_transaction(hash_table, '2024-01-02', 'new_hash', 75.00, 'New')

        self.assertEqual(len(hash_table['transactions']), 2)
        self.assertEqual(hash_table['transactions'][0]['date'], '2024-01-01')
        self.assertEqual(hash_table['transactions'][1]['date'], '2024-01-02')

    def test_save_transaction_with_negative_amount(self):
        """Test saving transaction with negative amount (income)"""
        hash_table = initialize_hash_table()

        save_transaction(hash_table, '2024-01-15', 'hash_salary', -5000.00, 'Salary')

        self.assertEqual(hash_table['transactions'][0]['amount'], -5000.00)


if __name__ == '__main__':
    unittest.main()
