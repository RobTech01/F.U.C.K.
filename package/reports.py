"""
Reports module for F.U.C.K. - Spending insights and analysis
"""

from typing import Dict, List, Tuple


def generate_category_breakdown(categories: Dict[str, float]) -> Dict:
    """
    Generate a category breakdown report with percentages and rankings.

    Args:
        categories: Dictionary of categories and their totals

    Returns:
        Dict with report data: total, categories sorted, percentages
    """
    if not categories:
        return {
            'total': 0.0,
            'categories': [],
            'has_data': False
        }

    total = sum(categories.values())

    # Sort categories by amount (descending)
    sorted_categories = sorted(
        categories.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    # Calculate percentages
    category_data = []
    for category, amount in sorted_categories:
        percentage = (abs(amount) / total * 100) if total != 0 else 0
        category_data.append({
            'category': category,
            'amount': amount,
            'percentage': percentage
        })

    return {
        'total': total,
        'categories': category_data,
        'has_data': True,
        'count': len(category_data)
    }


def generate_ascii_bar(value: float, max_value: float, bar_width: int = 40) -> str:
    """
    Generate an ASCII bar chart for a value.

    Args:
        value: The value to represent
        max_value: Maximum value for scaling
        bar_width: Width of the bar in characters

    Returns:
        String representation of bar
    """
    if max_value == 0:
        return ""

    # Calculate bar length
    proportion = abs(value) / max_value
    bar_length = int(proportion * bar_width)

    # Create bar with █ character
    bar = "█" * bar_length

    return bar


def format_category_report(report_data: Dict, show_bars: bool = True) -> str:
    """
    Format category breakdown report for display.

    Args:
        report_data: Report data from generate_category_breakdown
        show_bars: Whether to show ASCII bar charts

    Returns:
        Formatted report string
    """
    if not report_data['has_data']:
        return "\nNo data available for report.\n"

    lines = []
    lines.append("\n" + "="*80)
    lines.append("SPENDING BREAKDOWN BY CATEGORY")
    lines.append("="*80)
    lines.append(f"Total: ${report_data['total']:.2f}")
    lines.append(f"Categories: {report_data['count']}")
    lines.append("-" * 80)
    lines.append("")

    # Find max amount for bar scaling
    max_amount = max(abs(cat['amount']) for cat in report_data['categories'])

    # Display each category
    for idx, cat_data in enumerate(report_data['categories'], 1):
        category = cat_data['category']
        amount = cat_data['amount']
        percentage = cat_data['percentage']

        # Format category line
        cat_display = f"{idx}. {category[:35]:<35}"
        amount_display = f"${amount:>10.2f}"
        pct_display = f"{percentage:>5.1f}%"

        lines.append(f"{cat_display} {amount_display}  ({pct_display})")

        # Add ASCII bar if requested
        if show_bars:
            bar = generate_ascii_bar(amount, max_amount, bar_width=40)
            if bar:
                lines.append(f"   {bar}")
            lines.append("")

    lines.append("="*80)

    return "\n".join(lines)


def get_top_categories(categories: Dict[str, float], limit: int = 5) -> List[Tuple[str, float]]:
    """
    Get top N categories by spending.

    Args:
        categories: Dictionary of categories and totals
        limit: Number of top categories to return

    Returns:
        List of (category, amount) tuples
    """
    sorted_categories = sorted(
        categories.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    return sorted_categories[:limit]


def calculate_category_statistics(categories: Dict[str, float]) -> Dict:
    """
    Calculate statistics for categories.

    Args:
        categories: Dictionary of categories and totals

    Returns:
        Dict with mean, median, highest, lowest
    """
    if not categories:
        return {
            'mean': 0.0,
            'median': 0.0,
            'highest': None,
            'lowest': None
        }

    amounts = [abs(amount) for amount in categories.values()]
    amounts_sorted = sorted(amounts)

    # Calculate mean
    mean = sum(amounts) / len(amounts)

    # Calculate median
    n = len(amounts_sorted)
    if n % 2 == 0:
        median = (amounts_sorted[n//2 - 1] + amounts_sorted[n//2]) / 2
    else:
        median = amounts_sorted[n//2]

    # Find highest and lowest
    sorted_cats = sorted(
        categories.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    return {
        'mean': mean,
        'median': median,
        'highest': sorted_cats[0] if sorted_cats else None,
        'lowest': sorted_cats[-1] if sorted_cats else None
    }
