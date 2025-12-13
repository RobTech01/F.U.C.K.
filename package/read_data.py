import csv
import argparse
from .category_manager import categorize_transaction
from .crypto import initialize_crypto
from .storage import load_hash_table, save_hash_table, print_hash_table
from . import cli
from .core import validate_csv_file, validate_transaction, parse_csv_row, sanitize_transaction
from typing import Tuple, List, Dict


def process_csv_file(filepath: str, hash_table: dict, cipher_suite, SALT) -> Dict[str, int]:
    """
    Process a CSV file and categorize all transactions.

    Args:
        filepath: Path to CSV file
        hash_table: Hash table to update
        cipher_suite: Encryption cipher
        SALT: Salt for hashing

    Returns:
        Dict with statistics: {'total': int, 'processed': int, 'skipped': int, 'errors': int}

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV file is invalid or malformed
    """
    # Validate CSV file first
    is_valid, error_msg = validate_csv_file(filepath)
    if not is_valid:
        raise ValueError(f"Invalid CSV file: {error_msg}")

    stats = {'total': 0, 'processed': 0, 'skipped': 0, 'errors': 0}

    try:
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')

            # Read header
            try:
                header = next(reader)
            except StopIteration:
                raise ValueError("CSV file is empty")

            if not header or len(header) < 3:
                raise ValueError(f"CSV header invalid: needs at least 3 columns, got {len(header)}")

            # Get column mapping from user
            date_col, address_col, amount_col, name_col, type_col, description_col = cli.select_csv_columns(header)

            # Validate column selections
            max_col = len(header) - 1
            if not (0 <= date_col <= max_col and 0 <= address_col <= max_col and 0 <= amount_col <= max_col):
                raise ValueError("Invalid column selection: columns out of range")

            # Process each row
            row_num = 1  # Header is row 0
            for row in reader:
                row_num += 1
                stats['total'] += 1

                # Validate row length
                if len(row) < len(header):
                    print(f"Warning: Row {row_num} has fewer columns than header, skipping")
                    stats['skipped'] += 1
                    continue

                try:
                    # Extract transaction data
                    date = row[date_col].strip()
                    address = row[address_col].strip()
                    amount_str = row[amount_col].strip()

                    # Validate and parse amount
                    try:
                        amount = float(amount_str.replace(',', '.'))
                    except ValueError:
                        print(f"Warning: Row {row_num} has invalid amount '{amount_str}', skipping")
                        stats['skipped'] += 1
                        continue

                    # Extract optional fields
                    name = row[name_col].strip() if name_col >= 0 and name_col < len(row) else ""
                    trans_type = row[type_col].strip() if type_col >= 0 and type_col < len(row) else ""
                    description = row[description_col].strip() if description_col >= 0 and description_col < len(row) else ""

                    # Build transaction
                    transaction = {
                        'date': date,
                        'address': address,
                        'amount': amount,
                        'name': name,
                        'type': trans_type,
                        'description': description
                    }

                    # Sanitize transaction data
                    transaction = sanitize_transaction(transaction)

                    # Validate transaction
                    is_valid, error_msg = validate_transaction(transaction)
                    if not is_valid:
                        print(f"Warning: Row {row_num} invalid: {error_msg}, skipping")
                        stats['skipped'] += 1
                        continue

                    # Categorize transaction
                    categorize_transaction(transaction, hash_table, cipher_suite, SALT)
                    stats['processed'] += 1

                except IndexError as e:
                    print(f"Warning: Row {row_num} has column access error: {e}, skipping")
                    stats['skipped'] += 1
                except Exception as e:
                    print(f"Error processing row {row_num}: {e}")
                    stats['errors'] += 1
                    if stats['errors'] > 10:
                        print("Too many errors, stopping CSV processing")
                        break

            # Print summary
            cli.print_summary(stats['total'], stats['processed'], stats['skipped'])

            return stats

    except UnicodeDecodeError:
        raise ValueError("CSV file encoding error: file must be UTF-8 encoded")
    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a new data file and categorize transactions.")
    parser.add_argument("csv_file_path", type=str, default = '../dummy-data/january.csv')

    args = parser.parse_args()

    cipher_suite, SALT = initialize_crypto()
    hash_table = load_hash_table(cipher_suite)
    print("Table loaded successfully.")

    process_csv_file(args.csv_file_path, hash_table, cipher_suite, SALT)
    print("CSV file processed successfully.")

    save_hash_table(hash_table, cipher_suite)
    print("File saved successfully.")


