"""
Unit tests for export module (Session 4)
"""

import unittest
import json
import csv
import os
import tempfile
from package.export import (
    export_to_csv,
    export_to_json,
    export_to_txt,
    get_export_filename,
    validate_format,
    export_categories
)


class TestExportToCSV(unittest.TestCase):
    """Test CSV export functionality"""

    def setUp(self):
        """Set up test data"""
        self.test_categories = {
            'Groceries/Food': 450.75,
            'Utilities/Bills': 250.00,
            'Entertainment': 75.25
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.temp_file.close()

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_export_to_csv_creates_file(self):
        """Test that CSV export creates a file"""
        export_to_csv(self.test_categories, self.temp_file.name)
        self.assertTrue(os.path.exists(self.temp_file.name))

    def test_export_to_csv_format(self):
        """Test that CSV has correct format"""
        export_to_csv(self.test_categories, self.temp_file.name)

        with open(self.temp_file.name, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        self.assertEqual(rows[0], ['category', 'amount'])

        # Check data rows (should be sorted)
        self.assertEqual(len(rows), 4)  # Header + 3 categories
        self.assertEqual(rows[1][0], 'Entertainment')
        self.assertEqual(rows[2][0], 'Groceries/Food')
        self.assertEqual(rows[3][0], 'Utilities/Bills')

    def test_export_to_csv_amounts(self):
        """Test that amounts are formatted correctly"""
        export_to_csv(self.test_categories, self.temp_file.name)

        with open(self.temp_file.name, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

        # Check amounts are formatted to 2 decimal places
        for row in rows:
            amount = float(row[1])
            self.assertEqual(row[1], f"{amount:.2f}")


class TestExportToJSON(unittest.TestCase):
    """Test JSON export functionality"""

    def setUp(self):
        """Set up test data"""
        self.test_categories = {
            'Groceries/Food': 450.75,
            'Utilities/Bills': 250.00,
            'Entertainment': 75.25
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_export_to_json_creates_file(self):
        """Test that JSON export creates a file"""
        export_to_json(self.test_categories, self.temp_file.name)
        self.assertTrue(os.path.exists(self.temp_file.name))

    def test_export_to_json_valid(self):
        """Test that exported JSON is valid"""
        export_to_json(self.test_categories, self.temp_file.name)

        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)

    def test_export_to_json_structure(self):
        """Test that JSON has correct structure"""
        export_to_json(self.test_categories, self.temp_file.name)

        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)

        # Check required fields
        self.assertIn('export_date', data)
        self.assertIn('total_categories', data)
        self.assertIn('grand_total', data)
        self.assertIn('categories', data)

        # Check values
        self.assertEqual(data['total_categories'], 3)
        self.assertEqual(data['grand_total'], 776.00)
        self.assertEqual(len(data['categories']), 3)

    def test_export_to_json_category_format(self):
        """Test that categories are formatted correctly"""
        export_to_json(self.test_categories, self.temp_file.name)

        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)

        # Each category should have category and amount fields
        for cat in data['categories']:
            self.assertIn('category', cat)
            self.assertIn('amount', cat)
            self.assertIsInstance(cat['category'], str)
            self.assertIsInstance(cat['amount'], (int, float))

    def test_export_to_json_pretty_print(self):
        """Test that pretty print adds indentation"""
        export_to_json(self.test_categories, self.temp_file.name, pretty=True)

        with open(self.temp_file.name, 'r') as f:
            content = f.read()

        # Pretty printed JSON should have indentation
        self.assertIn('  ', content)

    def test_export_to_json_compact(self):
        """Test that compact format has no extra whitespace"""
        export_to_json(self.test_categories, self.temp_file.name, pretty=False)

        with open(self.temp_file.name, 'r') as f:
            content = f.read()

        # Compact JSON should not have indentation
        lines = content.split('\n')
        self.assertEqual(len(lines), 1)  # All on one line


class TestExportToTXT(unittest.TestCase):
    """Test TXT export functionality"""

    def setUp(self):
        """Set up test data"""
        self.test_categories = {
            'Groceries/Food': 450.75,
            'Utilities/Bills': 250.00,
            'Entertainment': 75.25
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file.close()

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_export_to_txt_creates_file(self):
        """Test that TXT export creates a file"""
        export_to_txt(self.test_categories, self.temp_file.name)
        self.assertTrue(os.path.exists(self.temp_file.name))

    def test_export_to_txt_content(self):
        """Test that TXT has correct content"""
        export_to_txt(self.test_categories, self.temp_file.name)

        with open(self.temp_file.name, 'r') as f:
            content = f.read()

        # Check for required sections
        self.assertIn('F.U.C.K. SPENDING REPORT', content)
        self.assertIn('Export Date:', content)
        self.assertIn('Total Categories: 3', content)
        self.assertIn('Grand Total: $776.00', content)
        self.assertIn('Groceries/Food', content)
        self.assertIn('Utilities/Bills', content)
        self.assertIn('Entertainment', content)


class TestExportHelpers(unittest.TestCase):
    """Test helper functions"""

    def test_get_export_filename_with_output(self):
        """Test filename generation with user-provided output"""
        result = get_export_filename('csv', 'myfile.csv')
        self.assertEqual(result, 'myfile.csv')

    def test_get_export_filename_default(self):
        """Test default filename generation"""
        result = get_export_filename('csv', None)
        self.assertTrue(result.startswith('fuck_export_'))
        self.assertTrue(result.endswith('.csv'))

    def test_get_export_filename_formats(self):
        """Test filename generation for different formats"""
        for format_type in ['csv', 'json', 'txt']:
            result = get_export_filename(format_type, None)
            self.assertTrue(result.endswith(f'.{format_type}'))

    def test_validate_format_valid(self):
        """Test format validation with valid formats"""
        self.assertTrue(validate_format('csv'))
        self.assertTrue(validate_format('json'))
        self.assertTrue(validate_format('txt'))
        self.assertTrue(validate_format('CSV'))  # Case-insensitive
        self.assertTrue(validate_format('JSON'))

    def test_validate_format_invalid(self):
        """Test format validation with invalid formats"""
        self.assertFalse(validate_format('xml'))
        self.assertFalse(validate_format('pdf'))
        self.assertFalse(validate_format(''))


class TestExportCategories(unittest.TestCase):
    """Test main export function"""

    def setUp(self):
        """Set up test data"""
        self.test_categories = {
            'Groceries/Food': 450.75,
            'Utilities/Bills': 250.00
        }

    def test_export_categories_csv(self):
        """Test exporting to CSV"""
        output_file = export_categories(self.test_categories, 'csv', 'test_output.csv')
        self.assertTrue(os.path.exists(output_file))
        os.remove(output_file)

    def test_export_categories_json(self):
        """Test exporting to JSON"""
        output_file = export_categories(self.test_categories, 'json', 'test_output.json')
        self.assertTrue(os.path.exists(output_file))
        os.remove(output_file)

    def test_export_categories_txt(self):
        """Test exporting to TXT"""
        output_file = export_categories(self.test_categories, 'txt', 'test_output.txt')
        self.assertTrue(os.path.exists(output_file))
        os.remove(output_file)

    def test_export_categories_empty(self):
        """Test exporting empty categories raises error"""
        with self.assertRaises(ValueError) as ctx:
            export_categories({}, 'csv')
        self.assertIn('empty', str(ctx.exception).lower())

    def test_export_categories_invalid_format(self):
        """Test invalid format raises error"""
        with self.assertRaises(ValueError) as ctx:
            export_categories(self.test_categories, 'pdf')
        self.assertIn('Invalid export format', str(ctx.exception))

    def test_export_categories_returns_filename(self):
        """Test that export returns the filename"""
        output_file = export_categories(self.test_categories, 'csv', 'test.csv')
        self.assertEqual(output_file, 'test.csv')
        os.remove(output_file)


if __name__ == '__main__':
    unittest.main()
