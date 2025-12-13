"""
Unit tests for read_data.py CSV processing functions
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock, call
from cryptography.fernet import Fernet
from package.read_data import process_csv_file
from package.storage import initialize_hash_table


class TestProcessCSVFile(unittest.TestCase):
    """Test CSV file processing"""

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.test_salt = b'test_salt_1234567890123456789012'
        self.hash_table = initialize_hash_table()

        # Create temporary CSV file
        self.temp_csv = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.csv', encoding='utf-8'
        )
        self.temp_csv.close()

    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.temp_csv.name):
            os.unlink(self.temp_csv.name)

    def _write_csv(self, content):
        """Helper to write CSV content"""
        with open(self.temp_csv.name, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_mock_config(self, has_mapping=False):
        """Helper to create mock config"""
        mock_config = MagicMock()
        if has_mapping:
            mock_config.get_column_mapping.return_value = {
                'date': 0,
                'address': 1,
                'amount': 2,
                'name': -1,
                'type': -1,
                'description': -1
            }
        else:
            mock_config.get_column_mapping.return_value = None
        return mock_config

    @patch('package.read_data.Config')
    @patch('package.read_data.categorize_transaction')
    @patch('package.read_data.cli.select_csv_columns')
    @patch('package.read_data.cli.print_progress')
    @patch('package.read_data.cli.print_summary')
    def test_process_valid_csv_with_saved_mapping(
        self, mock_summary, mock_progress, mock_select, mock_categorize, mock_config_class
    ):
        """Test processing a valid CSV with saved column mapping"""
        # Setup
        csv_content = """Date;Address;Amount
2024-01-01;Walmart;100.50
2024-01-02;Target;75.25
2024-01-03;Best Buy;250.00"""
        self._write_csv(csv_content)

        mock_config = self._create_mock_config(has_mapping=True)
        mock_config_class.load.return_value = mock_config

        # Execute
        stats = process_csv_file(
            self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Verify
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['processed'], 3)
        self.assertEqual(stats['skipped'], 0)
        self.assertEqual(stats['errors'], 0)
        self.assertEqual(mock_categorize.call_count, 3)
        mock_select.assert_not_called()  # Should use saved mapping

    @patch('package.read_data.Config')
    @patch('package.read_data.categorize_transaction')
    @patch('package.read_data.cli.select_csv_columns')
    @patch('package.read_data.cli.print_progress')
    @patch('package.read_data.cli.print_summary')
    def test_process_csv_without_saved_mapping(
        self, mock_summary, mock_progress, mock_select, mock_categorize, mock_config_class
    ):
        """Test processing CSV when no saved mapping exists"""
        csv_content = """Date;Store;Total
2024-01-01;Costco;150.00"""
        self._write_csv(csv_content)

        mock_config = self._create_mock_config(has_mapping=False)
        mock_config_class.load.return_value = mock_config
        mock_select.return_value = (0, 1, 2, -1, -1, -1)  # date, address, amount, ...

        # Execute
        stats = process_csv_file(
            self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Verify
        self.assertEqual(stats['processed'], 1)
        mock_select.assert_called_once()  # Should prompt for mapping
        mock_config.save_column_mapping.assert_called_once()  # Should save mapping

    @patch('package.read_data.Config')
    @patch('package.read_data.categorize_transaction')
    @patch('package.read_data.cli.select_csv_columns')
    @patch('package.read_data.cli.print_progress')
    @patch('package.read_data.cli.print_summary')
    def test_process_csv_skips_invalid_rows(
        self, mock_summary, mock_progress, mock_select, mock_categorize, mock_config_class
    ):
        """Test that invalid rows are skipped"""
        csv_content = """Date;Address;Amount
2024-01-01;Walmart;100.50
2024-01-02;Target;invalid_amount
2024-01-03;Best Buy;200.00"""
        self._write_csv(csv_content)

        mock_config = self._create_mock_config(has_mapping=True)
        mock_config_class.load.return_value = mock_config

        # Execute
        stats = process_csv_file(
            self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Verify
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['processed'], 2)
        self.assertEqual(stats['skipped'], 1)
        self.assertEqual(mock_categorize.call_count, 2)

    @patch('package.read_data.Config')
    @patch('package.read_data.categorize_transaction')
    @patch('package.read_data.cli.select_csv_columns')
    @patch('package.read_data.cli.print_progress')
    @patch('package.read_data.cli.print_summary')
    def test_process_csv_handles_malicious_input(
        self, mock_summary, mock_progress, mock_select, mock_categorize, mock_config_class
    ):
        """Test that SQL injection patterns are detected and skipped"""
        csv_content = """Date;Address;Amount
2024-01-01;'; DROP TABLE users; --;100.50"""
        self._write_csv(csv_content)

        mock_config = self._create_mock_config(has_mapping=True)
        mock_config_class.load.return_value = mock_config

        # Execute
        stats = process_csv_file(
            self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Verify - should be skipped due to suspicious content
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['skipped'], 1)
        self.assertEqual(stats['processed'], 0)

    def test_process_empty_csv_raises_error(self):
        """Test that empty CSV raises ValueError"""
        self._write_csv("")

        with self.assertRaises(ValueError) as context:
            process_csv_file(
                self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
            )

        self.assertIn("empty", str(context.exception).lower())

    def test_process_csv_with_invalid_header(self):
        """Test that CSV with too few columns raises error"""
        csv_content = """Date;Amount
2024-01-01;100"""
        self._write_csv(csv_content)

        with self.assertRaises(ValueError) as context:
            process_csv_file(
                self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
            )

        self.assertIn("header", str(context.exception).lower())

    def test_process_nonexistent_file_raises_error(self):
        """Test that non-existent file raises ValueError"""
        with self.assertRaises(ValueError) as context:
            process_csv_file(
                '/tmp/does_not_exist_12345.csv',
                self.hash_table,
                self.cipher_suite,
                self.test_salt
            )

        # Should fail validation before FileNotFoundError
        self.assertIn("Invalid CSV", str(context.exception))

    @patch('package.read_data.Config')
    @patch('package.read_data.categorize_transaction')
    @patch('package.read_data.cli.select_csv_columns')
    @patch('package.read_data.cli.print_progress')
    @patch('package.read_data.cli.print_summary')
    def test_process_csv_with_decimal_comma(
        self, mock_summary, mock_progress, mock_select, mock_categorize, mock_config_class
    ):
        """Test that European decimal format (comma) is handled"""
        csv_content = """Date;Address;Amount
2024-01-01;Store;100,50
2024-01-02;Shop;75,25"""
        self._write_csv(csv_content)

        mock_config = self._create_mock_config(has_mapping=True)
        mock_config_class.load.return_value = mock_config

        # Execute
        stats = process_csv_file(
            self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Verify - commas should be converted to dots
        self.assertEqual(stats['processed'], 2)
        self.assertEqual(stats['skipped'], 0)

    @patch('package.read_data.Config')
    @patch('package.read_data.categorize_transaction')
    @patch('package.read_data.cli.select_csv_columns')
    @patch('package.read_data.cli.print_progress')
    @patch('package.read_data.cli.print_summary')
    def test_process_csv_with_missing_columns_in_row(
        self, mock_summary, mock_progress, mock_select, mock_categorize, mock_config_class
    ):
        """Test that rows with fewer columns than header are skipped"""
        csv_content = """Date;Address;Amount
2024-01-01;Walmart;100.50
2024-01-02;Target
2024-01-03;Best Buy;200.00"""
        self._write_csv(csv_content)

        mock_config = self._create_mock_config(has_mapping=True)
        mock_config_class.load.return_value = mock_config

        # Execute
        stats = process_csv_file(
            self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Verify
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['processed'], 2)
        self.assertEqual(stats['skipped'], 1)

    @patch('package.read_data.Config')
    @patch('package.read_data.categorize_transaction')
    @patch('package.read_data.cli.select_csv_columns')
    @patch('package.read_data.cli.print_progress')
    @patch('package.read_data.cli.print_summary')
    def test_process_csv_stops_after_many_errors(
        self, mock_summary, mock_progress, mock_select, mock_categorize, mock_config_class
    ):
        """Test that processing stops after too many errors"""
        # Create CSV with many rows
        csv_content = "Date;Address;Amount\n"
        for i in range(20):
            csv_content += f"2024-01-{i+1:02d};Store;100.00\n"
        self._write_csv(csv_content)

        mock_config = self._create_mock_config(has_mapping=True)
        mock_config_class.load.return_value = mock_config

        # Make categorize_transaction raise exceptions
        mock_categorize.side_effect = Exception("Processing error")

        # Execute
        stats = process_csv_file(
            self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Verify - should stop after 10 errors
        self.assertEqual(stats['errors'], 11)  # Stops on 11th error
        self.assertLess(stats['total'], 20)  # Should not process all rows

    @patch('package.read_data.Config')
    @patch('package.read_data.categorize_transaction')
    @patch('package.read_data.cli.select_csv_columns')
    @patch('package.read_data.cli.print_progress')
    @patch('package.read_data.cli.print_summary')
    def test_process_csv_with_optional_columns(
        self, mock_summary, mock_progress, mock_select, mock_categorize, mock_config_class
    ):
        """Test processing with optional name, type, description columns"""
        csv_content = """Date;Address;Amount;Name;Type;Description
2024-01-01;Walmart;100.50;John Doe;Purchase;Groceries
2024-01-02;Target;75.00;Jane Smith;Debit;Clothing"""
        self._write_csv(csv_content)

        mock_config = self._create_mock_config(has_mapping=False)
        mock_config_class.load.return_value = mock_config
        # Map all columns including optional ones
        mock_select.return_value = (0, 1, 2, 3, 4, 5)

        # Execute
        stats = process_csv_file(
            self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Verify
        self.assertEqual(stats['processed'], 2)

        # Check that categorize was called with transactions containing optional fields
        calls = mock_categorize.call_args_list
        self.assertEqual(len(calls), 2)

        # First transaction
        first_tx = calls[0][0][0]
        self.assertEqual(first_tx['name'], 'John Doe')
        self.assertEqual(first_tx['type'], 'Purchase')
        self.assertEqual(first_tx['description'], 'Groceries')

    @patch('package.read_data.Config')
    @patch('package.read_data.categorize_transaction')
    @patch('package.read_data.cli.select_csv_columns')
    @patch('package.read_data.cli.print_progress')
    @patch('package.read_data.cli.print_summary')
    def test_process_csv_sanitizes_transactions(
        self, mock_summary, mock_progress, mock_select, mock_categorize, mock_config_class
    ):
        """Test that transactions are sanitized (null bytes removed, trimmed)"""
        csv_content = """Date;Address;Amount
2024-01-01;  Walmart  ;100.50"""
        self._write_csv(csv_content)

        mock_config = self._create_mock_config(has_mapping=True)
        mock_config_class.load.return_value = mock_config

        # Execute
        stats = process_csv_file(
            self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Verify sanitization occurred
        self.assertEqual(stats['processed'], 1)
        call_args = mock_categorize.call_args_list[0][0][0]
        self.assertEqual(call_args['address'], 'Walmart')  # Trimmed


class TestCSVFileValidation(unittest.TestCase):
    """Test CSV file validation edge cases"""

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.test_salt = b'test_salt_1234567890123456789012'
        self.hash_table = initialize_hash_table()

        self.temp_csv = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.csv', encoding='utf-8'
        )
        self.temp_csv.close()

    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_csv.name):
            os.unlink(self.temp_csv.name)

    def test_process_csv_with_special_characters(self):
        """Test CSV with unicode and special characters in addresses"""
        csv_content = """Date;Address;Amount
2024-01-01;Café René;50.00
2024-01-02;Store #123 @ Main;75.50"""

        with open(self.temp_csv.name, 'w', encoding='utf-8') as f:
            f.write(csv_content)

        mock_config = MagicMock()
        mock_config.get_column_mapping.return_value = {
            'date': 0, 'address': 1, 'amount': 2,
            'name': -1, 'type': -1, 'description': -1
        }

        with patch('package.read_data.Config') as mock_config_class, \
             patch('package.read_data.categorize_transaction') as mock_cat, \
             patch('package.read_data.cli.print_progress'), \
             patch('package.read_data.cli.print_summary'):

            mock_config_class.load.return_value = mock_config

            stats = process_csv_file(
                self.temp_csv.name, self.hash_table, self.cipher_suite, self.test_salt
            )

            # Should process both transactions
            self.assertEqual(stats['processed'], 2)


if __name__ == '__main__':
    unittest.main()
