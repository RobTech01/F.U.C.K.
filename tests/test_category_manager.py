"""
Unit tests for category_manager.py transaction categorization functions
"""

import unittest
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
from package.category_manager import (
    generate_transaction_id,
    find_category_by_address,
    categorize_transaction
)
from package.crypto import hash_address, encrypt_address
from package.storage import initialize_hash_table


class TestGenerateTransactionID(unittest.TestCase):
    """Test transaction ID generation"""

    def test_generate_id_with_hash(self):
        """Test generating transaction ID with hashed address"""
        tx_id = generate_transaction_id('2024-01-01', 100.50, 'abcd1234567890')

        self.assertIn('2024-01-01', tx_id)
        self.assertIn('abcd1234', tx_id)  # First 8 chars
        self.assertIn('100.5', tx_id)

    def test_generate_id_without_hash(self):
        """Test generating transaction ID without hashed address"""
        tx_id = generate_transaction_id('2024-01-15', 250.00)

        self.assertIn('2024-01-15', tx_id)
        self.assertIn('250', tx_id)

    def test_generate_id_deterministic(self):
        """Test that same inputs produce same ID"""
        tx_id1 = generate_transaction_id('2024-01-01', 100.50, 'hash12345')
        tx_id2 = generate_transaction_id('2024-01-01', 100.50, 'hash12345')

        self.assertEqual(tx_id1, tx_id2)

    def test_generate_id_different_dates(self):
        """Test that different dates produce different IDs"""
        tx_id1 = generate_transaction_id('2024-01-01', 100.00, 'hash123')
        tx_id2 = generate_transaction_id('2024-01-02', 100.00, 'hash123')

        self.assertNotEqual(tx_id1, tx_id2)

    def test_generate_id_different_amounts(self):
        """Test that different amounts produce different IDs"""
        tx_id1 = generate_transaction_id('2024-01-01', 100.00, 'hash123')
        tx_id2 = generate_transaction_id('2024-01-01', 200.00, 'hash123')

        self.assertNotEqual(tx_id1, tx_id2)


class TestFindCategoryByAddress(unittest.TestCase):
    """Test finding category by decrypting addresses"""

    def setUp(self):
        """Set up test cipher suite"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)

    def test_find_existing_category(self):
        """Test finding a category for an existing address"""
        # Setup encrypted hash
        address = "Walmart Supercenter"
        encrypted = encrypt_address(address, self.cipher_suite)
        encrypted_hash = {
            encrypted: "Groceries/Food"
        }

        # Find category
        category = find_category_by_address(encrypted_hash, address, self.cipher_suite)

        self.assertEqual(category, "Groceries/Food")

    def test_find_category_not_found(self):
        """Test that None is returned for unknown address"""
        # Setup with one address
        address1 = "Target"
        encrypted1 = encrypt_address(address1, self.cipher_suite)
        encrypted_hash = {
            encrypted1: "Groceries/Food"
        }

        # Search for different address
        category = find_category_by_address(encrypted_hash, "Best Buy", self.cipher_suite)

        self.assertIsNone(category)

    def test_find_category_multiple_addresses(self):
        """Test finding category among multiple addresses"""
        addresses = {
            "Walmart": "Groceries/Food",
            "Electric Company": "Utilities/Bills",
            "Target": "Groceries/Food",
            "Netflix": "Entertainment/Leisure"
        }

        # Encrypt all addresses
        encrypted_hash = {}
        for addr, cat in addresses.items():
            encrypted = encrypt_address(addr, self.cipher_suite)
            encrypted_hash[encrypted] = cat

        # Find each category
        for addr, expected_cat in addresses.items():
            category = find_category_by_address(encrypted_hash, addr, self.cipher_suite)
            self.assertEqual(category, expected_cat)

    def test_find_category_empty_hash(self):
        """Test with empty hash table"""
        category = find_category_by_address({}, "Any Address", self.cipher_suite)
        self.assertIsNone(category)


class TestCategorizeTransaction(unittest.TestCase):
    """Test transaction categorization logic"""

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.test_salt = b'test_salt_1234567890123456789012'
        self.hash_table = initialize_hash_table()
        self.categories = [
            "Groceries/Food",
            "Utilities/Bills",
            "Entertainment/Leisure"
        ]

    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_categorize_new_address(self, mock_prompt, mock_get_cat, mock_print):
        """Test categorizing a transaction with a new address"""
        transaction = {
            'date': '2024-01-01',
            'address': 'New Store',
            'amount': 100.50
        }

        # Mock user selecting category
        mock_get_cat.return_value = "Groceries/Food"

        # Categorize
        categorize_transaction(
            transaction, self.hash_table, self.cipher_suite,
            self.test_salt, self.categories
        )

        # Verify category was added
        self.assertIn("Groceries/Food", self.hash_table['categories'])
        self.assertEqual(self.hash_table['categories']["Groceries/Food"], 100.50)

        # Verify address was stored
        self.assertEqual(len(self.hash_table['addresses']), 1)

        # Verify user was prompted
        mock_prompt.assert_called_once()
        mock_get_cat.assert_called_once()

    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_categorize_existing_address(self, mock_prompt, mock_get_cat, mock_print):
        """Test categorizing with an existing address (no prompt)"""
        # Pre-populate hash table with an address
        address = "Walmart"
        hashed = hash_address(address, self.test_salt)
        encrypted = encrypt_address(hashed, self.cipher_suite)
        self.hash_table['addresses'][encrypted] = "Groceries/Food"
        self.hash_table['categories']["Groceries/Food"] = 50.00

        # New transaction with same address
        transaction = {
            'date': '2024-01-02',
            'address': address,
            'amount': 75.25
        }

        # Categorize
        categorize_transaction(
            transaction, self.hash_table, self.cipher_suite,
            self.test_salt, self.categories
        )

        # Verify amount was added to existing category
        self.assertEqual(self.hash_table['categories']["Groceries/Food"], 125.25)

        # Verify user was NOT prompted (existing address)
        mock_prompt.assert_not_called()
        mock_get_cat.assert_not_called()

    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.print_duplicate_warning')
    @patch('package.category_manager.cli.get_user_category')
    def test_categorize_duplicate_transaction_rejected(
        self, mock_get_cat, mock_dup_warn, mock_print
    ):
        """Test that duplicate transaction can be rejected"""
        transaction = {
            'date': '2024-01-01',
            'address': 'Store',
            'amount': 100.00
        }

        # First categorization (new address)
        mock_get_cat.return_value = "Groceries/Food"

        with patch('package.category_manager.cli.print_new_address_prompt'):
            categorize_transaction(
                transaction, self.hash_table, self.cipher_suite,
                self.test_salt, self.categories
            )

        initial_count = len(self.hash_table['transaction_ids'])
        initial_total = self.hash_table['categories']["Groceries/Food"]

        # Try to categorize same transaction again (rejected)
        mock_dup_warn.return_value = False  # User rejects duplicate

        categorize_transaction(
            transaction, self.hash_table, self.cipher_suite,
            self.test_salt, self.categories
        )

        # Verify transaction was NOT added again
        self.assertEqual(len(self.hash_table['transaction_ids']), initial_count)
        self.assertEqual(self.hash_table['categories']["Groceries/Food"], initial_total)

    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.print_duplicate_warning')
    @patch('package.category_manager.cli.get_user_category')
    def test_categorize_duplicate_transaction_accepted(
        self, mock_get_cat, mock_dup_warn, mock_print
    ):
        """Test that duplicate transaction can be accepted"""
        transaction = {
            'date': '2024-01-01',
            'address': 'Store',
            'amount': 100.00
        }

        # First categorization
        mock_get_cat.return_value = "Groceries/Food"

        with patch('package.category_manager.cli.print_new_address_prompt'):
            categorize_transaction(
                transaction, self.hash_table, self.cipher_suite,
                self.test_salt, self.categories
            )

        initial_total = self.hash_table['categories']["Groceries/Food"]

        # Try to categorize same transaction again (accepted)
        mock_dup_warn.return_value = True  # User accepts duplicate

        categorize_transaction(
            transaction, self.hash_table, self.cipher_suite,
            self.test_salt, self.categories
        )

        # Verify amount was added again
        self.assertEqual(self.hash_table['categories']["Groceries/Food"], initial_total + 100.00)

    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_categorize_multiple_transactions(self, mock_prompt, mock_get_cat, mock_print):
        """Test categorizing multiple transactions to different categories"""
        transactions = [
            {'date': '2024-01-01', 'address': 'Walmart', 'amount': 50.00},
            {'date': '2024-01-02', 'address': 'Electric Co', 'amount': 150.00},
            {'date': '2024-01-03', 'address': 'Netflix', 'amount': 15.99},
        ]

        categories_selected = ["Groceries/Food", "Utilities/Bills", "Entertainment/Leisure"]
        mock_get_cat.side_effect = categories_selected

        # Categorize all
        for tx in transactions:
            categorize_transaction(
                tx, self.hash_table, self.cipher_suite,
                self.test_salt, self.categories
            )

        # Verify all categories created
        self.assertEqual(len(self.hash_table['categories']), 3)
        self.assertEqual(self.hash_table['categories']["Groceries/Food"], 50.00)
        self.assertEqual(self.hash_table['categories']["Utilities/Bills"], 150.00)
        self.assertEqual(self.hash_table['categories']["Entertainment/Leisure"], 15.99)

        # Verify all addresses stored
        self.assertEqual(len(self.hash_table['addresses']), 3)

    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_categorize_accumulates_category_totals(self, mock_prompt, mock_get_cat, mock_print):
        """Test that amounts accumulate correctly in categories"""
        transactions = [
            {'date': '2024-01-01', 'address': 'Walmart', 'amount': 50.00},
            {'date': '2024-01-02', 'address': 'Target', 'amount': 75.00},
            {'date': '2024-01-03', 'address': 'Costco', 'amount': 100.00},
        ]

        # All go to same category
        mock_get_cat.return_value = "Groceries/Food"

        for tx in transactions:
            categorize_transaction(
                tx, self.hash_table, self.cipher_suite,
                self.test_salt, self.categories
            )

        # Verify total
        self.assertEqual(self.hash_table['categories']["Groceries/Food"], 225.00)

    def test_categorize_invalid_hash_table_type(self):
        """Test that TypeError is raised for invalid hash_table type"""
        transaction = {'date': '2024-01-01', 'address': 'Store', 'amount': 100.00}

        with self.assertRaises(TypeError):
            categorize_transaction(
                transaction, "not_a_dict", self.cipher_suite,
                self.test_salt, self.categories
            )

    def test_categorize_invalid_transaction_type(self):
        """Test that TypeError is raised for invalid transaction type"""
        with self.assertRaises(TypeError):
            categorize_transaction(
                "not_a_dict", self.hash_table, self.cipher_suite,
                self.test_salt, self.categories
            )

    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_categorize_uses_default_categories(self, mock_prompt, mock_get_cat, mock_print):
        """Test that default categories are loaded when not provided"""
        transaction = {'date': '2024-01-01', 'address': 'Store', 'amount': 100.00}
        mock_get_cat.return_value = "Groceries/Food"

        # Don't pass categories parameter
        categorize_transaction(
            transaction, self.hash_table, self.cipher_suite, self.test_salt
        )

        # Should work with default categories from Config
        mock_get_cat.assert_called_once()
        # Verify first arg is a list of categories
        self.assertIsInstance(mock_get_cat.call_args[0][0], list)


class TestCategoryManagerIntegration(unittest.TestCase):
    """Test realistic category manager workflows"""

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.test_salt = b'test_salt_1234567890123456789012'
        self.hash_table = initialize_hash_table()
        self.categories = ["Groceries/Food", "Utilities/Bills", "Entertainment/Leisure"]

    @patch('package.category_manager.cli.print_transaction_info')
    @patch('package.category_manager.cli.get_user_category')
    @patch('package.category_manager.cli.print_new_address_prompt')
    def test_realistic_monthly_workflow(self, mock_prompt, mock_get_cat, mock_print):
        """Test realistic workflow of processing monthly transactions"""
        # Simulate a month of transactions
        transactions = [
            # Week 1
            {'date': '2024-01-01', 'address': 'Walmart', 'amount': 85.50},
            {'date': '2024-01-02', 'address': 'Electric Company', 'amount': 120.00},
            {'date': '2024-01-03', 'address': 'Walmart', 'amount': 42.30},  # Repeat address
            # Week 2
            {'date': '2024-01-08', 'address': 'Target', 'amount': 67.99},
            {'date': '2024-01-09', 'address': 'Netflix', 'amount': 15.99},
            {'date': '2024-01-10', 'address': 'Walmart', 'amount': 55.20},  # Repeat again
            # Week 3
            {'date': '2024-01-15', 'address': 'Gas Company', 'amount': 80.00},
            {'date': '2024-01-16', 'address': 'Target', 'amount': 34.50},  # Repeat
        ]

        # Mock user selections for new addresses only
        mock_get_cat.side_effect = [
            "Groceries/Food",      # Walmart (new)
            "Utilities/Bills",     # Electric (new)
            "Groceries/Food",      # Target (new)
            "Entertainment/Leisure", # Netflix (new)
            "Utilities/Bills",     # Gas (new)
        ]

        # Process all transactions
        for tx in transactions:
            categorize_transaction(
                tx, self.hash_table, self.cipher_suite,
                self.test_salt, self.categories
            )

        # Verify results
        # Should have 5 unique addresses
        self.assertEqual(len(self.hash_table['addresses']), 5)

        # Should have 3 categories with correct totals
        self.assertAlmostEqual(
            self.hash_table['categories']['Groceries/Food'],
            85.50 + 42.30 + 67.99 + 55.20 + 34.50,
            places=2
        )
        self.assertAlmostEqual(
            self.hash_table['categories']['Utilities/Bills'],
            120.00 + 80.00,
            places=2
        )
        self.assertEqual(
            self.hash_table['categories']['Entertainment/Leisure'],
            15.99
        )

        # Should have prompted user only 5 times (for new addresses)
        self.assertEqual(mock_get_cat.call_count, 5)

        # Should have 8 transaction IDs
        self.assertEqual(len(self.hash_table['transaction_ids']), 8)


if __name__ == '__main__':
    unittest.main()
