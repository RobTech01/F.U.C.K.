"""
Unit tests for reports module (Session 6)
"""

import unittest
from package.reports import (
    generate_category_breakdown,
    generate_ascii_bar,
    format_category_report,
    get_top_categories,
    calculate_category_statistics
)


class TestCategoryBreakdown(unittest.TestCase):
    """Test category breakdown generation"""

    def test_breakdown_with_data(self):
        """Test breakdown with normal category data"""
        categories = {
            'Groceries/Food': 450.75,
            'Utilities/Bills': 250.00,
            'Entertainment': 75.25
        }

        result = generate_category_breakdown(categories)

        self.assertTrue(result['has_data'])
        self.assertEqual(result['total'], 776.00)
        self.assertEqual(result['count'], 3)
        self.assertEqual(len(result['categories']), 3)

        # Check sorted by amount descending
        self.assertEqual(result['categories'][0]['category'], 'Groceries/Food')
        self.assertEqual(result['categories'][1]['category'], 'Utilities/Bills')
        self.assertEqual(result['categories'][2]['category'], 'Entertainment')

    def test_breakdown_calculates_percentages(self):
        """Test that percentages are calculated correctly"""
        categories = {'Category A': 50.00, 'Category B': 50.00}

        result = generate_category_breakdown(categories)

        for cat_data in result['categories']:
            self.assertAlmostEqual(cat_data['percentage'], 50.0, places=1)

    def test_breakdown_empty_categories(self):
        """Test breakdown with empty categories"""
        result = generate_category_breakdown({})

        self.assertFalse(result['has_data'])
        self.assertEqual(result['total'], 0.0)

    def test_breakdown_single_category(self):
        """Test breakdown with single category"""
        categories = {'Only One': 100.00}

        result = generate_category_breakdown(categories)

        self.assertTrue(result['has_data'])
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['categories'][0]['percentage'], 100.0)


class TestASCIIBar(unittest.TestCase):
    """Test ASCII bar generation"""

    def test_ascii_bar_full_width(self):
        """Test bar at maximum value"""
        bar = generate_ascii_bar(100.0, 100.0, bar_width=10)

        self.assertEqual(len(bar), 10)
        self.assertTrue(all(c == '█' for c in bar))

    def test_ascii_bar_half_width(self):
        """Test bar at half of maximum"""
        bar = generate_ascii_bar(50.0, 100.0, bar_width=10)

        self.assertEqual(len(bar), 5)

    def test_ascii_bar_zero_value(self):
        """Test bar with zero value"""
        bar = generate_ascii_bar(0.0, 100.0, bar_width=10)

        self.assertEqual(len(bar), 0)

    def test_ascii_bar_zero_max(self):
        """Test bar when max is zero"""
        bar = generate_ascii_bar(50.0, 0.0, bar_width=10)

        self.assertEqual(bar, "")

    def test_ascii_bar_negative_value(self):
        """Test bar with negative value (uses absolute)"""
        bar = generate_ascii_bar(-50.0, 100.0, bar_width=10)

        self.assertEqual(len(bar), 5)


class TestTopCategories(unittest.TestCase):
    """Test top categories extraction"""

    def test_get_top_categories_default_limit(self):
        """Test getting top 5 categories"""
        categories = {
            f'Category{i}': float(i * 10)
            for i in range(10, 0, -1)
        }

        top = get_top_categories(categories, limit=5)

        self.assertEqual(len(top), 5)
        self.assertEqual(top[0][0], 'Category10')  # Highest
        self.assertEqual(top[0][1], 100.0)

    def test_get_top_categories_fewer_than_limit(self):
        """Test when there are fewer categories than limit"""
        categories = {'A': 100.0, 'B': 50.0}

        top = get_top_categories(categories, limit=5)

        self.assertEqual(len(top), 2)

    def test_get_top_categories_empty(self):
        """Test with empty categories"""
        top = get_top_categories({}, limit=5)

        self.assertEqual(len(top), 0)


class TestCategoryStatistics(unittest.TestCase):
    """Test category statistics calculation"""

    def test_statistics_with_data(self):
        """Test statistics with normal data"""
        categories = {
            'A': 100.0,
            'B': 200.0,
            'C': 300.0
        }

        stats = calculate_category_statistics(categories)

        self.assertEqual(stats['mean'], 200.0)
        self.assertEqual(stats['median'], 200.0)
        self.assertEqual(stats['highest'], ('C', 300.0))
        self.assertEqual(stats['lowest'], ('A', 100.0))

    def test_statistics_even_count(self):
        """Test median with even number of categories"""
        categories = {
            'A': 100.0,
            'B': 200.0,
            'C': 300.0,
            'D': 400.0
        }

        stats = calculate_category_statistics(categories)

        self.assertEqual(stats['median'], 250.0)  # (200 + 300) / 2

    def test_statistics_odd_count(self):
        """Test median with odd number of categories"""
        categories = {
            'A': 100.0,
            'B': 200.0,
            'C': 300.0
        }

        stats = calculate_category_statistics(categories)

        self.assertEqual(stats['median'], 200.0)

    def test_statistics_empty(self):
        """Test statistics with no data"""
        stats = calculate_category_statistics({})

        self.assertEqual(stats['mean'], 0.0)
        self.assertEqual(stats['median'], 0.0)
        self.assertIsNone(stats['highest'])
        self.assertIsNone(stats['lowest'])


class TestFormatCategoryReport(unittest.TestCase):
    """Test report formatting"""

    def test_format_report_with_bars(self):
        """Test formatting with bars enabled"""
        report_data = {
            'total': 100.0,
            'count': 2,
            'has_data': True,
            'categories': [
                {'category': 'A', 'amount': 60.0, 'percentage': 60.0},
                {'category': 'B', 'amount': 40.0, 'percentage': 40.0}
            ]
        }

        output = format_category_report(report_data, show_bars=True)

        self.assertIn('SPENDING BREAKDOWN', output)
        self.assertIn('Total: $100.00', output)
        self.assertIn('Categories: 2', output)
        self.assertIn('A', output)
        self.assertIn('60.0%', output)
        self.assertIn('█', output)  # Bar character

    def test_format_report_without_bars(self):
        """Test formatting with bars disabled"""
        report_data = {
            'total': 100.0,
            'count': 1,
            'has_data': True,
            'categories': [
                {'category': 'A', 'amount': 100.0, 'percentage': 100.0}
            ]
        }

        output = format_category_report(report_data, show_bars=False)

        self.assertIn('SPENDING BREAKDOWN', output)
        # Should not have excessive empty lines from bars
        self.assertNotIn('███', output)  # No bars should appear

    def test_format_report_no_data(self):
        """Test formatting with no data"""
        report_data = {
            'total': 0.0,
            'has_data': False,
            'categories': []
        }

        output = format_category_report(report_data, show_bars=True)

        self.assertIn('No data available', output)


if __name__ == '__main__':
    unittest.main()
