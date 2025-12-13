"""
Unit tests for storage filtering functionality (Session 3)
"""

import unittest
from package.storage import initialize_hash_table, filter_categories


class TestFilterCategories(unittest.TestCase):
    """Test category filtering functions"""

    def setUp(self):
        """Set up test environment"""
        self.hash_table = initialize_hash_table()

        # Add test data
        self.hash_table['categories'] = {
            'Groceries/Food': 450.75,
            'Utilities/Bills': 250.00,
            'Shopping': 125.50,
            'Entertainment': 75.25,
            'Salary': 3000.00,
            'Gifts/Donations': 50.00
        }

    def test_filter_no_filters_returns_all(self):
        """Test that no filters returns all categories"""
        result = filter_categories(self.hash_table)

        self.assertEqual(len(result), 6)
        self.assertEqual(result, self.hash_table['categories'])

    def test_filter_by_category_substring(self):
        """Test filtering by category name substring"""
        result = filter_categories(self.hash_table, category_filter="food")

        self.assertEqual(len(result), 1)
        self.assertIn('Groceries/Food', result)
        self.assertEqual(result['Groceries/Food'], 450.75)

    def test_filter_by_category_case_insensitive(self):
        """Test that category filter is case-insensitive"""
        result_lower = filter_categories(self.hash_table, category_filter="shopping")
        result_upper = filter_categories(self.hash_table, category_filter="SHOPPING")
        result_mixed = filter_categories(self.hash_table, category_filter="ShOpPiNg")

        self.assertEqual(result_lower, result_upper)
        self.assertEqual(result_lower, result_mixed)
        self.assertEqual(len(result_lower), 1)

    def test_filter_by_min_amount(self):
        """Test filtering by minimum amount"""
        result = filter_categories(self.hash_table, min_amount=200.00)

        self.assertEqual(len(result), 3)
        self.assertIn('Groceries/Food', result)
        self.assertIn('Utilities/Bills', result)
        self.assertIn('Salary', result)
        self.assertNotIn('Shopping', result)
        self.assertNotIn('Entertainment', result)

    def test_filter_by_max_amount(self):
        """Test filtering by maximum amount"""
        result = filter_categories(self.hash_table, max_amount=100.00)

        self.assertEqual(len(result), 2)
        self.assertIn('Entertainment', result)
        self.assertIn('Gifts/Donations', result)
        self.assertNotIn('Groceries/Food', result)
        self.assertNotIn('Salary', result)

    def test_filter_by_amount_range(self):
        """Test filtering by both min and max amount"""
        result = filter_categories(
            self.hash_table,
            min_amount=100.00,
            max_amount=500.00
        )

        self.assertEqual(len(result), 3)
        self.assertIn('Groceries/Food', result)
        self.assertIn('Utilities/Bills', result)
        self.assertIn('Shopping', result)
        self.assertNotIn('Entertainment', result)  # Too low
        self.assertNotIn('Salary', result)  # Too high

    def test_filter_by_category_and_amount(self):
        """Test combining category and amount filters"""
        result = filter_categories(
            self.hash_table,
            category_filter="s",  # Matches "Shopping", "Salary", "Groceries", "Utilities", "Gifts"
            min_amount=100.00
        )

        # Should match: Groceries (450.75), Utilities (250), Shopping (125.50), Salary (3000)
        # Not: Entertainment (no 's'), Gifts (< 100)
        self.assertIn('Groceries/Food', result)
        self.assertIn('Utilities/Bills', result)
        self.assertIn('Shopping', result)
        self.assertIn('Salary', result)
        self.assertNotIn('Entertainment', result)
        self.assertNotIn('Gifts/Donations', result)

    def test_filter_no_matches(self):
        """Test that empty dict returned when no matches"""
        result = filter_categories(self.hash_table, category_filter="NonexistentCategory")

        self.assertEqual(len(result), 0)
        self.assertEqual(result, {})

    def test_filter_exact_amount_match(self):
        """Test filtering with exact amount boundaries"""
        result = filter_categories(
            self.hash_table,
            min_amount=250.00,
            max_amount=250.00
        )

        self.assertEqual(len(result), 1)
        self.assertIn('Utilities/Bills', result)
        self.assertEqual(result['Utilities/Bills'], 250.00)

    def test_filter_empty_hash_table(self):
        """Test filtering empty hash table"""
        empty_table = initialize_hash_table()
        result = filter_categories(empty_table, category_filter="anything")

        self.assertEqual(len(result), 0)

    def test_filter_preserves_original(self):
        """Test that filtering doesn't modify original hash table"""
        original_categories = self.hash_table['categories'].copy()

        filter_categories(self.hash_table, category_filter="food")

        self.assertEqual(self.hash_table['categories'], original_categories)

    def test_filter_partial_category_match(self):
        """Test that partial matches work correctly"""
        # "i" appears in multiple categories
        result = filter_categories(self.hash_table, category_filter="i")

        # Should match: Groceries, Utilities, Shopping, Gifts
        self.assertIn('Groceries/Food', result)
        self.assertIn('Utilities/Bills', result)
        self.assertIn('Shopping', result)
        self.assertIn('Gifts/Donations', result)
        # Should NOT match: Salary, Entertainment
        self.assertEqual(len(result), 4)


if __name__ == '__main__':
    unittest.main()
