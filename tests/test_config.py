"""
Unit tests for config.py
"""

import unittest
import tempfile
import os
from package.config import Config, get_bank_identifier


class TestConfig(unittest.TestCase):
    """Test configuration management"""

    def setUp(self):
        """Create temporary config file"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')

    def test_config_creation(self):
        """Test creating a new config"""
        config = Config()
        self.assertIsNotNone(config.default_categories)
        self.assertEqual(len(config.default_categories), 13)

    def test_save_and_load_column_mapping(self):
        """Test saving and loading column mappings"""
        config = Config(config_file=self.config_file)
        mapping = {'date': 0, 'address': 1, 'amount': 2}

        config.save_column_mapping('test_bank', mapping)
        loaded_mapping = config.get_column_mapping('test_bank')

        self.assertEqual(loaded_mapping, mapping)

    def test_get_bank_identifier(self):
        """Test bank identifier generation"""
        headers = ['Date', 'Amount', 'Description']
        bank_id = get_bank_identifier(headers)

        self.assertIsInstance(bank_id, str)
        self.assertEqual(len(bank_id), 16)

        # Same headers should produce same ID
        bank_id2 = get_bank_identifier(headers)
        self.assertEqual(bank_id, bank_id2)


if __name__ == '__main__':
    unittest.main()
