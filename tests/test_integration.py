"""
Integration tests for F.U.C.K. - Phase 2
Tests component interactions with minimal mocking (only user input)
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

# Import all components
from package.crypto import initialize_crypto, hash_address, encrypt_address, decrypt_address
from package.storage import initialize_hash_table, save_hash_table, load_hash_table
from package.config import Config, get_bank_identifier
from package.category_manager import categorize_transaction
from package.read_data import process_csv_file


class TestCryptoStorageIntegration(unittest.TestCase):
    """
    Phase 2.1: Test Crypto + Storage integration
    Uses real encryption and file I/O, no mocking
    """

    def setUp(self):
        """Set up test environment with temp files"""
        # Create temp file for encrypted storage
        self.temp_storage = tempfile.NamedTemporaryFile(delete=False, suffix='.enc')
        self.temp_storage.close()

        # Create real cipher suite
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.test_salt = b'integration_test_salt_123456789'

    def tearDown(self):
        """Clean up temp files"""
        if os.path.exists(self.temp_storage.name):
            os.unlink(self.temp_storage.name)

    def test_full_encrypt_save_load_decrypt_cycle(self):
        """Test complete encryption workflow: encrypt → save → load → decrypt"""
        # Create hash table with real data
        hash_table = initialize_hash_table()

        # Add encrypted addresses
        addresses = ["Walmart Supercenter", "Target Store", "Best Buy"]
        for i, addr in enumerate(addresses):
            hashed = hash_address(addr, self.test_salt)
            encrypted = encrypt_address(hashed, self.cipher_suite)
            hash_table['addresses'][encrypted] = f"Category_{i}"
            hash_table['categories'][f"Category_{i}"] = (i + 1) * 100.0

        hash_table['transaction_ids'] = ['tx_001', 'tx_002', 'tx_003']

        # Save with real encryption
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            save_hash_table(hash_table, self.cipher_suite)

        # Verify file exists and is encrypted
        self.assertTrue(os.path.exists(self.temp_storage.name))

        with open(self.temp_storage.name, 'rb') as f:
            raw_content = f.read()
            # Should not be plain text
            self.assertNotIn(b'Walmart', raw_content)
            self.assertNotIn(b'Target', raw_content)

        # Load with same cipher
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            loaded_table = load_hash_table(self.cipher_suite)

        # Verify data integrity
        self.assertEqual(loaded_table['transaction_ids'], hash_table['transaction_ids'])
        self.assertEqual(loaded_table['categories'], hash_table['categories'])
        self.assertEqual(len(loaded_table['addresses']), len(hash_table['addresses']))

        # Verify addresses can be decrypted correctly
        for encrypted_addr in loaded_table['addresses'].keys():
            decrypted_hash = decrypt_address(encrypted_addr, self.cipher_suite)
            # Should be one of our original addresses (hashed)
            self.assertIsInstance(decrypted_hash, str)
            self.assertEqual(len(decrypted_hash), 64)  # SHA-256 hex

    def test_wrong_key_cannot_decrypt(self):
        """Test that wrong encryption key cannot decrypt data"""
        hash_table = initialize_hash_table()
        hash_table['categories'] = {'Groceries': 500.00}

        # Save with one key
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            save_hash_table(hash_table, self.cipher_suite)

        # Try to load with different key
        wrong_key = Fernet.generate_key()
        wrong_cipher = Fernet(wrong_key)

        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            with self.assertRaises(Exception):
                load_hash_table(wrong_cipher)

    def test_multiple_save_load_cycles_maintain_integrity(self):
        """Test that data remains intact through multiple save/load cycles"""
        hash_table = initialize_hash_table()

        # Perform 10 cycles of modification + save + load
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            for i in range(10):
                # Add data
                hash_table['transaction_ids'].append(f'tx_{i:03d}')
                hash_table['categories'][f'Category_{i}'] = i * 50.0

                # Save
                save_hash_table(hash_table, self.cipher_suite)

                # Load
                hash_table = load_hash_table(self.cipher_suite)

        # Verify all data persisted
        self.assertEqual(len(hash_table['transaction_ids']), 10)
        self.assertEqual(len(hash_table['categories']), 10)
        self.assertEqual(hash_table['categories']['Category_5'], 250.0)


class TestCSVCategoryManagerIntegration(unittest.TestCase):
    """
    Phase 2.2: Test CSV + Category Manager integration
    Uses real CSV parsing and categorization, mock only user prompts
    """

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.test_salt = b'integration_test_salt_123456789'
        self.hash_table = initialize_hash_table()

        # Create temp CSV file
        self.temp_csv = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.csv', encoding='utf-8'
        )
        self.temp_csv.close()

        # Create temp config file
        self.temp_config = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.json'
        )
        self.temp_config.close()

    def tearDown(self):
        """Clean up temp files"""
        for f in [self.temp_csv.name, self.temp_config.name]:
            if os.path.exists(f):
                os.unlink(f)

    def _write_csv(self, content):
        """Helper to write CSV content"""
        with open(self.temp_csv.name, 'w', encoding='utf-8') as f:
            f.write(content)

    @patch('package.read_data.cli.print_summary')
    @patch('package.read_data.cli.print_progress')
    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_process_csv_categorizes_transactions(
        self, mock_prompt, mock_get_cat, mock_print_tx, mock_progress, mock_summary
    ):
        """Test that CSV processing correctly categorizes transactions"""
        csv_content = """Date;Address;Amount
2024-01-01;Walmart;100.50
2024-01-02;Electric Company;150.00
2024-01-03;Walmart;75.25"""
        self._write_csv(csv_content)

        # Mock user selecting categories for new addresses
        mock_get_cat.side_effect = [
            "Groceries/Food",      # First Walmart
            "Utilities/Bills"      # Electric Company
            # Second Walmart should reuse existing category
        ]

        # Mock config with saved mapping
        mock_config = MagicMock()
        mock_config.get_column_mapping.return_value = {
            'date': 0, 'address': 1, 'amount': 2,
            'name': -1, 'type': -1, 'description': -1
        }

        with patch('package.read_data.Config') as mock_config_class:
            mock_config_class.load.return_value = mock_config

            # Process CSV
            stats = process_csv_file(
                self.temp_csv.name, self.hash_table,
                self.cipher_suite, self.test_salt
            )

        # Verify all transactions processed
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['processed'], 3)
        self.assertEqual(stats['skipped'], 0)

        # Verify categories created and totals calculated
        self.assertIn("Groceries/Food", self.hash_table['categories'])
        self.assertIn("Utilities/Bills", self.hash_table['categories'])
        self.assertAlmostEqual(
            self.hash_table['categories']["Groceries/Food"],
            175.75,  # 100.50 + 75.25
            places=2
        )
        self.assertEqual(self.hash_table['categories']["Utilities/Bills"], 150.00)

        # Verify user prompted only twice (not for second Walmart)
        self.assertEqual(mock_get_cat.call_count, 2)

        # Verify 2 unique addresses stored
        self.assertEqual(len(self.hash_table['addresses']), 2)

        # Verify 3 transaction IDs stored
        self.assertEqual(len(self.hash_table['transaction_ids']), 3)

    @patch('package.read_data.cli.print_summary')
    @patch('package.read_data.cli.print_progress')
    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.print_duplicate_warning')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_process_csv_detects_duplicate_transactions(
        self, mock_prompt, mock_get_cat, mock_dup_warn,
        mock_print_tx, mock_progress, mock_summary
    ):
        """Test that duplicate transactions are detected during CSV processing"""
        csv_content = """Date;Address;Amount
2024-01-01;Store A;100.00
2024-01-01;Store A;100.00"""  # Exact duplicate
        self._write_csv(csv_content)

        mock_get_cat.return_value = "Groceries/Food"
        mock_dup_warn.return_value = False  # User rejects duplicate

        mock_config = MagicMock()
        mock_config.get_column_mapping.return_value = {
            'date': 0, 'address': 1, 'amount': 2,
            'name': -1, 'type': -1, 'description': -1
        }

        with patch('package.read_data.Config') as mock_config_class:
            mock_config_class.load.return_value = mock_config

            stats = process_csv_file(
                self.temp_csv.name, self.hash_table,
                self.cipher_suite, self.test_salt
            )

        # Verify duplicate was detected and rejected
        self.assertEqual(stats['processed'], 2)  # Both processed (prompt shown)
        self.assertEqual(len(self.hash_table['transaction_ids']), 1)  # Only one added
        mock_dup_warn.assert_called_once()

    @patch('package.read_data.cli.print_summary')
    @patch('package.read_data.cli.print_progress')
    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_incremental_csv_processing(
        self, mock_prompt, mock_get_cat, mock_print_tx, mock_progress, mock_summary
    ):
        """Test processing multiple CSV files incrementally (realistic workflow)"""
        # First CSV (January)
        csv_jan = """Date;Address;Amount
2024-01-15;Walmart;85.50
2024-01-20;Target;67.99"""
        self._write_csv(csv_jan)

        mock_get_cat.side_effect = ["Groceries/Food", "Groceries/Food"]

        mock_config = MagicMock()
        mock_config.get_column_mapping.return_value = {
            'date': 0, 'address': 1, 'amount': 2,
            'name': -1, 'type': -1, 'description': -1
        }

        with patch('package.read_data.Config') as mock_config_class:
            mock_config_class.load.return_value = mock_config

            stats_jan = process_csv_file(
                self.temp_csv.name, self.hash_table,
                self.cipher_suite, self.test_salt
            )

        self.assertEqual(stats_jan['processed'], 2)
        self.assertAlmostEqual(
            self.hash_table['categories']["Groceries/Food"],
            153.49,
            places=2
        )

        # Second CSV (February) - same addresses
        csv_feb = """Date;Address;Amount
2024-02-10;Walmart;92.00
2024-02-15;Target;45.50"""
        self._write_csv(csv_feb)

        # Reset mock side effects for second file
        mock_get_cat.side_effect = []  # No new prompts (addresses known)

        with patch('package.read_data.Config') as mock_config_class:
            mock_config_class.load.return_value = mock_config

            stats_feb = process_csv_file(
                self.temp_csv.name, self.hash_table,
                self.cipher_suite, self.test_salt
            )

        # Verify incremental processing
        self.assertEqual(stats_feb['processed'], 2)
        self.assertAlmostEqual(
            self.hash_table['categories']["Groceries/Food"],
            290.99,  # 153.49 + 137.50
            places=2
        )

        # Should still have only 2 unique addresses
        self.assertEqual(len(self.hash_table['addresses']), 2)

        # Should have 4 transaction IDs
        self.assertEqual(len(self.hash_table['transaction_ids']), 4)


class TestFullPipelineIntegration(unittest.TestCase):
    """
    Phase 2.3: Test full pipeline with mocked user input only
    Uses real crypto, storage, CSV parsing, and categorization
    """

    def setUp(self):
        """Set up complete test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.test_salt = b'full_pipeline_test_salt_12345678'

        # Create temp files
        self.temp_csv = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.csv', encoding='utf-8'
        )
        self.temp_csv.close()

        self.temp_storage = tempfile.NamedTemporaryFile(
            delete=False, suffix='.enc'
        )
        self.temp_storage.close()

    def tearDown(self):
        """Clean up all temp files"""
        for f in [self.temp_csv.name, self.temp_storage.name]:
            if os.path.exists(f):
                os.unlink(f)

    @patch('package.read_data.cli.print_summary')
    @patch('package.read_data.cli.print_progress')
    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_complete_workflow_with_persistence(
        self, mock_prompt, mock_get_cat, mock_print_tx, mock_progress, mock_summary
    ):
        """Test complete workflow: CSV → categorize → encrypt → save → load → verify"""

        # Step 1: Create CSV with realistic data
        csv_content = """Date;Merchant;Amount;Description
2024-01-05;WALMART SUPERCENTER #1234;125.67;Groceries
2024-01-07;ELECTRIC COMPANY;89.50;Monthly bill
2024-01-10;NETFLIX.COM;15.99;Subscription
2024-01-12;WALMART SUPERCENTER #1234;67.43;Household items
2024-01-15;GAS COMPANY;75.00;Utility"""

        with open(self.temp_csv.name, 'w', encoding='utf-8') as f:
            f.write(csv_content)

        # Step 2: Setup mocks for user interaction
        mock_get_cat.side_effect = [
            "Groceries/Food",         # Walmart (first time)
            "Utilities/Bills",        # Electric
            "Entertainment/Leisure",  # Netflix
            "Utilities/Bills"         # Gas
            # Walmart second time reuses category
        ]

        mock_config = MagicMock()
        mock_config.get_column_mapping.return_value = {
            'date': 0, 'address': 1, 'amount': 2,
            'name': -1, 'type': -1, 'description': 3
        }

        # Step 3: Process CSV
        hash_table = initialize_hash_table()

        with patch('package.read_data.Config') as mock_config_class:
            mock_config_class.load.return_value = mock_config

            stats = process_csv_file(
                self.temp_csv.name, hash_table,
                self.cipher_suite, self.test_salt
            )

        # Verify processing stats
        self.assertEqual(stats['total'], 5)
        self.assertEqual(stats['processed'], 5)
        self.assertEqual(stats['skipped'], 0)
        self.assertEqual(stats['errors'], 0)

        # Step 4: Verify categorization
        self.assertEqual(len(hash_table['categories']), 3)
        self.assertAlmostEqual(
            hash_table['categories']['Groceries/Food'],
            193.10,  # 125.67 + 67.43
            places=2
        )
        self.assertAlmostEqual(
            hash_table['categories']['Utilities/Bills'],
            164.50,  # 89.50 + 75.00
            places=2
        )
        self.assertEqual(hash_table['categories']['Entertainment/Leisure'], 15.99)

        # Step 5: Save encrypted
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            save_hash_table(hash_table, self.cipher_suite)

        # Step 6: Verify file is encrypted
        with open(self.temp_storage.name, 'rb') as f:
            encrypted_content = f.read()
            # Should not contain plain text
            self.assertNotIn(b'Groceries', encrypted_content)
            self.assertNotIn(b'WALMART', encrypted_content)

        # Step 7: Load from encrypted storage
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            loaded_table = load_hash_table(self.cipher_suite)

        # Step 8: Verify loaded data matches original
        self.assertEqual(loaded_table['categories'], hash_table['categories'])
        self.assertEqual(
            len(loaded_table['transaction_ids']),
            len(hash_table['transaction_ids'])
        )
        self.assertEqual(
            len(loaded_table['addresses']),
            4  # 4 unique addresses
        )

        # Step 9: Verify addresses can be decrypted
        for encrypted_addr in loaded_table['addresses'].keys():
            decrypted = decrypt_address(encrypted_addr, self.cipher_suite)
            self.assertIsInstance(decrypted, str)
            self.assertEqual(len(decrypted), 64)  # SHA-256 hash

    @patch('package.read_data.cli.print_summary')
    @patch('package.read_data.cli.print_progress')
    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_multi_session_workflow(
        self, mock_prompt, mock_get_cat, mock_print_tx, mock_progress, mock_summary
    ):
        """Test realistic multi-session workflow: process → save → load → process more"""

        mock_config = MagicMock()
        mock_config.get_column_mapping.return_value = {
            'date': 0, 'address': 1, 'amount': 2,
            'name': -1, 'type': -1, 'description': -1
        }

        # === SESSION 1: Initial processing ===
        csv_session1 = """Date;Store;Amount
2024-01-01;Store A;100.00
2024-01-02;Store B;200.00"""

        with open(self.temp_csv.name, 'w') as f:
            f.write(csv_session1)

        hash_table = initialize_hash_table()
        mock_get_cat.side_effect = ["Groceries/Food", "Utilities/Bills"]

        with patch('package.read_data.Config') as mock_config_class:
            mock_config_class.load.return_value = mock_config
            process_csv_file(
                self.temp_csv.name, hash_table,
                self.cipher_suite, self.test_salt
            )

        # Save session 1
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            save_hash_table(hash_table, self.cipher_suite)

        # === SESSION 2: Load and continue ===
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            hash_table = load_hash_table(self.cipher_suite)

        # Process more transactions
        csv_session2 = """Date;Store;Amount
2024-01-03;Store A;150.00
2024-01-04;Store C;75.00"""

        with open(self.temp_csv.name, 'w') as f:
            f.write(csv_session2)

        mock_get_cat.side_effect = ["Entertainment/Leisure"]  # Only for Store C

        with patch('package.read_data.Config') as mock_config_class:
            mock_config_class.load.return_value = mock_config
            process_csv_file(
                self.temp_csv.name, hash_table,
                self.cipher_suite, self.test_salt
            )

        # Save session 2
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            save_hash_table(hash_table, self.cipher_suite)

        # === VERIFY: Load final state ===
        with patch('package.storage.HASH_TABLE_FILE', self.temp_storage.name):
            final_table = load_hash_table(self.cipher_suite)

        # Should have all data from both sessions
        self.assertEqual(len(final_table['categories']), 3)
        self.assertEqual(
            final_table['categories']['Groceries/Food'],
            250.00  # 100 + 150
        )
        self.assertEqual(final_table['categories']['Utilities/Bills'], 200.00)
        self.assertEqual(final_table['categories']['Entertainment/Leisure'], 75.00)

        # Should have 4 transactions total
        self.assertEqual(len(final_table['transaction_ids']), 4)

        # Should have 3 unique addresses
        self.assertEqual(len(final_table['addresses']), 3)


if __name__ == '__main__':
    unittest.main()
