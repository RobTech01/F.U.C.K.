import csv
import argparse
import copy
from .category_manager import categorize_transaction
from .crypto import initialize_crypto
from .storage import load_hash_table, save_hash_table, print_hash_table
from . import cli
from .core import validate_csv_file, validate_transaction, parse_csv_row, sanitize_transaction
from .config import Config, get_bank_identifier
from typing import Tuple, List, Dict


def process_csv_file(filepath: str, hash_table: dict, cipher_suite, SALT, review: bool = True, strict: bool = False) -> Dict[str, int]:
    """
    Process a CSV file and categorize all transactions.

    Args:
        filepath: Path to CSV file
        hash_table: Hash table to update
        cipher_suite: Encryption cipher
        SALT: Salt for hashing
        review: Whether to show review screen before saving (default: True)
        strict: Whether to fail on first validation error (default: False)

    Returns:
        Dict with statistics: {'total': int, 'processed': int, 'skipped': int, 'errors': int, 'validation_errors': List}

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV file is invalid or malformed
        ValidationError: If strict=True and a validation error occurs
    """
    from .core import ValidationError

    # Validate CSV file first
    is_valid, error_msg = validate_csv_file(filepath)
    if not is_valid:
        raise ValueError(f"Invalid CSV file: {error_msg}")

    stats = {'total': 0, 'processed': 0, 'skipped': 0, 'errors': 0, 'validation_errors': []}

    # Create temporary hash table for review mode
    if review:
        temp_hash_table = copy.deepcopy(hash_table)
        reviewed_transactions = []  # Track transactions for display
    else:
        temp_hash_table = hash_table

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

            # Load config and check for saved column mapping
            config = Config.load()
            bank_id = get_bank_identifier(header)

            saved_mapping = config.get_column_mapping(bank_id)
            if saved_mapping:
                print(f"✓ Using saved column mapping for this CSV format")
                date_col = saved_mapping.get('date', 0)
                address_col = saved_mapping.get('address', 0)
                amount_col = saved_mapping.get('amount', 0)
                name_col = saved_mapping.get('name', -1)
                type_col = saved_mapping.get('type', -1)
                description_col = saved_mapping.get('description', -1)
            else:
                # Get column mapping from user
                date_col, address_col, amount_col, name_col, type_col, description_col = cli.select_csv_columns(header)

                # Save mapping for future use
                mapping = {
                    'date': date_col,
                    'address': address_col,
                    'amount': amount_col,
                    'name': name_col,
                    'type': type_col,
                    'description': description_col
                }
                config.save_column_mapping(bank_id, mapping)
                print("✓ Column mapping saved for future use")

            # Validate column selections
            max_col = len(header) - 1
            if not (0 <= date_col <= max_col and 0 <= address_col <= max_col and 0 <= amount_col <= max_col):
                raise ValueError("Invalid column selection: columns out of range")

            # Count total rows first for progress indication
            rows = list(reader)
            total_rows = len(rows)

            print(f"\nProcessing {total_rows} transactions...")

            # Process each row
            row_num = 1  # Header is row 0
            for idx, row in enumerate(rows, 1):
                row_num += 1
                stats['total'] += 1

                # Show progress every 10 rows or on last row
                if idx % 10 == 0 or idx == total_rows:
                    cli.print_progress(idx, total_rows, "Processing")

                # Validate row length
                if len(row) < len(header):
                    error = ValidationError(
                        f"Row has fewer columns than header ({len(row)} < {len(header)})",
                        line_number=row_num,
                        error_type='missing_columns'
                    )
                    stats['validation_errors'].append(error)
                    print(f"Warning: {error}")
                    stats['skipped'] += 1
                    if strict:
                        raise error
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
                        error = ValidationError(
                            f"Invalid amount value: '{amount_str}'",
                            line_number=row_num,
                            error_type='invalid_amount',
                            field='amount',
                            value=amount_str
                        )
                        stats['validation_errors'].append(error)
                        print(f"Warning: {error}")
                        stats['skipped'] += 1
                        if strict:
                            raise error
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
                        # Determine error type from message
                        error_type = 'validation_error'
                        if 'amount' in error_msg.lower():
                            error_type = 'invalid_amount'
                        elif 'date' in error_msg.lower():
                            error_type = 'invalid_date'
                        elif 'address' in error_msg.lower():
                            error_type = 'invalid_address'
                        elif 'missing' in error_msg.lower():
                            error_type = 'missing_field'
                        elif 'suspicious' in error_msg.lower():
                            error_type = 'suspicious_content'

                        error = ValidationError(
                            error_msg,
                            line_number=row_num,
                            error_type=error_type
                        )
                        stats['validation_errors'].append(error)
                        print(f"Warning: {error}")
                        stats['skipped'] += 1
                        if strict:
                            raise error
                        continue

                    # Categorize transaction (into temp table if review mode)
                    categorize_transaction(transaction, temp_hash_table, cipher_suite, SALT)
                    stats['processed'] += 1

                    # Track for review display
                    if review:
                        # Find the category that was just assigned
                        from .category_manager import find_category_by_address
                        from .crypto import hash_address
                        hashed_address = hash_address(transaction['address'], SALT)
                        category = find_category_by_address(temp_hash_table['addresses'], hashed_address, cipher_suite)
                        reviewed_transactions.append({
                            'date': transaction['date'],
                            'amount': transaction['amount'],
                            'category': category,
                            'address': transaction['address']
                        })

                except IndexError as e:
                    error = ValidationError(
                        f"Column access error: {e}",
                        line_number=row_num,
                        error_type='column_access_error'
                    )
                    stats['validation_errors'].append(error)
                    print(f"Warning: {error}")
                    stats['skipped'] += 1
                    if strict:
                        raise error
                except Exception as e:
                    print(f"Error processing row {row_num}: {e}")
                    stats['errors'] += 1
                    if stats['errors'] > 10:
                        print("Too many errors, stopping CSV processing")
                        break

            # Print summary
            cli.print_summary(stats['total'], stats['processed'], stats['skipped'])

            # Print validation errors summary if any errors occurred
            if stats['validation_errors']:
                cli.print_validation_summary(stats['validation_errors'])

            # Review mode: Show review screen and get confirmation
            if review and stats['processed'] > 0:
                print("\n" + "="*80)
                print("Review mode: Please review transactions before saving")
                print("="*80)

                # Display review with category totals from temp hash table
                cli.display_review(reviewed_transactions, temp_hash_table['categories'])

                # Get user confirmation
                user_choice = cli.confirm_processing()

                if user_choice == 'confirm':
                    print("\n✓ Applying changes to database...")
                    # Merge temp data into real hash_table
                    hash_table['addresses'] = temp_hash_table['addresses']
                    hash_table['categories'] = temp_hash_table['categories']
                    hash_table['transaction_ids'] = temp_hash_table['transaction_ids']
                    print("✓ Changes applied successfully")
                elif user_choice == 'cancel':
                    print("\n✗ Processing cancelled by user")
                    print("No changes were saved to the database")
                    raise ValueError("User cancelled transaction review")
                # 'edit' will be handled in Session 2

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


