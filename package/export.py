"""
Export module for F.U.C.K.
Provides functionality to export category data in multiple formats.
"""

import json
import csv
from typing import Dict, List, Optional
from datetime import datetime


def export_to_csv(categories: Dict[str, float], output_file: str) -> None:
    """
    Export category totals to CSV format.

    Args:
        categories: Dictionary mapping category names to totals
        output_file: Path to output CSV file

    Format:
        category,amount
        Groceries/Food,450.75
        Utilities/Bills,250.00
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['category', 'amount'])

        # Sort by category name for consistent output
        for category in sorted(categories.keys()):
            writer.writerow([category, f"{categories[category]:.2f}"])


def export_to_json(categories: Dict[str, float], output_file: str, pretty: bool = True) -> None:
    """
    Export category totals to JSON format.

    Args:
        categories: Dictionary mapping category names to totals
        output_file: Path to output JSON file
        pretty: Whether to use pretty-printing (indented)

    Format:
        {
          "export_date": "2025-12-13",
          "total_categories": 3,
          "grand_total": 776.00,
          "categories": [
            {"category": "Groceries/Food", "amount": 450.75},
            ...
          ]
        }
    """
    # Calculate totals
    grand_total = sum(categories.values())

    # Build structured data
    export_data = {
        "export_date": datetime.now().strftime("%Y-%m-%d"),
        "total_categories": len(categories),
        "grand_total": round(grand_total, 2),
        "categories": [
            {
                "category": category,
                "amount": round(amount, 2)
            }
            for category, amount in sorted(categories.items())
        ]
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(export_data, f, ensure_ascii=False)


def export_to_txt(categories: Dict[str, float], output_file: str) -> None:
    """
    Export category totals to human-readable text format.

    Args:
        categories: Dictionary mapping category names to totals
        output_file: Path to output text file

    Format:
        ================================================================================
        F.U.C.K. SPENDING REPORT
        ================================================================================
        Export Date: 2025-12-13
        Total Categories: 3
        Grand Total: $776.00
        --------------------------------------------------------------------------------

        Category                                           Amount
        --------------------------------------------------------------------------------
        Groceries/Food                                   $450.75
        ...
    """
    grand_total = sum(categories.values())
    export_date = datetime.now().strftime("%Y-%m-%d")

    lines = []
    lines.append("=" * 80)
    lines.append("F.U.C.K. SPENDING REPORT")
    lines.append("=" * 80)
    lines.append(f"Export Date: {export_date}")
    lines.append(f"Total Categories: {len(categories)}")
    lines.append(f"Grand Total: ${grand_total:.2f}")
    lines.append("-" * 80)
    lines.append("")
    lines.append(f"{'Category':<50} {'Amount':>12}")
    lines.append("-" * 80)

    for category in sorted(categories.keys()):
        amount = categories[category]
        lines.append(f"{category:<50} ${amount:>11.2f}")

    lines.append("=" * 80)
    lines.append("")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def get_export_filename(format_type: str, output_file: Optional[str] = None) -> str:
    """
    Generate a default export filename if none provided.

    Args:
        format_type: Export format (csv, json, txt)
        output_file: User-provided filename (optional)

    Returns:
        Filename to use for export
    """
    if output_file:
        return output_file

    # Generate default filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"fuck_export_{timestamp}.{format_type}"


def validate_format(format_type: str) -> bool:
    """
    Validate that the export format is supported.

    Args:
        format_type: Format to validate

    Returns:
        True if valid, False otherwise
    """
    return format_type.lower() in ['csv', 'json', 'txt']


def export_categories(
    categories: Dict[str, float],
    format_type: str = 'csv',
    output_file: Optional[str] = None
) -> str:
    """
    Export categories to specified format.

    Args:
        categories: Dictionary mapping category names to totals
        format_type: Export format (csv, json, txt)
        output_file: Optional output filename

    Returns:
        Path to exported file

    Raises:
        ValueError: If format is invalid or categories is empty
    """
    if not categories:
        raise ValueError("No data to export. Categories dictionary is empty.")

    format_lower = format_type.lower()

    if not validate_format(format_lower):
        raise ValueError(f"Invalid export format: {format_type}. Must be csv, json, or txt.")

    # Get filename
    filename = get_export_filename(format_lower, output_file)

    # Export based on format
    if format_lower == 'csv':
        export_to_csv(categories, filename)
    elif format_lower == 'json':
        export_to_json(categories, filename)
    elif format_lower == 'txt':
        export_to_txt(categories, filename)

    return filename
