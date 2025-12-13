"""
Unit tests for category manager edit functionality (Session 2)
"""

import unittest
from unittest.mock import MagicMock, patch
from cryptography.fernet import Fernet
from package.storage import initialize_hash_table
from package.category_manager import (
    get_all_addresses_with_categories,
    recategorize_address,
    search_addresses
)


class TestAddressRetrieval(unittest.TestCase):
    """Test address listing and search functions"""

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.hash_table = initialize_hash_table()

        # Add test data
        self.encrypted_addr1 = self.cipher_suite.encrypt(b"walmart_hash")
        self.encrypted_addr2 = self.cipher_suite.encrypt(b"target_hash")

        self.hash_table['addresses'][self.encrypted_addr1.decode()] = "Groceries/Food"
        self.hash_table['addresses'][self.encrypted_addr2.decode()] = "Shopping"

    def test_get_all_addresses_returns_list(self):
        """Test that get_all_addresses returns a list of tuples"""
        results = get_all_addresses_with_categories(self.hash_table, self.cipher_suite)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)

        # Each result should be a tuple of (address, category, encrypted_hash)
        for result in results:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 3)

    def test_search_addresses_finds_matches(self):
        """Test that search finds matching addresses"""
        # Search should find "walmart" in the encrypted addresses
        # Note: This is a simplified test since real addresses would be hashed
        results = search_addresses(self.hash_table, self.cipher_suite, "walmart")

        # Should find walmart_hash
        address_hashes = [r[0] for r in results]
        self.assertTrue(any("walmart" in addr for addr in address_hashes))

    def test_search_addresses_case_insensitive(self):
        """Test that search is case-insensitive"""
        results_lower = search_addresses(self.hash_table, self.cipher_suite, "walmart")
        results_upper = search_addresses(self.hash_table, self.cipher_suite, "WALMART")

        self.assertEqual(len(results_lower), len(results_upper))

    def test_search_addresses_no_matches(self):
        """Test that search returns empty list when no matches"""
        results = search_addresses(self.hash_table, self.cipher_suite, "nonexistent")

        self.assertEqual(len(results), 0)


class TestRecategorizeAddress(unittest.TestCase):
    """Test address recategorization function"""

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.hash_table = initialize_hash_table()

        # Add test data
        self.encrypted_addr = self.cipher_suite.encrypt(b"test_address_hash")
        self.hash_table['addresses'][self.encrypted_addr.decode()] = "Groceries/Food"
        self.hash_table['categories']['Groceries/Food'] = 150.00

    def test_recategorize_success(self):
        """Test successful recategorization"""
        success, message = recategorize_address(
            self.encrypted_addr.decode(),
            "Shopping",
            self.hash_table,
            self.cipher_suite
        )

        self.assertTrue(success)
        self.assertIn("recategorized", message.lower())
        self.assertEqual(self.hash_table['addresses'][self.encrypted_addr.decode()], "Shopping")

    def test_recategorize_nonexistent_address(self):
        """Test recategorization of non-existent address fails"""
        success, message = recategorize_address(
            "nonexistent_hash",
            "Shopping",
            self.hash_table,
            self.cipher_suite
        )

        self.assertFalse(success)
        self.assertIn("not found", message.lower())

    def test_recategorize_same_category(self):
        """Test that recategorizing to same category fails gracefully"""
        success, message = recategorize_address(
            self.encrypted_addr.decode(),
            "Groceries/Food",  # Same as current
            self.hash_table,
            self.cipher_suite
        )

        self.assertFalse(success)
        self.assertIn("already", message.lower())

    def test_recategorize_updates_hash_table(self):
        """Test that recategorization updates the hash table correctly"""
        old_category = self.hash_table['addresses'][self.encrypted_addr.decode()]

        success, _ = recategorize_address(
            self.encrypted_addr.decode(),
            "NewCategory",
            self.hash_table,
            self.cipher_suite
        )

        self.assertTrue(success)
        self.assertNotEqual(
            self.hash_table['addresses'][self.encrypted_addr.decode()],
            old_category
        )
        self.assertEqual(
            self.hash_table['addresses'][self.encrypted_addr.decode()],
            "NewCategory"
        )


if __name__ == '__main__':
    unittest.main()
