"""
Core business logic for F.U.C.K.
Pure functions without UI dependencies.
"""

from typing import Dict, Tuple, Optional, List
import csv
from pathlib import Path


def generate_transaction_id(date: str, amount: float, hashed_address: str = "") -> str:
    """
    Generates a unique ID for a transaction using its date, amount, and address hash.

    Args:
        date: Transaction date
        amount: Transaction amount
        hashed_address: Hashed address for uniqueness (optional, first 8 chars used)

    Returns:
        String representing the transaction ID
    """
    address_prefix = hashed_address[:8] if hashed_address else ""
    return f"{date}-{address_prefix}-{amount}"


def is_duplicate_transaction(transaction_id_hash: str, hash_table: Dict) -> bool:
    """
    Check if a transaction ID already exists in the hash table.

    Args:
        transaction_id_hash: Hashed transaction ID
        hash_table: The hash table containing transaction IDs

    Returns:
        True if duplicate, False otherwise
    """
    return transaction_id_hash in hash_table.get('transaction_ids', [])


def find_category_by_address(encrypted_addresses: Dict, target_hash: str, cipher_suite) -> Optional[str]:
    """
    Find the category for a given address hash by decrypting stored addresses.

    Args:
        encrypted_addresses: Dict of encrypted hashes to categories
        target_hash: The hashed address to find
        cipher_suite: Encryption cipher suite

    Returns:
        Category string if found, None otherwise
    """
    from .crypto import decrypt_address

    for encrypted_key, category in encrypted_addresses.items():
        try:
            decrypted_key = decrypt_address(encrypted_key, cipher_suite)
            if decrypted_key == target_hash:
                return category
        except Exception:
            # Skip invalid/corrupted entries
            continue
    return None


def validate_csv_file(filepath: str) -> Tuple[bool, str]:
    """
    Validate that a CSV file exists and is readable.

    Args:
        filepath: Path to CSV file

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(filepath)

    if not path.exists():
        return False, f"File does not exist: {filepath}"

    if not path.is_file():
        return False, f"Path is not a file: {filepath}"

    if not path.suffix.lower() == '.csv':
        return False, f"File is not a CSV: {filepath}"

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Try to read first line
            f.readline()
        return True, ""
    except PermissionError:
        return False, f"Permission denied: {filepath}"
    except Exception as e:
        return False, f"Cannot read file: {str(e)}"


def validate_transaction(transaction: Dict) -> Tuple[bool, str]:
    """
    Validate that a transaction has required fields.

    Args:
        transaction: Transaction dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['date', 'address', 'amount']

    for field in required_fields:
        if field not in transaction:
            return False, f"Missing required field: {field}"

    # Validate amount is numeric
    try:
        float(transaction['amount'])
    except (ValueError, TypeError):
        return False, f"Invalid amount: {transaction.get('amount')}"

    # Validate date is not empty
    if not transaction['date'].strip():
        return False, "Date cannot be empty"

    # Validate address is not empty
    if not transaction['address'].strip():
        return False, "Address cannot be empty"

    return True, ""


def add_transaction_to_hash_table(
    transaction: Dict,
    hash_table: Dict,
    hashed_address: str,
    encrypted_hashed_address: str,
    transaction_id_hash: str,
    category: str
) -> None:
    """
    Add a transaction to the hash table (pure business logic, no UI).

    Args:
        transaction: Transaction dictionary
        hash_table: Hash table to update
        hashed_address: Hashed address
        encrypted_hashed_address: Encrypted hashed address
        transaction_id_hash: Hashed transaction ID
        category: Category to assign
    """
    # Add transaction ID
    if 'transaction_ids' not in hash_table:
        hash_table['transaction_ids'] = []
    hash_table['transaction_ids'].append(transaction_id_hash)

    # Add/update address mapping
    if 'addresses' not in hash_table:
        hash_table['addresses'] = {}
    if encrypted_hashed_address not in hash_table['addresses']:
        hash_table['addresses'][encrypted_hashed_address] = category

    # Update category total
    if 'categories' not in hash_table:
        hash_table['categories'] = {}
    hash_table['categories'].setdefault(category, 0)
    hash_table['categories'][category] += transaction['amount']


def get_category_totals(hash_table: Dict) -> Dict[str, float]:
    """
    Get all category totals from hash table.

    Args:
        hash_table: The hash table

    Returns:
        Dictionary of category -> total amount
    """
    return hash_table.get('categories', {}).copy()


def get_transaction_count(hash_table: Dict) -> int:
    """
    Get total number of transactions in hash table.

    Args:
        hash_table: The hash table

    Returns:
        Number of transactions
    """
    return len(hash_table.get('transaction_ids', []))


def parse_csv_row(row: List[str], column_mapping: Dict[str, int]) -> Dict:
    """
    Parse a CSV row into a transaction dictionary using column mapping.

    Args:
        row: CSV row data
        column_mapping: Mapping of field names to column indices

    Returns:
        Transaction dictionary
    """
    transaction = {}

    # Required fields
    transaction['date'] = row[column_mapping['date']].strip()
    transaction['address'] = row[column_mapping['address']].strip()
    transaction['amount'] = float(row[column_mapping['amount']].strip())

    # Optional fields
    for field in ['name', 'type', 'description']:
        if field in column_mapping and column_mapping[field] >= 0:
            transaction[field] = row[column_mapping[field]].strip()
        else:
            transaction[field] = ""

    return transaction
