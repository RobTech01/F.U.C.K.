"""
Unit tests for patterns.py merchant analysis functions
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock
from package.patterns import (
    parse_date,
    calculate_date_interval,
    categorize_regularity,
    analyze_merchants,
    calculate_investment_rate,
    get_top_merchants,
    get_merchants_by_regularity
)


class TestParseDate(unittest.TestCase):
    """Test date parsing function"""

    def test_parse_iso_format(self):
        """Test parsing ISO format (YYYY-MM-DD)"""
        date = parse_date('2024-01-15')
        self.assertEqual(date.year, 2024)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 15)

    def test_parse_european_format(self):
        """Test parsing European format (DD.MM.YYYY)"""
        date = parse_date('15.01.2024')
        self.assertEqual(date.year, 2024)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 15)

    def test_parse_us_format(self):
        """Test parsing US format (MM/DD/YYYY)"""
        date = parse_date('01/15/2024')
        self.assertEqual(date.year, 2024)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 15)

    def test_parse_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError"""
        with self.assertRaises(ValueError):
            parse_date('invalid-date')

    def test_parse_empty_string_raises_error(self):
        """Test that empty string raises ValueError"""
        with self.assertRaises(ValueError):
            parse_date('')


class TestCalculateDateInterval(unittest.TestCase):
    """Test date interval calculation"""

    def test_interval_same_month(self):
        """Test interval calculation within same month"""
        days = calculate_date_interval('2024-01-01', '2024-01-15')
        self.assertEqual(days, 14)

    def test_interval_different_months(self):
        """Test interval calculation across months"""
        days = calculate_date_interval('2024-01-15', '2024-02-15')
        self.assertEqual(days, 31)

    def test_interval_reversed_dates(self):
        """Test that order doesn't matter (absolute value)"""
        days1 = calculate_date_interval('2024-01-01', '2024-01-15')
        days2 = calculate_date_interval('2024-01-15', '2024-01-01')
        self.assertEqual(days1, days2)

    def test_interval_one_year(self):
        """Test interval of one year"""
        days = calculate_date_interval('2024-01-01', '2025-01-01')
        self.assertEqual(days, 366)  # 2024 is a leap year


class TestCategorizeRegularity(unittest.TestCase):
    """Test regularity categorization"""

    def test_weekly_regularity(self):
        """Test weekly pattern detection"""
        self.assertEqual(categorize_regularity(7), 'weekly')
        self.assertEqual(categorize_regularity(5), 'weekly')
        self.assertEqual(categorize_regularity(10), 'weekly')

    def test_monthly_regularity(self):
        """Test monthly pattern detection"""
        self.assertEqual(categorize_regularity(30), 'monthly')
        self.assertEqual(categorize_regularity(20), 'monthly')
        self.assertEqual(categorize_regularity(40), 'monthly')

    def test_yearly_regularity(self):
        """Test yearly pattern detection"""
        self.assertEqual(categorize_regularity(365), 'yearly')
        self.assertEqual(categorize_regularity(330), 'yearly')
        self.assertEqual(categorize_regularity(400), 'yearly')

    def test_irregular_pattern(self):
        """Test irregular pattern detection"""
        self.assertEqual(categorize_regularity(15), 'irregular')
        self.assertEqual(categorize_regularity(45), 'irregular')
        self.assertEqual(categorize_regularity(100), 'irregular')


class TestAnalyzeMerchants(unittest.TestCase):
    """Test merchant analysis function"""

    def setUp(self):
        """Set up mock cipher suite"""
        self.mock_cipher = MagicMock()
        # Mock decrypt to return a simple identifier
        self.mock_cipher.decrypt = lambda x: x.decode() if isinstance(x, bytes) else x

    def test_analyze_empty_transactions(self):
        """Test with no transactions"""
        result = analyze_merchants([], self.mock_cipher)
        self.assertEqual(result, [])

    def test_analyze_single_merchant_single_transaction(self):
        """Test single merchant with one transaction"""
        transactions = [
            {
                'date': '2024-01-15',
                'address_hash': 'merchant_a',
                'amount': 100.00,
                'category': 'Food'
            }
        ]

        result = analyze_merchants(transactions, self.mock_cipher)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['count'], 1)
        self.assertEqual(result[0]['total'], 100.00)
        self.assertEqual(result[0]['avg_amount'], 100.00)
        self.assertEqual(result[0]['regularity'], 'single')
        self.assertEqual(result[0]['category'], 'Food')

    def test_analyze_merchant_with_weekly_pattern(self):
        """Test merchant with weekly purchase pattern"""
        transactions = [
            {'date': '2024-01-01', 'address_hash': 'grocery', 'amount': 50.00, 'category': 'Food'},
            {'date': '2024-01-08', 'address_hash': 'grocery', 'amount': 55.00, 'category': 'Food'},
            {'date': '2024-01-15', 'address_hash': 'grocery', 'amount': 52.00, 'category': 'Food'}
        ]

        result = analyze_merchants(transactions, self.mock_cipher)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['count'], 3)
        self.assertEqual(result[0]['total'], 157.00)
        self.assertEqual(result[0]['regularity'], 'weekly')

    def test_analyze_merchant_with_monthly_pattern(self):
        """Test merchant with monthly subscription pattern"""
        transactions = [
            {'date': '2024-01-15', 'address_hash': 'netflix', 'amount': 15.99, 'category': 'Entertainment'},
            {'date': '2024-02-15', 'address_hash': 'netflix', 'amount': 15.99, 'category': 'Entertainment'},
            {'date': '2024-03-15', 'address_hash': 'netflix', 'amount': 15.99, 'category': 'Entertainment'}
        ]

        result = analyze_merchants(transactions, self.mock_cipher)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['count'], 3)
        self.assertAlmostEqual(result[0]['total'], 47.97, places=2)
        self.assertEqual(result[0]['regularity'], 'monthly')

    def test_analyze_multiple_merchants_sorted_by_total(self):
        """Test multiple merchants are sorted by total spending"""
        transactions = [
            {'date': '2024-01-15', 'address_hash': 'merchant_a', 'amount': 100.00, 'category': 'Food'},
            {'date': '2024-01-16', 'address_hash': 'merchant_b', 'amount': 500.00, 'category': 'Utilities'},
            {'date': '2024-01-17', 'address_hash': 'merchant_c', 'amount': 50.00, 'category': 'Entertainment'}
        ]

        result = analyze_merchants(transactions, self.mock_cipher)

        self.assertEqual(len(result), 3)
        # Should be sorted by total spending (descending)
        self.assertEqual(result[0]['total'], 500.00)  # merchant_b
        self.assertEqual(result[1]['total'], 100.00)  # merchant_a
        self.assertEqual(result[2]['total'], 50.00)   # merchant_c

    def test_analyze_merchant_category_most_common(self):
        """Test that most common category is selected"""
        transactions = [
            {'date': '2024-01-15', 'address_hash': 'amazon', 'amount': 50.00, 'category': 'Entertainment'},
            {'date': '2024-01-20', 'address_hash': 'amazon', 'amount': 75.00, 'category': 'Food'},
            {'date': '2024-01-25', 'address_hash': 'amazon', 'amount': 100.00, 'category': 'Food'}
        ]

        result = analyze_merchants(transactions, self.mock_cipher)

        # Most common category is 'Food' (appears twice)
        self.assertEqual(result[0]['category'], 'Food')

    def test_analyze_irregular_pattern(self):
        """Test merchant with irregular purchase pattern"""
        transactions = [
            {'date': '2024-01-01', 'address_hash': 'store', 'amount': 50.00, 'category': 'Misc'},
            {'date': '2024-01-15', 'address_hash': 'store', 'amount': 75.00, 'category': 'Misc'},
            {'date': '2024-02-20', 'address_hash': 'store', 'amount': 100.00, 'category': 'Misc'}
        ]

        result = analyze_merchants(transactions, self.mock_cipher)

        # Intervals: 14 days, 36 days -> avg ~25 days (irregular, not quite weekly or monthly)
        self.assertEqual(result[0]['regularity'], 'irregular')


class TestCalculateInvestmentRate(unittest.TestCase):
    """Test investment rate calculation"""

    def test_all_consumption(self):
        """Test with only consumption transactions"""
        transactions = [
            {'amount': 100.00, 'category': 'Food'},
            {'amount': 50.00, 'category': 'Entertainment'},
            {'amount': 75.00, 'category': 'Utilities/Bills'}
        ]

        result = calculate_investment_rate(transactions)

        self.assertEqual(result['investment_total'], 0.0)
        self.assertEqual(result['consumption_total'], 225.0)
        self.assertEqual(result['total_spending'], 225.0)
        self.assertEqual(result['investment_rate'], 0.0)

    def test_all_investment(self):
        """Test with only investment transactions"""
        transactions = [
            {'amount': 500.00, 'category': 'Savings'},
            {'amount': 1000.00, 'category': 'Stable Investments'},
            {'amount': 200.00, 'category': 'Retirement'}
        ]

        result = calculate_investment_rate(transactions)

        self.assertEqual(result['investment_total'], 1700.0)
        self.assertEqual(result['consumption_total'], 0.0)
        self.assertEqual(result['total_spending'], 1700.0)
        self.assertEqual(result['investment_rate'], 100.0)

    def test_mixed_transactions(self):
        """Test with mixed investment and consumption"""
        transactions = [
            {'amount': 500.00, 'category': 'Savings'},
            {'amount': 100.00, 'category': 'Food'},
            {'amount': 200.00, 'category': 'Stable Investments'},
            {'amount': 50.00, 'category': 'Entertainment'}
        ]

        result = calculate_investment_rate(transactions)

        self.assertEqual(result['investment_total'], 700.0)
        self.assertEqual(result['consumption_total'], 150.0)
        self.assertEqual(result['total_spending'], 850.0)
        self.assertAlmostEqual(result['investment_rate'], 82.35, places=2)

    def test_investment_breakdown(self):
        """Test investment breakdown by category"""
        transactions = [
            {'amount': 500.00, 'category': 'Savings'},
            {'amount': 1000.00, 'category': 'Stable Investments'},
            {'amount': 200.00, 'category': 'Savings'}
        ]

        result = calculate_investment_rate(transactions)

        self.assertEqual(result['investment_breakdown']['Savings'], 700.0)
        self.assertEqual(result['investment_breakdown']['Stable Investments'], 1000.0)

    def test_negative_amounts_use_absolute_value(self):
        """Test that negative amounts (income) are handled correctly"""
        transactions = [
            {'amount': -500.00, 'category': 'Savings'},  # Income/deposit
            {'amount': 100.00, 'category': 'Food'}
        ]

        result = calculate_investment_rate(transactions)

        # Should use absolute values
        self.assertEqual(result['investment_total'], 500.0)
        self.assertEqual(result['consumption_total'], 100.0)

    def test_empty_transactions(self):
        """Test with no transactions"""
        result = calculate_investment_rate([])

        self.assertEqual(result['investment_total'], 0.0)
        self.assertEqual(result['consumption_total'], 0.0)
        self.assertEqual(result['total_spending'], 0.0)
        self.assertEqual(result['investment_rate'], 0.0)


class TestGetTopMerchants(unittest.TestCase):
    """Test top merchants extraction"""

    def test_get_top_10_default(self):
        """Test getting top 10 merchants by default"""
        merchants = [{'total': i * 100} for i in range(20, 0, -1)]

        result = get_top_merchants(merchants)

        self.assertEqual(len(result), 10)
        self.assertEqual(result[0]['total'], 2000)  # Highest
        self.assertEqual(result[9]['total'], 1100)  # 10th

    def test_get_top_n_custom_limit(self):
        """Test getting top N with custom limit"""
        merchants = [{'total': i * 100} for i in range(20, 0, -1)]

        result = get_top_merchants(merchants, limit=5)

        self.assertEqual(len(result), 5)

    def test_get_top_fewer_than_limit(self):
        """Test when there are fewer merchants than limit"""
        merchants = [{'total': 100}, {'total': 200}, {'total': 300}]

        result = get_top_merchants(merchants, limit=10)

        self.assertEqual(len(result), 3)


class TestGetMerchantsByRegularity(unittest.TestCase):
    """Test filtering merchants by regularity"""

    def test_filter_monthly_merchants(self):
        """Test filtering for monthly patterns"""
        merchants = [
            {'address': 'A', 'regularity': 'monthly'},
            {'address': 'B', 'regularity': 'weekly'},
            {'address': 'C', 'regularity': 'monthly'},
            {'address': 'D', 'regularity': 'irregular'}
        ]

        result = get_merchants_by_regularity(merchants, 'monthly')

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['address'], 'A')
        self.assertEqual(result[1]['address'], 'C')

    def test_filter_no_matches(self):
        """Test filtering with no matches"""
        merchants = [
            {'address': 'A', 'regularity': 'weekly'},
            {'address': 'B', 'regularity': 'irregular'}
        ]

        result = get_merchants_by_regularity(merchants, 'monthly')

        self.assertEqual(len(result), 0)

    def test_filter_all_match(self):
        """Test filtering when all match"""
        merchants = [
            {'address': 'A', 'regularity': 'weekly'},
            {'address': 'B', 'regularity': 'weekly'}
        ]

        result = get_merchants_by_regularity(merchants, 'weekly')

        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()
