"""
Unit tests for patterns CLI integration
"""

import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
from package.cli import display_merchant_patterns


class TestDisplayMerchantPatterns(unittest.TestCase):
    """Test merchant patterns display function"""

    def test_display_empty_merchants(self):
        """Test displaying with no merchants"""
        merchants = []
        investment_data = {
            'investment_total': 0.0,
            'consumption_total': 0.0,
            'total_spending': 0.0,
            'investment_rate': 0.0,
            'investment_breakdown': {}
        }

        with patch('sys.stdout', new=StringIO()) as output:
            display_merchant_patterns(merchants, investment_data)
            result = output.getvalue()

        self.assertIn('No transaction data available', result)

    def test_display_single_merchant(self):
        """Test displaying single merchant"""
        merchants = [
            {
                'address': 'Test Store',
                'count': 5,
                'total': 500.00,
                'avg_amount': 100.00,
                'regularity': 'monthly',
                'category': 'Food'
            }
        ]
        investment_data = {
            'investment_total': 0.0,
            'consumption_total': 500.0,
            'total_spending': 500.0,
            'investment_rate': 0.0,
            'investment_breakdown': {}
        }

        with patch('sys.stdout', new=StringIO()) as output:
            display_merchant_patterns(merchants, investment_data)
            result = output.getvalue()

        self.assertIn('Test Store', result)
        self.assertIn('$500.00', result)
        self.assertIn('monthly', result.lower())
        self.assertIn('Food', result)

    def test_display_multiple_merchants(self):
        """Test displaying multiple merchants"""
        merchants = [
            {
                'address': 'Store A',
                'count': 10,
                'total': 1000.00,
                'avg_amount': 100.00,
                'regularity': 'weekly',
                'category': 'Food'
            },
            {
                'address': 'Store B',
                'count': 5,
                'total': 500.00,
                'avg_amount': 100.00,
                'regularity': 'monthly',
                'category': 'Utilities'
            }
        ]
        investment_data = {
            'investment_total': 0.0,
            'consumption_total': 1500.0,
            'total_spending': 1500.0,
            'investment_rate': 0.0,
            'investment_breakdown': {}
        }

        with patch('sys.stdout', new=StringIO()) as output:
            display_merchant_patterns(merchants, investment_data)
            result = output.getvalue()

        self.assertIn('Store A', result)
        self.assertIn('Store B', result)
        self.assertIn('weekly', result.lower())
        self.assertIn('monthly', result.lower())

    def test_display_regularity_breakdown(self):
        """Test regularity breakdown section"""
        merchants = [
            {'address': 'A', 'count': 1, 'total': 100, 'avg_amount': 100, 'regularity': 'weekly', 'category': 'Food'},
            {'address': 'B', 'count': 1, 'total': 200, 'avg_amount': 200, 'regularity': 'weekly', 'category': 'Food'},
            {'address': 'C', 'count': 1, 'total': 300, 'avg_amount': 300, 'regularity': 'monthly', 'category': 'Bills'},
        ]
        investment_data = {
            'investment_total': 0.0,
            'consumption_total': 600.0,
            'total_spending': 600.0,
            'investment_rate': 0.0,
            'investment_breakdown': {}
        }

        with patch('sys.stdout', new=StringIO()) as output:
            display_merchant_patterns(merchants, investment_data)
            result = output.getvalue()

        self.assertIn('REGULARITY BREAKDOWN', result)
        self.assertIn('Weekly', result)
        self.assertIn('Monthly', result)
        # Should show 2 weekly (66.7%) and 1 monthly (33.3%)
        self.assertIn('2', result)  # Count of weekly

    def test_display_investment_rate(self):
        """Test investment vs consumption display"""
        merchants = [
            {'address': 'Investment Broker', 'count': 2, 'total': 2000, 'avg_amount': 1000, 'regularity': 'monthly', 'category': 'Savings'}
        ]
        investment_data = {
            'investment_total': 2000.0,
            'consumption_total': 500.0,
            'total_spending': 2500.0,
            'investment_rate': 80.0,
            'investment_breakdown': {
                'Savings': 2000.0
            }
        }

        with patch('sys.stdout', new=StringIO()) as output:
            display_merchant_patterns(merchants, investment_data)
            result = output.getvalue()

        self.assertIn('INVESTMENT VS. CONSUMPTION', result)
        self.assertIn('$2,000.00', result)
        self.assertIn('80.0%', result)
        self.assertIn('$2,500.00', result)  # Total
        self.assertIn('Savings', result)

    def test_display_respects_limit(self):
        """Test that limit parameter works"""
        merchants = [
            {'address': f'Store {i}', 'count': 1, 'total': 100-i, 'avg_amount': 100-i, 'regularity': 'single', 'category': 'Food'}
            for i in range(20)
        ]
        investment_data = {
            'investment_total': 0.0,
            'consumption_total': sum(m['total'] for m in merchants),
            'total_spending': sum(m['total'] for m in merchants),
            'investment_rate': 0.0,
            'investment_breakdown': {}
        }

        with patch('sys.stdout', new=StringIO()) as output:
            display_merchant_patterns(merchants, investment_data, limit=5)
            result = output.getvalue()

        # Should only show first 5 merchants
        self.assertIn('Store 0', result)
        self.assertIn('Store 4', result)
        # Should not show beyond limit
        self.assertNotIn('Store 10', result)

    def test_display_long_merchant_name_truncated(self):
        """Test that very long merchant names are truncated"""
        long_name = 'A' * 100  # 100 character name
        merchants = [
            {
                'address': long_name,
                'count': 1,
                'total': 100.00,
                'avg_amount': 100.00,
                'regularity': 'single',
                'category': 'Food'
            }
        ]
        investment_data = {
            'investment_total': 0.0,
            'consumption_total': 100.0,
            'total_spending': 100.0,
            'investment_rate': 0.0,
            'investment_breakdown': {}
        }

        with patch('sys.stdout', new=StringIO()) as output:
            display_merchant_patterns(merchants, investment_data)
            result = output.getvalue()

        # Name should be truncated to 50 chars in display
        self.assertIn('A' * 50, result)

    def test_display_all_regularity_types(self):
        """Test display with all regularity types"""
        merchants = [
            {'address': 'Weekly Store', 'count': 2, 'total': 100, 'avg_amount': 50, 'regularity': 'weekly', 'category': 'Food'},
            {'address': 'Monthly Subscription', 'count': 3, 'total': 90, 'avg_amount': 30, 'regularity': 'monthly', 'category': 'Entertainment'},
            {'address': 'Yearly Payment', 'count': 2, 'total': 200, 'avg_amount': 100, 'regularity': 'yearly', 'category': 'Insurance'},
            {'address': 'Irregular Purchase', 'count': 2, 'total': 150, 'avg_amount': 75, 'regularity': 'irregular', 'category': 'Misc'},
            {'address': 'Single Purchase', 'count': 1, 'total': 50, 'avg_amount': 50, 'regularity': 'single', 'category': 'Misc'}
        ]
        investment_data = {
            'investment_total': 0.0,
            'consumption_total': 590.0,
            'total_spending': 590.0,
            'investment_rate': 0.0,
            'investment_breakdown': {}
        }

        with patch('sys.stdout', new=StringIO()) as output:
            display_merchant_patterns(merchants, investment_data)
            result = output.getvalue()

        # All regularity types should appear
        for regularity in ['weekly', 'monthly', 'yearly', 'irregular', 'single']:
            self.assertIn(regularity.capitalize(), result)


if __name__ == '__main__':
    unittest.main()
