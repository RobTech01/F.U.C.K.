"""
Unit tests for bulk operations (Session 7)
"""

import unittest
from unittest.mock import MagicMock
from cryptography.fernet import Fernet
from package.storage import initialize_hash_table
from package.category_manager import bulk_recategorize


class TestBulkRecategorize(unittest.TestCase):
    """Test bulk recategorization function"""

    def setUp(self):
        """Set up test environment"""
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)
        self.hash_table = initialize_hash_table()

        # Add test data
        self.enc1 = self.cipher_suite.encrypt(b"walmart_store").decode()
        self.enc2 = self.cipher_suite.encrypt(b"walmart_online").decode()
        self.enc3 = self.cipher_suite.encrypt(b"target_store").decode()

        self.hash_table['addresses'] = {
            self.enc1: "Shopping",
            self.enc2: "Shopping",
            self.enc3: "Groceries/Food"
        }

    def test_bulk_recategorize_dry_run(self):
        """Test dry run doesn't modify data"""
        original_cat = self.hash_table['addresses'][self.enc1]

        count, affected = bulk_recategorize(
            "walmart",
            "Groceries/Food",
            self.hash_table,
            self.cipher_suite,
            dry_run=True
        )

        # Should find matches but not modify
        self.assertEqual(count, 2)
        self.assertEqual(len(affected), 2)
        self.assertEqual(self.hash_table['addresses'][self.enc1], original_cat)  # Unchanged

    def test_bulk_recategorize_actual_change(self):
        """Test actual recategorization modifies data"""
        count, affected = bulk_recategorize(
            "walmart",
            "Groceries/Food",
            self.hash_table,
            self.cipher_suite,
            dry_run=False
        )

        self.assertEqual(count, 2)
        self.assertEqual(self.hash_table['addresses'][self.enc1], "Groceries/Food")
        self.assertEqual(self.hash_table['addresses'][self.enc2], "Groceries/Food")
        self.assertEqual(self.hash_table['addresses'][self.enc3], "Groceries/Food")  # Unchanged

    def test_bulk_recategorize_no_matches(self):
        """Test with pattern that matches nothing"""
        count, affected = bulk_recategorize(
            "nonexistent",
            "NewCategory",
            self.hash_table,
            self.cipher_suite,
            dry_run=False
        )

        self.assertEqual(count, 0)
        self.assertEqual(len(affected), 0)

    def test_bulk_recategorize_case_insensitive(self):
        """Test pattern matching is case-insensitive"""
        count_lower, _ = bulk_recategorize(
            "walmart",
            "NewCat",
            self.hash_table,
            self.cipher_suite,
            dry_run=True
        )

        count_upper, _ = bulk_recategorize(
            "WALMART",
            "NewCat",
            self.hash_table,
            self.cipher_suite,
            dry_run=True
        )

        self.assertEqual(count_lower, count_upper)
        self.assertEqual(count_lower, 2)

    def test_bulk_recategorize_skips_same_category(self):
        """Test that addresses already in target category are skipped"""
        count, affected = bulk_recategorize(
            "walmart",
            "Shopping",  # Same as current
            self.hash_table,
            self.cipher_suite,
            dry_run=True
        )

        # Should find 0 because both walmart addresses are already in Shopping
        self.assertEqual(count, 0)

    def test_bulk_recategorize_partial_match(self):
        """Test partial string matching"""
        count, affected = bulk_recategorize(
            "store",  # Matches both walmart_store and target_store
            "Retail",
            self.hash_table,
            self.cipher_suite,
            dry_run=True
        )

        self.assertEqual(count, 2)  # walmart_store + target_store

    def test_bulk_recategorize_affected_list_format(self):
        """Test that affected list has correct format"""
        count, affected = bulk_recategorize(
            "walmart",
            "Groceries/Food",
            self.hash_table,
            self.cipher_suite,
            dry_run=True
        )

        self.assertEqual(len(affected), 2)
        for item in affected:
            self.assertIn(" (", item)  # Contains old category
            self.assertIn(" → ", item)  # Contains arrow
            self.assertIn("Groceries/Food", item)  # Contains new category


if __name__ == '__main__':
    unittest.main()
