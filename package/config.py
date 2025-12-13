"""
Configuration management for F.U.C.K.
Handles crypto configuration, file paths, and user settings.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Config:
    """Main configuration class for F.U.C.K."""

    # Crypto settings (runtime only, not saved)
    cipher_suite: Optional[object] = None
    salt: Optional[bytes] = None

    # File paths
    storage_dir: str = "./storage"
    hash_table_file: str = "./storage/hash_table.enc"
    config_file: str = "./config.json"

    # CSV column mappings (saved per bank)
    column_mappings: Dict[str, Dict[str, int]] = None

    # Default categories
    default_categories: list = None

    def __post_init__(self):
        """Initialize default values if not provided."""
        if self.column_mappings is None:
            self.column_mappings = {}

        if self.default_categories is None:
            self.default_categories = [
                'Groceries/Food',
                'Utilities/Bills',
                'Rent/Mortgage',
                'Salary',
                'Savings',
                'Stable Investments',
                'High-Risk Investments',
                'Arbitrage/Resale Profits',
                'Retirement',
                'Entertainment/Leisure',
                'Health & Wellness',
                'Education',
                'Miscellaneous/Other'
            ]

    def save(self, filepath: Optional[str] = None) -> None:
        """
        Save configuration to JSON file (excludes crypto objects).

        Args:
            filepath: Path to save config (default: self.config_file)
        """
        filepath = filepath or self.config_file

        # Create config dict excluding crypto objects
        config_data = {
            'storage_dir': self.storage_dir,
            'hash_table_file': self.hash_table_file,
            'config_file': self.config_file,
            'column_mappings': self.column_mappings,
            'default_categories': self.default_categories
        }

        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)

    @classmethod
    def load(cls, filepath: str = "./config.json") -> 'Config':
        """
        Load configuration from JSON file.

        Args:
            filepath: Path to config file

        Returns:
            Config object
        """
        if not os.path.exists(filepath):
            return cls()  # Return default config

        with open(filepath, 'r') as f:
            config_data = json.load(f)

        return cls(**config_data)

    def get_column_mapping(self, bank_identifier: str) -> Optional[Dict[str, int]]:
        """
        Get saved column mapping for a specific bank.

        Args:
            bank_identifier: Unique identifier for the bank (e.g., CSV structure hash)

        Returns:
            Dictionary mapping column names to indices, or None if not found
        """
        return self.column_mappings.get(bank_identifier)

    def save_column_mapping(self, bank_identifier: str, mapping: Dict[str, int]) -> None:
        """
        Save column mapping for a specific bank.

        Args:
            bank_identifier: Unique identifier for the bank
            mapping: Dictionary mapping column names to indices
        """
        self.column_mappings[bank_identifier] = mapping
        self.save()


def get_bank_identifier(csv_headers: list) -> str:
    """
    Generate a unique identifier for a CSV format based on its headers.

    Args:
        csv_headers: List of CSV column headers

    Returns:
        String identifier (simple hash of headers)
    """
    import hashlib
    headers_str = "|".join(csv_headers)
    return hashlib.md5(headers_str.encode()).hexdigest()[:16]
