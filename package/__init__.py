"""
Fund Utilization and Categorization Kit (F.U.C.K.)
A personal finance tracker for processing and categorizing bank transactions.
"""

__version__ = "0.2.0"
__author__ = "RobTech01"

# Core functionality exports
from .crypto import initialize_crypto, hash_address, encrypt_address, decrypt_address
from .storage import load_hash_table, save_hash_table, initialize_hash_table
from .category_manager import categorize_transaction
from .read_data import process_csv_file
from .config import Config
from . import cli

__all__ = [
    # Crypto utilities
    'initialize_crypto',
    'hash_address',
    'encrypt_address',
    'decrypt_address',
    # Storage
    'load_hash_table',
    'save_hash_table',
    'initialize_hash_table',
    # Category management
    'categorize_transaction',
    # Data processing
    'process_csv_file',
    # Configuration
    'Config',
    # CLI module (imported as whole module)
    'cli',
]
