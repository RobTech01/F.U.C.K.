"""
Pattern analysis for transaction data.

This module provides functions to analyze spending patterns, detect recurring
merchants, and calculate investment vs. consumption habits.
"""

from datetime import datetime
from typing import List, Dict, Tuple
from .crypto import decrypt_address


def parse_date(date_str: str) -> datetime:
    """
    Parse a date string into a datetime object.

    Supports multiple common date formats:
    - YYYY-MM-DD (ISO format)
    - DD.MM.YYYY (European format)
    - MM/DD/YYYY (US format)

    Args:
        date_str: Date string to parse

    Returns:
        datetime object

    Raises:
        ValueError: If date format is not recognized
    """
    # Try ISO format first (YYYY-MM-DD)
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        pass

    # Try European format (DD.MM.YYYY)
    try:
        return datetime.strptime(date_str, '%d.%m.%Y')
    except ValueError:
        pass

    # Try US format (MM/DD/YYYY)
    try:
        return datetime.strptime(date_str, '%m/%d/%Y')
    except ValueError:
        pass

    # If none work, raise error
    raise ValueError(f"Unrecognized date format: {date_str}")


def calculate_date_interval(date1_str: str, date2_str: str) -> int:
    """
    Calculate the number of days between two dates.

    Args:
        date1_str: First date string
        date2_str: Second date string

    Returns:
        Number of days between dates (absolute value)
    """
    date1 = parse_date(date1_str)
    date2 = parse_date(date2_str)

    return abs((date2 - date1).days)


def categorize_regularity(avg_interval: float) -> str:
    """
    Categorize transaction regularity based on average interval.

    Args:
        avg_interval: Average number of days between transactions

    Returns:
        Regularity category: 'weekly', 'monthly', 'yearly', or 'irregular'
    """
    if 5 <= avg_interval <= 10:
        return 'weekly'
    elif 20 <= avg_interval <= 40:
        return 'monthly'
    elif 330 <= avg_interval <= 400:
        return 'yearly'
    else:
        return 'irregular'


def analyze_merchants(transactions: List[Dict], cipher_suite) -> List[Dict]:
    """
    Analyze merchants to find spending patterns and regularity.

    Groups transactions by merchant (address_hash), calculates frequency,
    total spending, and regularity pattern.

    Args:
        transactions: List of transaction dicts with keys:
                     {date, address_hash, amount, category}
        cipher_suite: Cipher suite for decrypting address hashes

    Returns:
        List of merchant analysis dicts, sorted by total spending (descending):
        {
            'address': str,        # Decrypted merchant name
            'count': int,          # Number of transactions
            'total': float,        # Total amount spent
            'avg_amount': float,   # Average amount per transaction
            'regularity': str,     # 'weekly', 'monthly', 'yearly', 'irregular', or 'single'
            'category': str        # Most common category
        }
    """
    if not transactions:
        return []

    # Group transactions by address_hash
    grouped = {}
    for txn in transactions:
        address_hash = txn['address_hash']
        if address_hash not in grouped:
            grouped[address_hash] = []
        grouped[address_hash].append(txn)

    # Analyze each merchant
    merchants = []
    for address_hash, txns in grouped.items():
        count = len(txns)
        total = sum(t['amount'] for t in txns)

        # Get most common category for this merchant
        categories = [t['category'] for t in txns]
        category = max(set(categories), key=categories.count)

        # Calculate regularity if 2+ transactions
        regularity = 'single'
        if count >= 2:
            # Sort by date
            sorted_txns = sorted(txns, key=lambda t: parse_date(t['date']))

            # Calculate intervals between consecutive transactions
            intervals = []
            for i in range(1, len(sorted_txns)):
                days = calculate_date_interval(
                    sorted_txns[i-1]['date'],
                    sorted_txns[i]['date']
                )
                intervals.append(days)

            # Calculate average interval
            avg_interval = sum(intervals) / len(intervals)

            # Categorize regularity
            regularity = categorize_regularity(avg_interval)

        # Decrypt address
        decrypted_address = decrypt_address(address_hash, cipher_suite)

        merchants.append({
            'address': decrypted_address,
            'count': count,
            'total': total,
            'avg_amount': total / count,
            'regularity': regularity,
            'category': category
        })

    # Sort by total spending (descending)
    return sorted(merchants, key=lambda m: m['total'], reverse=True)


def calculate_investment_rate(transactions: List[Dict]) -> Dict:
    """
    Calculate investment vs. consumption spending rate.

    Investment categories:
    - Savings
    - Stable Investments
    - High-Risk Investments
    - Arbitrage/Resale Profits
    - Retirement

    Args:
        transactions: List of transaction dicts

    Returns:
        Dict with investment analysis:
        {
            'investment_total': float,
            'consumption_total': float,
            'total_spending': float,
            'investment_rate': float,  # Percentage (0-100)
            'investment_breakdown': Dict[str, float]  # Amount per investment category
        }
    """
    investment_categories = {
        'Savings',
        'Stable Investments',
        'High-Risk Investments',
        'Arbitrage/Resale Profits',
        'Retirement'
    }

    investment_total = 0.0
    consumption_total = 0.0
    investment_breakdown = {}

    for txn in transactions:
        amount = abs(txn['amount'])  # Use absolute value
        category = txn['category']

        if category in investment_categories:
            investment_total += amount
            investment_breakdown[category] = investment_breakdown.get(category, 0.0) + amount
        else:
            consumption_total += amount

    total_spending = investment_total + consumption_total
    investment_rate = (investment_total / total_spending * 100) if total_spending > 0 else 0.0

    return {
        'investment_total': investment_total,
        'consumption_total': consumption_total,
        'total_spending': total_spending,
        'investment_rate': investment_rate,
        'investment_breakdown': investment_breakdown
    }


def get_top_merchants(merchants: List[Dict], limit: int = 10) -> List[Dict]:
    """
    Get top N merchants by total spending.

    Args:
        merchants: List of merchant analysis dicts from analyze_merchants()
        limit: Maximum number of merchants to return (default: 10)

    Returns:
        Top N merchants, already sorted by total spending
    """
    return merchants[:limit]


def get_merchants_by_regularity(merchants: List[Dict], regularity: str) -> List[Dict]:
    """
    Filter merchants by regularity type.

    Args:
        merchants: List of merchant analysis dicts
        regularity: Regularity type ('weekly', 'monthly', 'yearly', 'irregular', 'single')

    Returns:
        Filtered list of merchants with specified regularity
    """
    return [m for m in merchants if m['regularity'] == regularity]
