"""
Core business logic for F.U.C.K.
Pure functions without UI dependencies.
"""

from typing import Dict, Tuple, Optional, List
import csv
from pathlib import Path


class ValidationError(Exception):
    """
    Custom exception for transaction validation errors with detailed information.

    Attributes:
        message: Human-readable error message
        line_number: Line number in CSV file (1-indexed)
        error_type: Type of validation error (e.g., 'invalid_amount', 'missing_field')
        field: Field that caused the error (optional)
        value: Value that caused the error (optional)
    """

    def __init__(self, message: str, line_number: int = None, error_type: str = 'unknown',
                 field: str = None, value: str = None):
        self.message = message
        self.line_number = line_number
        self.error_type = error_type
        self.field = field
        self.value = value
        super().__init__(self.message)

    def __str__(self):
        if self.line_number:
            return f"Line {self.line_number}: {self.message}"
        return self.message


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


def sanitize_filepath(filepath: str, allowed_extensions: List[str] = None) -> Tuple[str, bool, str]:
    """
    Sanitize and validate a file path to prevent directory traversal attacks.

    Args:
        filepath: File path to sanitize
        allowed_extensions: List of allowed file extensions (e.g., ['.csv', '.txt'])

    Returns:
        Tuple of (sanitized_path, is_valid, error_message)
    """
    if allowed_extensions is None:
        allowed_extensions = ['.csv']

    try:
        # Convert to Path object and resolve to absolute path
        path = Path(filepath).resolve()

        # Check for path traversal attempts
        try:
            # Get current working directory
            cwd = Path.cwd().resolve()
            # Check if path is under current directory or is absolute
            # This prevents ../../../etc/passwd type attacks
            if not str(path).startswith(str(cwd)) and not path.is_absolute():
                return "", False, "Path traversal detected"
        except (ValueError, OSError):
            return "", False, "Invalid path"

        # Check file extension
        if path.suffix.lower() not in allowed_extensions:
            return "", False, f"Invalid file extension: {path.suffix}. Allowed: {allowed_extensions}"

        # Check for null bytes
        if '\x00' in str(filepath):
            return "", False, "Null byte in path"

        # Check path length (prevent DOS via extremely long paths)
        if len(str(path)) > 4096:
            return "", False, "Path too long"

        return str(path), True, ""

    except Exception as e:
        return "", False, f"Path validation error: {e}"


def validate_csv_file(filepath: str) -> Tuple[bool, str]:
    """
    Validate that a CSV file exists, is readable, and is safe.

    Args:
        filepath: Path to CSV file

    Returns:
        Tuple of (is_valid, error_message)
    """
    # First sanitize the path
    sanitized_path, is_safe, error_msg = sanitize_filepath(filepath, ['.csv'])
    if not is_safe:
        return False, f"Unsafe file path: {error_msg}"

    path = Path(sanitized_path)

    if not path.exists():
        return False, f"File does not exist: {filepath}"

    if not path.is_file():
        return False, f"Path is not a file: {filepath}"

    if not path.suffix.lower() == '.csv':
        return False, f"File is not a CSV: {filepath}"

    # Check file size (prevent DOS via huge files)
    try:
        file_size = path.stat().st_size
        if file_size > 100 * 1024 * 1024:  # 100 MB limit
            return False, f"File too large: {file_size / 1024 / 1024:.1f} MB (max 100 MB)"
    except Exception as e:
        return False, f"Cannot stat file: {e}"

    # Check if file is readable
    try:
        with open(sanitized_path, 'r', encoding='utf-8') as f:
            # Try to read first line
            f.readline()
        return True, ""
    except PermissionError:
        return False, f"Permission denied: {filepath}"
    except Exception as e:
        return False, f"Cannot read file: {str(e)}"


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string value to prevent injection attacks.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)

    # Remove null bytes
    sanitized = value.replace('\x00', '')

    # Remove control characters except newline and tab
    sanitized = ''.join(char for char in sanitized if char.isprintable() or char in '\n\t')

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    # Strip leading/trailing whitespace
    return sanitized.strip()


def sanitize_transaction(transaction: Dict) -> Dict:
    """
    Sanitize transaction data to prevent injection attacks.

    Args:
        transaction: Transaction dictionary

    Returns:
        Sanitized transaction dictionary
    """
    sanitized = {}

    # Sanitize all string fields
    for key, value in transaction.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, (int, float)):
            sanitized[key] = value
        else:
            sanitized[key] = sanitize_string(str(value))

    return sanitized


def validate_transaction(transaction: Dict) -> Tuple[bool, str]:
    """
    Validate that a transaction has required fields and safe values.

    Args:
        transaction: Transaction dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['date', 'address', 'amount']

    for field in required_fields:
        if field not in transaction:
            return False, f"Missing required field: {field}"

    # Validate amount is numeric and reasonable
    try:
        amount = float(transaction['amount'])
        # Check for suspicious values
        if abs(amount) > 1_000_000_000:  # 1 billion limit
            return False, f"Amount too large: {amount}"
    except (ValueError, TypeError):
        return False, f"Invalid amount: {transaction.get('amount')}"

    # Validate date is not empty and reasonable length
    date_str = str(transaction['date']).strip()
    if not date_str:
        return False, "Date cannot be empty"
    if len(date_str) > 50:
        return False, f"Date too long: {len(date_str)} characters"

    # Validate address is not empty and reasonable length
    address_str = str(transaction['address']).strip()
    if not address_str:
        return False, "Address cannot be empty"
    if len(address_str) > 500:
        return False, f"Address too long: {len(address_str)} characters"

    # Check for suspicious patterns (basic SQL/script injection detection)
    suspicious_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=', 'DROP TABLE', 'INSERT INTO', 'DELETE FROM']
    for field in ['date', 'address', 'name', 'type', 'description']:
        if field in transaction:
            value_lower = str(transaction[field]).lower()
            for pattern in suspicious_patterns:
                if pattern.lower() in value_lower:
                    return False, f"Suspicious content detected in {field}: {pattern}"

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
